from trac.core import *
from ldapplugin.api import *
import ldap
from acct_mgr.api import IPasswordStore
#from trac.config import Option

class LdapAuthStore(Component):
    """A trac authentication provider using LDAP.

    The LDAP database is configured with LdapPlugin.
    Registers itself with the AuthManager trac plugin.
    """
    implements(IPasswordStore)

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
        # group of all users with permission to log in
        self._allusers = self.config.get('ldap',
                        'allusers_group', 'tracusers')

        # user entry local cache
        self._cache = {}
        # max time to live for a cache entry
        self._cache_ttl = int(self.config.get('ldap', 'cache_ttl', str(15*60)))
        # max cache entries
        self._cache_size = min(25, int(self.config.get('ldap', 'cache_size', '100')))

        self.env.log.debug('LdapAuthStore: Initiated')

    def get_users(self):
        """Returns an iterable of the known usernames.

        Does so by listing the members of the LDAP group ldap.allusers .
        """

        self._openldap()
        gdn = self.util.group_attrdn(self._allusers)
        ldap_users = self._ldap.get_attribute(gdn,
                        self.config.get('ldap', 'groupmember', 'member')
                        .encode('ascii'))
        self.env.log.debug('Found %d trac users in LDAP directory.' \
        % len(ldap_users))
        if not self.config.getbool('ldap', 'groupmemberisdn', True):
            return ldap_users
        return (self.util.extract_user_from_dn(dn) for dn in ldap_users)

    def has_user(self, user):
        """Returns whether the user account exists.

        Does so by checking if the user is a member of
        the ldap.allusers LDAP group."""

        dn = self.util.user_attrdn(user)
        gdn = self.util.group_attrdn(self._allusers)

        self._openldap()
        return self._ldap.is_in_group(dn, gdn)

    # def has_user(self, user):
    #     self.env.log.info("checking user: %s"%user)
    #     return user in self.get_users()
    #
    # def get_users(self):
    #     self._openldap()
    #     #2008-03-17 change objectclass=simpleSecurityObject to object=*
    #     #MODIFIKEI
    #     #ldap_users = self._ldap.get_dn(self._ldap.basedn, '(objectclass=*)')
    #     self._basedn_filter = self.config.get('ldap', 'basedn_filter', 'objectClass=*')
    #     ldap_users = self._ldap.get_dn(self._ldap.basedn, self._basedn_filter)
    #
    #     self.env.log.info("ldap_users: %s"%(ldap_users))
    #     users = []
    #     for user in ldap_users:
    #         m = re.match('uid=([^,]+)', user)
    #         if m:
    #             users.append(m.group(1))
    #     return users

# do we want to set ldap passwd via trac?
    # maybe only if enabled in ini
    def set_password(self, user, password, old_password = None):
        dn = self.util.user_attrdn(user)
        try:
            self._set_password_as_user(dn, password, old_password)
        except ldap.UNWILLING_TO_PERFORM:
            self._set_password_as_admin(user, password, old_password)
        #Means no creation - weird convention
        #This means we send exceptions for anything else
        return False

    def _set_password_as_user(self, dn, password, old_password):
        """Throws if it cannot."""
        cnx = self._bind_as_user(dn, old_password)
        try:
            cnx._ds.passwd_s(dn, old_password, password)
        except ldap.UNWILLING_TO_PERFORM:
            cnx.close()
            raise

    def _set_password_as_admin(self, dn, password, old_password):
        self._openldap()
        self._ldap._open()
        self._ldap._ds.passwd_s(dn, old_password, password)

    def check_password(self, user, password):
        """Checks if the password is valid for the user.

        Does so by attempting an LDAP bind as this user.
        Does not attempt to check this is a valid trac account,
        see has_user for that.
        """
        dn = self.util.user_attrdn(user)
        cnx = self._bind_as_user(dn, password)
        if cnx is None:
            return False
        # Store values from ldap in the session cache or update if values
        # in ldap changed
        for attr in ('name', 'email'):
            fieldname = str(self.config.get('ldap', attr ))
            self.env.log.debug('LDAPstore : Getting %s for %s' % ( fieldname , attr ))
            value = cnx.get_attribute(dn, fieldname)
            if not value:
                continue
            value = unicode(value[0], 'utf-8')
            self.env.log.debug('LDAPstore : Got value %s for attribute %s' % ( value , attr ))
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            self.env.log.debug('LDAPstore : Update %s for %s' % ( value , attr ))
            cursor.execute("UPDATE session_attribute SET value=%s "
                    "WHERE name=%s AND sid=%s AND authenticated=1",
                    (value, attr, user))
            db.commit()
            cursor.execute("SELECT * from session_attribute WHERE name=%s AND sid=%s", (attr,user))
            db.commit()
            if not cursor.rowcount:
                self.env.log.debug('LDAPstore : Insert %s for %s' % ( value , attr ))
                cursor.execute("INSERT INTO session_attribute "
                        "(sid,authenticated,name,value) "
                        "VALUES (%s,1,%s,%s)",
                        (user, attr, value))
                db.commit()
        cnx.close()
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

    # we don't delete/add to ldap
    # def delete_user(self, user):
    #     """Deletes the user account.
    #
    #     Returns True if the account existed and was deleted, False otherwise.
    #     """
    #     return False

    def _openldap(self):
        """Ensure self._ldap is set to a privileged LDAP connection.
        """
        if self._ldap is None:
            bind = self.config.getbool('ldap', 'store_bind') or \
                    self.config.getbool('ldap', 'group_bind')
            self._ldap = LdapConnection(self.env.log, bind, **self._ldapcfg)
