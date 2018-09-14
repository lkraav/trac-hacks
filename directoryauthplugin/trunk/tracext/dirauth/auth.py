# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
# Extended: Branson Matheson <branson.matheson@nasa.gov>

import cPickle
import hashlib
import ldap
import time
import sys

from ldap.controls import SimplePagedResultsControl

from acct_mgr.api import IPasswordStore
from trac.config import IntOption, Option, BoolOption
from trac.core import Component, TracError, implements
from trac.perm import IPermissionGroupProvider
from trac.util.text import to_unicode
from trac.util.translation import _


GROUP_PREFIX = '@'
NOCACHE = 0

__all__ = ['DirAuthStore']


def to_utf8(text):
    # Account for poor behavior of to_utf8 in Trac < 1.0.2
    if isinstance(text, unicode):
        return text.encode('utf-8')
    else:
        from trac.util.text import to_utf8
        return to_utf8(text)


class DirAuthStore(Component):
    """Directory Password Store for Account Manager """
    implements(IPasswordStore, IPermissionGroupProvider)

    dir_uri = Option('account-manager', 'dir_uri', 'ldap://localhost',
                     "URI of the LDAP or Active Directory Server")

    dir_charset = Option('account-manager', 'dir_charset', 'utf-8',
                         "Text encoding used by the LDAP or Active "
                         "Directory Server")

    dir_scope = IntOption('account-manager', 'dir_scope', 2,
                          "0=Base, 1=OneLevel, 2=Subtree")

    dir_binddn = Option('account-manager', 'dir_binddn', '',
                        "DN used to bind to AD, leave blank for "
                        "anonymous bind")

    dir_bindpw = Option('account-manager', 'dir_bindpw', '',
                        "Password used when binding to AD, leave blank for "
                        "anonymous bind")

    dir_timeout = IntOption('account-manager', 'dir_timeout', 5,
                            "ldap response timeout in seconds")

    dir_basedn = Option('account-manager', 'dir_basedn', None,
                        "Base DN used for account searches")
    
    dir_pagesize = IntOption('account-manager', 'dir_pagesize', 1000,
                             "Page size for ldap queries.")

    user_attr = Option('account-manager', 'user_attr', 'sAMAccountName',
                       "Attribute of the user in the directory")

    name_attr = Option('account-manager', 'name_attr', 'displayName',
                       "Attribute of the users name in the directory")

    email_attr = Option('account-manager', 'email_attr', 'mail',
                        "Attribute of the users email in the directory")

    proxy_attr = Option('account-manager', 'proxy_attr', 'proxyAddress',
                        "Attribute of the users proxyAddress in the directory")

    member_attr = Option('account-manager', 'member_attr', 'member',
                         "Attribute to determine members of a group")

    group_class_attr = Option('account-manager', 'group_class_attr', 'group',
                              "Attribute of the group class")

    group_basedn = Option('account-manager', 'group_basedn', None,
                          "Base DN used for group searches")

    group_validusers = Option('account-manager', 'group_validusers', None,
                              "CN of group containing valid users. If None, "
                              "any AD user is valid")

    group_knownusers = BoolOption('account-manager', 'group_knownusers', False,
                             "Boolean: Display only the already known users.")

    group_expand = IntOption('account-manager', 'group_expand', 1,
                             "binary: expand ldap_groups into trac groups.")
    
    group_nested = BoolOption('account-manager', 'group_nested', False,
                             "Boolean: also add all parent groups of each group containing the user.")
    
    group_spaces2underscore = BoolOption('account-manager', 'group_spaces2underscore', True,
                             "Boolean:Replace spaces in group names with underscores.")
    
    group_nameattr = Option('account-manager', 'group_nameattr', 'cn',
                             "Specify the attribute to read the group name. Defaults to 'cn'. For full group names use 'dn'.")

    cache_ttl = IntOption('account-manager', 'cache_timeout', 60,
                          "cache timeout in seconds")

    cache_memsize = IntOption('account-manager', 'cache_memsize', 400,
                              "size of memcache in entries, zero to disable")

    cache_memprune = IntOption('account-manager', 'cache_memprune', 5,
                               "percent of entries to prune")

    cache_memsize_warn = IntOption('account-manager', 'cache_memsize_warn',
                                   300,
                                   "warning message for cache pruning in "
                                   "seconds")

    def __init__(self, ldap=None):
        self._ldap = ldap
        self._cache = {}
        reload(sys)
        sys.setdefaultencoding('utf8')

    # IPasswordStore methods

    def config_key(self):
        """Deprecated"""
        raise NotImplementedError

    def get_users(self):
        """Grab a list of users from the session store."""
        all_users = self._cache_get('allusers')
        if all_users:
            return all_users

        # Cache miss
        ldapCtx = self._bind_dir()
        self.log.debug('get users')
        if ldapCtx:
            if self.group_knownusers:
                userinfo = self.env.get_known_users()
            elif self.group_validusers:
                userinfo = self.expand_group_users(ldapCtx, self.group_validusers)
            else:
                users = self._ldap_search(ldapCtx, self.dir_basedn, ldap.SCOPE_SUBTREE,
                                      "objectClass=person",
                                      [to_utf8(self.user_attr),
                                       to_utf8(self.email_attr),
                                       to_utf8(self.proxy_attr),
                                       to_utf8(self.name_attr)])
                userinfo = [self._get_userinfo(u[1]) for u in users]
        else:
            raise TracError('Unable to bind to Active Directory')
        self.log.debug('get users: %s', str(userinfo))
        
        all_users = [u[0] for u in userinfo]
        self._cache_set('allusers', all_users)
        return all_users

    def expand_group_users(self, ldapCtx, group):
        """Given a group name, enumerate all members"""
                
        if self.group_expand == 0:
            return []
        
        if group.startswith('@'):
            group = group[1:]
        group = "cn=%s,%s" % (group, self.group_basedn) if self.group_nameattr == 'cn' else group
        self.log.debug("expand_group_users: search groups %s", group)
        g = self._ldap_search(ldapCtx, to_utf8(group),
                         ldap.SCOPE_SUBTREE if self.group_nested else ldap.SCOPE_BASE,
                         attrlist=[to_utf8(self.member_attr)])
        if g and self.member_attr in g[0][1]:
            users = []
            for m in g[0][1][str(self.member_attr)]:
                self.log.debug("expand_group_users: group expand: %s", m)
                try:
                    e = self._ldap_search(ldapCtx, to_utf8(m), ldap.SCOPE_BASE)
                    if e:
                        if 'person' in e[0][1]['objectClass']:
                            u = self._get_userinfo(e[0][1])
                            self.log.debug("found user %s", u[0])
                            users.append(u)
                        elif str(self.group_class_attr) in e[0][1]['objectClass']:
                            users.extend(self.expand_group_users(ldapCtx, e[0][0]))
                        else:
                            self.log.debug('The group member (%s) is neither a group nor a person', e[0][0])
                    else:
                        self.log.debug('Unable to find user listed in group: %s', str(m))
                        self.log.debug('This is very strange and you should probably check '
                                       'the consistency of your LDAP directory.', str(m))
                except Exception, e:
                    self.log.debug('expand_group_users: %s: Unable to find ldap user listed in group: %s', e, str(m))
            return users
        else:
            self.log.debug('expand_group_users: Unable to find any members of the group %s', group)
            return []

    def has_user(self, user):
        users = self.get_users()
        if user in users:
            return True
        else:
            return False

    def check_password(self, user, password):
        """Checks the password against LDAP."""
        success = None
        msg = "User Login: %s" % user

        if not user or not password:
            msg += " username or password can't be empty!"
            self.log.error('check_password: %s', msg)
            return success

        user_dn = self._get_user_dn(user, NOCACHE)
        if user_dn:
            success = self._bind_dir(user_dn, password.encode(self.dir_charset)) or False
            if success:
                msg += " Password Verified"
                success = True
            elif success is False:
                msg += " Password Failed"
            self.log.error('check_password: %s', msg)
        else:
            msg += " does not exist, deferring authentication"
            self.log.error('check_password: %s', msg)
            return success

        # Check the user is part of the right group, we don't use the cache
        # Here as this is part of 'authentication' vs 'authorization'
        if self.group_validusers:
            usergroups = self._expand_user_groups(user, NOCACHE)
            if self.group_validusers not in usergroups:
                msg += " but user is not in %s : %s" % (self.group_validusers, usergroups)
                self.log.error('check_password: %s', msg)
                return False

        # Update the session data at each login,
        # Note the use of NoCache to force the update(s)
        attrs = [self.user_attr, self.email_attr, self.proxy_attr, self.name_attr]
        lfilter = '(&(%s=%s)(objectClass=person))' % (self.user_attr, user)
        users = self._dir_search(self.dir_basedn, self.dir_scope,
                                 lfilter, attrs, NOCACHE)

        if not users:
            raise TracError(_("Authenticated, but didn't find the user with "
                              "filter: %(filter)s (%(users)s)",
                              filter=filter, users=users))

        # Update the session table to make this a valid user.
        user_info = self._get_userinfo(users[0][1])
        self._populate_user_session(user_info)

        # Update the users by doing a search w/o cache
        self.get_users()

        return success

    def delete_user(self, user):
        """Can't delete from LDAP."""
        raise NotImplementedError(_("Deleting users is not supported."))

    def get_user_groups(self, user):
        """Returns all groups for a user."""
        return self._expand_user_groups(user)

    def get_permission_groups(self, username):
        """Return a list of names of the groups that the user with the
        specified name is a member of."""
        return self._expand_user_groups(username)

    # Internal methods

    def _bind_dir(self, user_dn=None, passwd=None):

        if not self.dir_uri:
            raise TracError(_("The dir_uri ini option must be set."))

        if not self.dir_uri.lower().startswith('ldap'):
            raise TracError(_("The dir_uri URI must start with ldap: %s", self.dir_uri))

        if user_dn and passwd:
            user_ldap = ldap.ldapobject.ReconnectLDAPObject(self.dir_uri,
                                                            retry_max=5, retry_delay=1)

            self.log.debug("_bind_dir: attempting specific bind to %s as %s",
                           self.dir_uri, unicode(user_dn, 'utf8'))
            try:
                user_ldap.simple_bind_s(user_dn, passwd)
            except Exception, e:
                self.log.error("_bind_dir: binding failed. %s", e)
                return None
            return 1

        # Return cached handle for default use.
        if self._ldap:
            return self._ldap

        self._ldap = ldap.ldapobject.ReconnectLDAPObject(self.dir_uri, 
                                                         retry_max=5,
                                                         retry_delay=1)

        if self.dir_binddn:
            self.log.debug("_bind_dir: attempting general bind to %s as %s",
                           self.dir_uri, self.dir_binddn)
        else:
            self.log.debug("_bind_dir: attempting general bind to %s "
                           "anonymously", self.dir_uri)

        try:
            self._ldap.simple_bind_s(self.dir_binddn, self.dir_bindpw)
        except ldap.LDAPError, e:
            raise TracError("cannot bind to %s: %s" % (self.dir_uri, e))

        self.log.debug("_bind_dir: Bound to %s correctly.", self.dir_uri)

        # Allow restarting.
        self._ldap.set_option(ldap.OPT_RESTART, 1)
        self._ldap.set_option(ldap.OPT_TIMEOUT, self.dir_timeout)

        return self._ldap

    # ## searches
    def _get_user_dn(self, user, cache=1):
        """Get users dn."""

        dn = self._cache_get('dn: %s' % user)
        if dn:
            return dn

        u = self._dir_search(self.dir_basedn, self.dir_scope,
                             "(&(%s=%s)(objectClass=person))"
                             % (self.user_attr, user),
                             [self.user_attr], cache)

        if not u:
            self.log.debug("_get_user_dn: user not found: %s", user)
            dn = None
        else:
            dn = u[0][0]
            self._cache_set('dn: %s' % user, dn)
            self.log.debug("_get_user_dn: user %s has dn: %s", user, dn)
        return dn

    def _expand_user_groups(self, user, use_cache=1):
        """Get a list of all groups this user belongs to. This recurses up
        to make sure we get them all.
        """

        if use_cache:
            groups = self._cache_get('usergroups:%s' % user)
            if groups:
                return groups

        groups = []
        user_dn = self._get_user_dn(user)

        if not user_dn:
            self.log.debug("_expand_user_groups: username=%s has no dn.", user)
            return []

        if self.group_expand or self.group_validusers:
            basedn = self.group_basedn or self.dir_basedn if self.group_expand else self.group_validusers[1:]
            group_filter = ('(&(objectClass=%s)(%s=%s))') % (self.group_class_attr, self.member_attr, user_dn)
            user_groups = self._dir_search(basedn, self.dir_scope,
                                           group_filter, [self.group_nameattr])
            
            for entry in user_groups:
                groupdn = entry[0]
                group = entry[1][self.group_nameattr][0]
                if self.group_spaces2underscore:
                    group = group.replace(' ', '_')
                group = '%s%s' % (GROUP_PREFIX, group)
                if self.dir_charset == 'utf-8':
                    group = group.decode('utf-8')
                group = group.lower()
                self.log.debug('_expand_user_groups: %s repr=%s', group, repr(group))
                groups.append(group)  # dn
                if group not in groups:
                    groups.append(self._get_parent_groups(groups, groupdn))
            self.log.debug("_expand_user_groups: received groups: %s", groups)
                
        if self.group_expand == 0:
            gg = []
            if use_cache == 0:
                for g in groups:
                    self.log.debug("_expand_user_groups: %s == %s", g, self.group_validusers)
                    if g == self.group_validusers:
                        gg.append(g)
            groups = gg
        elif self.group_nested and self.group_nameattr == 'dn':
            gg = []
            for g in groups:
                g = g[1:]
                while True:
                    if g == self.group_basedn:
                        break
                    if g in gg:
                        break
                    gg.append(GROUP_PREFIX + g)
                    g = g[(g.index(',') + 1):]
            groups = gg

        if use_cache:
            self._cache_set('usergroups:%s' % user, groups)
        if groups:
            self.log.debug('_expand_user_groups: username=%s has groups %s', user, ', '.join(groups))
            return sorted(groups)
        else:
            self.log.debug('_expand_user_groups: username=%s has no groups.', user)
            return []


    def _get_parent_groups(self, groups, group_dn):
        group_filter = '(&(objectClass=%s)(%s=%s)' % (self.group_class_attr, self.member_attr, group_dn)
        basedn = self.group_basedn or self.dir_basedn
        ldap_groups = self._dir_search(basedn, self.dir_scope,
                                       group_filter, [self.group_nameattr])
        if ldap_groups:
            for entry in ldap_groups:
                groupdn = entry[0]
                group = entry[1][self.group_nameattr][0]
                if self.group_spaces2underscore:
                    group = group.replace(' ', '_')
                group = group.lower()
                if group not in groups:
                    groups.append(group)
                    groups.append(self._get_parent_groups(groups, groupdn))
        return groups

    def _get_userinfo(self, attrs):
        """Extract the userinfo tuple from the LDAP search result."""
        user_name = attrs[self.user_attr][0].lower()
        display_name = attrs.get(self.name_attr, [''])[0]
        email = ''
        if self.email_attr in attrs:
            email = attrs[self.email_attr][0].lower()
            self.log.debug("user %s has email %s", user_name, email)
        elif 'proxyAddresses' in attrs:
            for e in attrs['proxyAddresses']:
                if e.startswith('SMTP:'):
                    email = e[5:]
                continue
        return user_name, display_name, email

    def _populate_user_session(self, userinfo):
        """Create user session entries and populate email and last visit."""

        # Kind of ugly.  First try to insert a new session record.  If it
        # fails, don't worry, means it's already there.  Second, insert the
        # email address session attribute.  If it fails, don't worry, it's
        # already there.
        uname, displayname, email = userinfo

        with self._get_db() as db:

            cur = db.cursor()
            try:
                cur.execute("""
                    DELETE FROM session
                      WHERE sid=%s AND authenticated=1
                    """, (uname,))
                cur.execute("""
                    INSERT INTO session
                      (sid, authenticated, last_visit)
                    VALUES (%s, 1, %s)""", (uname, 0))
            except:
                self.log.debug("_populate_user_session: Session for %s exists.", uname)
    
            # Assume enabled if we get this far self.env.get_known_users()
            # needs this..
            # TODO need to have it updated by the get_dn stuff long term so the
            # db matches the auth source.
            cur = db.cursor()
            try:
                cur.execute("""
                    DELETE FROM session_attribute
                      WHERE sid=%s AND authenticated=1 AND name='enabled'
                    """, (uname,))
                cur.execute("""
                    INSERT INTO session_attribute
                      (sid, authenticated, name, value)
                    VALUES (%s, 1, 'enabled', '1')
                    """, (uname,))
            except:
                self.log.debug("_populate_user_session: Session for %s exists.", uname)
    
            if email:
                cur = db.cursor()
                cur.execute("""
                    DELETE FROM session_attribute
                      WHERE sid=%s AND authenticated=1 AND name='email'
                    """, (uname,))
                cur.execute("""
                    INSERT INTO session_attribute
                      (sid, authenticated, name, value)
                    VALUES (%s, 1, 'email', %s)
                    """, (uname, to_unicode(email)))
                self.log.debug("_populate_user_session: updating user session email info for %s (%s)",
                              uname, to_unicode(email))
    
            if displayname:
                cur = db.cursor()
                cur.execute("""
                    DELETE FROM session_attribute
                      WHERE sid=%s AND authenticated=1 AND name='name'
                    """, (uname,))
                cur.execute("""
                    INSERT INTO session_attribute
                      (sid, authenticated, name, value)
                    VALUES (%s, 1, 'name', %s)
                    """, (uname, to_unicode(displayname)))
                self.log.debug("_populate_user_session: updating user session displayname info for %s (%s)",
                              uname, to_unicode(displayname))
                
            return self._close_db(db)

    def _cache_get(self, key=None, ttl=None):
        """Get an item from memory cache"""
        cache_ttl = ttl or self.cache_ttl
        if not self.cache_memsize:
            return None

        now = time.time()

        if key in self._cache:
            lut, data = self._cache[key]
            if lut + cache_ttl >= now:
                self.log.debug("_cache_get: memcache hit for %s", key)
                return data
            else:
                del self._cache[key]
        return None

    def _cache_set(self, key=None, data=None, cache_time=None):
        if not self.cache_memsize:
            return None
        now = time.time()
        if not cache_time:
            cache_time = now

        # Prune if we need to.
        if len(self._cache) > self.cache_memsize:
            # Warn if too frequent.
            if 'last_prune' in self._cache:
                last_prune, data = self._cache['last_prune']
                if last_prune + self.cache_memsize_warn > now:
                    self.log.info("pruning memcache in less than %d seconds, "
                                  "you might increase cache_memsize.",
                                  self.cache_memsize_warn)

            self.log.debug("_cache_set: pruning memcache by %d: (current: %d > max: %d )",
                           self.cache_memprune, len(self._cache),
                           self.cache_memsize)
            cache_keys = self._cache.keys()
            cache_keys.sort(lambda x, y: cmp(self._cache[x][0],
                                             self._cache[y][0]))
            # Discards the 10% oldest.
            upper = self.cache_memprune * self.cache_memsize / 100
            old_keys = cache_keys[:upper]
            for k in old_keys:
                del self._cache[k]
                self._cache['last_prune'] = [now, []]

        self._cache[key] = [cache_time, data]
        return data

    def _dir_search(self, basedn, scope, lfilter, attrs=None, check_cache=1):
        current_time = time.time()

        attrs = self._decode_list(attrs or [])

        if not basedn:
            raise TracError(_("basedn not defined!"))
        if not lfilter:
            raise TracError(_("filter not defined!"))

        basedn = basedn
        lfilter = lfilter
        
        # Create unique key from the filter and the attributes.
        keystr = to_utf8(','.join([basedn, str(scope), lfilter, ':'.join(attrs)]))
        key = hashlib.md5(keystr).hexdigest()
        self.log.debug("_dir_search: searching %s for %s(%s)",
                       basedn, lfilter, key)

        with self._get_db() as db:
            # Check mem cache.
            if check_cache:
                ret = self._cache_get(key)
                if ret:
                    return ret
    
                # --  Check database
                cur = db.cursor()
                cur.execute("""
                    SELECT lut,data FROM dir_cache WHERE id=%s
                    """, (key,))
                row = cur.fetchone()
                if row:
                    lut, data = row
    
                    if current_time < lut + self.cache_ttl:
                        self.log.debug("_dir_search: dbcache hit for %s", lfilter)
                        ret = cPickle.loads(str(data))
                        self._cache_set(key, ret, lut)
                        return ret
                else:
                    # Old data, delete it and anything else that's old.
                    lut = current_time - self.cache_ttl
                    cur.execute("""
                        DELETE FROM dir_cache WHERE lut < %s
                        """, (lut,))
