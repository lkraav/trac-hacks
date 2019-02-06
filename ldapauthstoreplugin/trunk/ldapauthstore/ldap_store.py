from trac.core import *
from trac.config import Option, IntOption, BoolOption
from trac.perm import IPermissionGroupProvider

from acct_mgr.api import IPasswordStore

from ldapplugin.api import *

import ldap, ldap.filter

GROUP_PREFIX = '@'


class LdapAuthStore(Component):
    """A trac authentication provider using LDAP.

    The LDAP database is configured with LdapPlugin.
    Registers itself with the AuthManager trac plugin.
    """
    implements(IPasswordStore, IPermissionGroupProvider)

    ldap_basedn = Option('ldap', 'basedn', None,
        'Base DN for account searches')
    ldap_scope = IntOption('ldap', 'scope', 1,
        'Subtree search scope: 0=Base, 1=OneLevel, 2=Subtree')
    ldap_user_attr = Option('ldap', 'uidattr', 'sAMAccountName',
        'Attribute of the user account/id in the directory')
    ldap_user_filter = Option('ldap', 'user_filter', '(objectClass=person)',
        'Filter for user searches')
    ldap_validusers = Option('ldap', 'allusers_group', None,
        'DN of group containing valid users. If None, any user is valid')
    ldap_member_attr = Option('ldap', 'groupmember', 'member',
        'Attribute of user in a group')
    ldap_member_is_dn = BoolOption('ldap', 'groupmemberisdn', True,
        'Attribute of user in a group is users DN')
    ldap_group_attr = Option('ldap', 'groupattr', 'cn',
        'Attribute of the group name in the directory')
    ldap_group_filter = Option('ldap', 'group_filter', '(objectClass=group)',
        'Filter for group searches')
    ldap_email_attr = Option('ldap', 'email', 'mail',
        'Attribute of the users email')
    ldap_name_attr = Option('ldap', 'name', 'displayName',
        'Attribute of the users name')

    def __init__(self, ldap=None):
        # looks for groups only if LDAP support is enabled
        self.enabled = self.config.getbool('ldap', 'enable')
        if not self.enabled:
            return
        self.util = LdapUtil(self.config)
        # LDAP connection
        self._ldap = ldap
        # LDAP connection config
        self._ldapcfg = {}
        for name, value in self.config.options('ldap'):
            if name in LDAP_DIRECTORY_PARAMS:
                self._ldapcfg[name] = value

        # user entry local cache
        self._cache = {}
        # max time to live for a cache entry
        self._cache_ttl = int(self.config.get('ldap', 'cache_ttl', str(15*60)))
        # max cache entries
        self._cache_size = min(25, int(self.config.get('ldap', 'cache_size', '100')))
        self.log.debug('LdapAuthStore: Initiated')

    # IPermissionGroupProvider methods

    def get_permission_groups(self, user):
        """Return a list of names of the groups that the user with the
        specified name is a member of.
        """
        groups = []
        user_dn = self._get_user_dn(user)

        if not user_dn:
            return []

        search_filter = "(&(%s=%s)%s)" % (self.ldap_member_attr.encode('ascii'), unicode(user_dn,'utf8'), self.ldap_group_filter)
        res_attr = ['cn']
        self._openldap()
        #basedn = self.group_basedn or self.dir_basedn
        self.log.debug('Search for: %s %s %s %s' % ( self.ldap_basedn, search_filter, res_attr, self.ldap_scope ))
        result = self._ldap._search(self.ldap_basedn, search_filter.encode('iso-8859-15','ignore'), res_attr, self.ldap_scope)
        if not result:
            self.log.debug('No group found where %s is %s' % (user, self.ldap_member_attr))
            return []
        for entry in result:
            groupdn = entry[0]
            group = GROUP_PREFIX + entry[1]['cn'][0]
            #group = group.replace(' ', '_').lower()
            if group not in groups:
                groups.append(group)

        if not groups:
            self.log.warn("Could not retrieve groups for user %s" % user)
            return []

        self.log.debug('user %s has groups %s', user, ', '.join(groups))
        return sorted(groups)

    def _get_user_dn(self, user):
        """Search and return DN of user
        """
        self.log.debug('_get_user_dn(%s)' %  user)

        # search DN of the user
        search_filter = "(&(%s=%s)%s)" % (self.ldap_user_attr.encode('ascii'), user, self.ldap_user_filter)
        res_attr = ['dn']
        self._openldap()
        self.log.debug('Search for: %s %s %s %s' % ( self.ldap_basedn, search_filter, res_attr, self.ldap_scope ))
        result = self._ldap._search(self.ldap_basedn, search_filter, res_attr, self.ldap_scope)
        if not result:
            self.log.debug('User %s not found' % user)
            return None
        dn = result[0][0]
        self.log.debug('User %s has dn %s' % (user, dn.decode('iso-8859-15')))
        return dn

    def _get_group_dn(self, group):
        """Search and return DN of group
        """
        self.log.debug('_get_group_dn(%s)' %  group)

        search_filter = "(&(%s=%s)%s)" % (self.ldap_group_attr.encode('ascii'), group, self.ldap_group_filter)
        res_attr = ['dn']
        self._openldap()
        self.log.debug('Search for: %s %s %s %s' % ( self.ldap_basedn, search_filter, res_attr, self.ldap_scope ))
        result = self._ldap._search(self.ldap_basedn, search_filter, res_attr, self.ldap_scope)
        if not result:
            self.log.debug('Group %s not found' % group)
            return None
        dn = result[0][0]
        self.log.debug('Group %s has dn %s' % (group, dn.decode('iso-8859-15')))
        return dn

    def get_users(self):
        """Returns an iterable of the known usernames.

        Does so by listing the members of the LDAP group ldap.allusers
        or the useres in the session table if group is not defined
        """
        # data from session table
        if not self.ldap_validusers:
            user_list = []
            userinfo = self.env.get_known_users()
            for user in userinfo:
                user_list.append(user[0])
            if user_list:
                self.log.debug("user_list: %s " % ",".join(user_list))
                return sorted(user_list)

        # data from ldap group
        self._openldap()
        gdn = self._get_group_dn(self.ldap_validusers)
        ldap_users = self._ldap.get_attribute(gdn, self.ldap_member_attr.encode('ascii'))
        self.log.debug('Found %d trac users in LDAP directory.' \
        % len(ldap_users))
        if not self.ldap_member_is_dn:
            return ldap_users
        user_list = []
        for dn in ldap_users:
            edn = ldap.filter.escape_filter_chars(dn)
            try:
                user_list.append(self._ldap.get_attribute(edn, self.ldap_user_attr.encode('ascii'))[0])
            except:
                self.log.debug('user aattr not found for : %s' % ( dn.decode('iso-8859-15') ))
                pass
        return sorted(user_list)

    def has_user(self, user):
        """Returns whether the user account exists.
        THIS SEEMS NOT TO BE CALLED!
        Does so by checking if the user is a member of
        the ldap.allusers LDAP group."""
        self.log.debug("has_user (%s)" % (user))

        dn = self._get_user_dn(user)
        if not dn:
            self.log.warn("dn of user %s not found" % user)
            return False
        gdn = self._get_group_dn(self.ldap_validusers)
        if not gdn:
            self.log.warn("dn of group %s not found" % self.ldap_validusers)
            return False
        self._openldap()
        #should be search for group with dn and user (in case member attr is memberuid)
        return self._ldap._compare(gdn, self.ldap_member_attr, dn.decode('iso-8859-15'))

    def check_password(self, user, password):
        """Checks if the password is valid for the user.
        Does so by attempting an LDAP bind as this user.
        """
        self.log.debug('check_password(%s, %s)' % ( user, 'XXXXXXXX'))

        # search DN of the user
        search_filter = "(&(%s=%s)%s)" % (self.ldap_user_attr.encode('ascii'), user, self.ldap_user_filter)
        res_attr = ['dn',
                                self.ldap_user_attr.encode('ascii'),
                                self.ldap_email_attr.encode('ascii'),
                                self.ldap_name_attr.encode('ascii')]
        self._openldap()
        self.log.debug('Search for: %s %s %s %s' % ( self.ldap_basedn, search_filter, res_attr, self.ldap_scope ))
        result = self._ldap._search(self.ldap_basedn, search_filter, res_attr, self.ldap_scope)
        if not result:
            self.log.debug('User %s not found' % user)
            return None
        dn = result[0][0]
        #
        #TODO last login does not show up when data from ldap and user is not case sensitive
        #when using non case sensitive ldap users (default in openldp, ad according to rfc)
        #user should be normalised, but we get it from accountmgr the way it is typed
        #
        # users restricted to ldap group
        if self.ldap_validusers:
            # store user like it is spelled in ldap else cached data want show up in userlist
            user_attr = result[0][1][self.ldap_user_attr][0]
            self.log.debug('User %s is spelled %s and dn is %s' % ( user, user_attr, dn.decode('iso-8859-15') ))
        else:
            # data from session table
            user_attr = user
            self.log.debug('User %s has dn %s' % ( user_attr, dn.decode('iso-8859-15') ))

        # try to bind as this user
        cnx = self._bind_as_user(dn, password)
        if cnx is None:
            return False
        cnx.close()

        # has_user seems not to be used, so limit by group here
        if self.ldap_validusers:
            # limit users by group
            self.log.debug('Check if user is in valid group')
            if not self.has_user(user):
                self.log.info('User %s not in group %s' % (user_attr, self.ldap_validusers))
                return None

        attrs = {'name': '', 'email': ''}
        try:
            attrs['name'] = result[0][1][self.ldap_name_attr][0]
        except:
            self.log.warn('Attribute %s not found in %s' % (self.ldap_name_attr, dn.decode('iso-8859-15')))
        try:
            attrs['email'] = result[0][1][self.ldap_email_attr][0]
        except:
            self.log.warn('Attribute %s not found in %s' % (self.ldap_email_attr, dn.decode('iso-8859-15')))

        # Store values from ldap in the session cache
        for attr in ('name', 'email'):
            if not attrs[attr]:
                continue
            value = unicode(attrs[attr], 'utf-8')
            self.log.debug('LDAPstore : Update %s for %s',
                           value , attr)
            with self.env.db_transaction as db:
                db("""
                    UPDATE session_attribute SET value=%s
                    WHERE name=%s AND sid=%s AND authenticated='1'
                    """, (value, attr, user_attr))
                for _ in db("""
                        SELECT * from session_attribute
                        WHERE name=%s AND sid=%s
                        """, (attr, user_attr))
                    break
                else:
                    self.log.debug('LDAPstore : Insert %s for %s',
                                   value , attr)
                    db("""
                        INSERT INTO session_attribute
                         (sid,authenticated,name,value)
                        VALUES (%s,1,%s,%s)
                        """, (user_attr, attr, value))
        return True

    def _bind_as_user(self, dn, password):
        """Returns an ldapplugin.LdapConnection for this user.

        Returns None if unsuccessful.
        You must close the connection by calling its close method.
        """

        #   Creating an LdapConnection is maybe expensive, but sharing
        # _ldap would not be safe.
        #   The integration with LdapPlugin could
        # be better: add an API to LdapPlugin that gives us a raw,
        # unbound connection to the server.
        settings = dict(self._ldapcfg)
        settings['bind_user'] = dn
        settings['bind_passwd'] = password
        try:
            lc = LdapConnection(self.env.log, True, **settings)
            lc._open()
            return lc
        except TracError:
            try:
                lc.close()
            except:
                pass
        return None

    def _openldap(self):
        """Ensure self._ldap is set to a privileged LDAP connection.
        """
        if self._ldap is None:
            bind = self.config.getbool('ldap', 'store_bind') or \
                    self.config.getbool('ldap', 'group_bind')
            self._ldap = LdapConnection(self.env.log, bind, **self._ldapcfg)
