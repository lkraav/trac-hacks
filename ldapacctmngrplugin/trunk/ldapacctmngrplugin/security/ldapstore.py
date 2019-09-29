import ldap
import ldap.filter

from trac.core import *
from trac.config import *
from acct_mgr.api import IPasswordStore

class LDAPStore (Component):
    bind_server = Option('ldap', 'bind_server', 'ldap://localhost:389', doc='LDAP server for authentication. The format is "ldap[s]://host[:port]", e.g., "ldap://localhost:389".')
    bind_anonymous = Option('ldap', 'bind_anonymous', 'yes', doc='If server accepts anonymous bind (yes or no)')
    bind_dn = Option('ldap', 'bind_dn', '', doc='For server not accepting anonymous bind, specify a bind_dn and password.')
    bind_passwd = Option('ldap', 'bind_passwd', '', doc='For server not accepting anonymous bind, specify a bind_dn and password.')
    user_searchbase = Option('ldap', 'user_searchbase', 'dc=company,dc=com', doc='Where to look for users. It is usually "dc=your_company_name,dc=com". Please consult the structure of your LDAP tree.')
    user_searchfilter = Option('ldap', 'user_searchfilter', 'objectClass=inetOrgPerson', doc='Filter for listing valid users. The default ("objectClass=inetOrgPerson") should work for most of the cases.')
    user_matchfilter = Option('ldap', 'user_matchfilter', 'uid=%s', doc='The LDAP field for matching username when authenticating. The query is almost always "uid=%s".')

    implements(IPasswordStore)

    def check_password(self, user, password):
        # Authenticate a user by checking password
        con = None

        # nested "try:" for python2.4
        try:
            try:
                con = self.init_connection()
                resp = self._ldap_search_user(con, user, ['dn'])

                # Added to prevent empty password authentication (some server allows that)
                if not len(resp) :
                    return None

                resp = con.simple_bind_s(resp[0][0], password)
                return True
            except ldap.INVALID_CREDENTIALS:
                self.log.debug('Invalid credentials: user %s not authenticated', user)
                return False
        finally:
            if con != None:
                con.unbind()

    def get_users(self):
        # Get list of users from LDAP server
        con = None
        base = self.user_searchbase
        filter = self.user_searchfilter
        resp = None

        try:
            con = self.init_connection()
            resp = con.search_s(base, ldap.SCOPE_SUBTREE, filter, ['dn','uid'])
        finally:
            if con != None:
                con.unbind()

        self.log.debug('List users: get %d users' % (len(resp)))
        for entry in resp:
            if entry[1]['uid'][0]:
                yield entry[1]['uid'][0]

    def has_user(self, user):
        con = self.init_connection()
        try:
            resp = self._ldap_search_user(con, user, ['dn'])
            return len(resp) != 0
        finally:
            con.unbind()

    def init_connection(self):
        # Initialize LDAP connection
        connection = ldap.initialize(self.bind_server)

        if self.bind_server.startswith('ldaps'):
            # Not verifying the certificate for TLS
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            #connection.start_tls_s()

        if self.bind_anonymous.lower() != 'yes':
            resp = connection.simple_bind_s(self.bind_dn, self.bind_passwd)

        return connection

    def _ldap_search_user(self, con, user, attrs):
        filter_ = ldap.filter.filter_format(self.user_matchfilter, [user])
        return con.search_s(self.user_searchbase, ldap.SCOPE_SUBTREE, filter_,
                            attrs)