#                    db.commit()
            else:
                self.log.debug("_dir_search: skipping cache.")
    
            ldapCtx = self._bind_dir()
            self.log.debug("_dir_search: starting LDAP search of %s %s using %s "
                           "for %s", self.dir_uri, basedn, lfilter, attrs)
    
            res = []
            try:
                try:
                    res = self._ldap_search(ldapCtx, basedn.encode(self.dir_charset), scope,
                                 lfilter, attrs)
                except ldap.LDAPError, e:
                    # second try - does not work properly without
                    self.log.info("got %s - doing one additional retry", e)
                    self._ldap = None
                    ldapCtx = self._bind_dir()
                    res = self._ldap_search(ldapCtx, basedn.encode(self.dir_charset), scope,
                                 lfilter, attrs)
            except ldap.LDAPError, e:
                self.log.error("_dir_search: Error searching %s using %s: %s",
                               basedn, lfilter, e)
    
            if res:
                self.log.debug("_dir_search: dir hit, %d entries.", len(res))
            else:
                self.log.debug("_dir_search: dir miss.")
    
            if not check_cache:
                return res
    
            # Set the db cache for the next search, even if results are empty.
            res_str = cPickle.dumps(res, 0)
            try:
                cur = db.cursor()
                cur.execute("""
                    DELETE FROM dir_cache WHERE id=%s
                    """, (key,))
                self.log.debug("_dir_search: INSERT VALUES (%s, %s, %s)"
                               % (key, current_time, buffer(res_str)))
                cur.execute("""
                    INSERT INTO dir_cache (id, lut, data)
                    VALUES (%s, %s, %s)
                    """, (key, current_time, buffer(res_str)))
#                db.commit()
            except Exception, e:
                db.rollback()
                self.log.warn("_dir_search: db cache update failed. %s" % e)
                
            self._close_db(db)
    
            self._cache_set(key, res)

        self.log.debug("_dir_search: res=%s" % res)
        return res

    # helper method for UserExtensiblePermissionStore
    def get_all_groups(self):
        """Get all groups. Returns an array containing arrays [dn, cn]
        """

        if self.group_expand == 0:
            return []

        basedn = self.group_basedn or self.dir_basedn
        group_filter = ('(objectClass=%s)') % self.group_class_attr
        all_groups = self._dir_search(basedn, self.dir_scope, group_filter, [self.group_nameattr])
        
        if self.group_spaces2underscore:
            self.log.debug("get_all_groups: all=%s" % all_groups)
            for index, item in enumerate(all_groups):
                all_groups[index] = (item[0].replace(' ', '_'), item[1])

        all_groups

        self.log.debug("get_all_groups: all=%s" % all_groups)
        return all_groups

    def get_group_users(self, groupdn):
        """Grab a list of users from the session store."""

        lcnx = self._bind_dir()
        self.log.debug('get users:')
        if lcnx:
                userinfo = self.expand_group_users(lcnx, groupdn)
        else:
            raise TracError('Unable to bind to Active Directory')
        self.log.debug('get users: %s', str(userinfo))
        return [u[0] for u in userinfo]

    @staticmethod
    def _decode_list(l=None):
        newlist = []
        if not l:
            return l
        for val in l:
            #newlist.append(to_utf8(val))
            newlist.append(val.encode('ascii', 'ignore'))
        return newlist

    def _get_db(self):
        """ Obtain a writeable db connection """
        if "get_db_cnx" in self.env:
            return self.env.get_db_cnx()
        else:
            dbx = self.env.db_transaction
            return dbx

    def _close_db(self, db):
        """ close the database connection. """
        if "get_db_cnx" in self.env:
            db.commit()
            return db.close()
        
        return True


    def _ldap_search(self, context, base, scope, filterstr = '(objectClass=*)', attrlist = None):
        """Perform a LDAP search."""
        
        sz = int(self.dir_pagesize)
        if sz > 0:
            self.log.debug("_ldap_search: ldap query with page size %s", sz)
        
        lc = SimplePagedResultsControl(True, sz, '') if sz > 0 else None

        r = []

        while True:
            msgid = context.search_ext(base, scope, filterstr, attrlist, 0, [lc], None, -1, sz);
            
            resp_type, resp_data, resp_msgid, decoded_resp_ctrls = context.result3(msgid)
    
            r += resp_data
            
            self.log.debug("_ldap_search: serverControls: %s", decoded_resp_ctrls)
            
            pctrls = [
                c
                for c in decoded_resp_ctrls
                if c.controlType == ldap.CONTROL_PAGEDRESULTS
            ]
            if pctrls:
                cookie = pctrls[0].cookie
                if cookie:
                    self.log.debug("_ldap_search: cookie: %s", cookie)
                    lc = SimplePagedResultsControl(True, sz, cookie)
                else:
                    break
            else:
                break

        self.log.debug("_ldap_search: result = %s", r)
        return r;
    
