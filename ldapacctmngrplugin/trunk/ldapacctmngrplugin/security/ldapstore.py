# -*- coding: utf-8 -*-

import ldap
from ldap.filter import filter_format

from trac.core import Component, implements
from trac.config import BoolOption, Option
from acct_mgr.api import IPasswordStore


class LDAPStore(Component):

    implements(IPasswordStore)

    bind_server = Option(
        'ldap', 'bind_server', 'ldap://localhost:389',
        doc='LDAP server for authentication. The format is '
            'ldap[s]://host[:port]", e.g., "ldap://localhost:389".')

    bind_anonymous = BoolOption(
        'ldap', 'bind_anonymous', 'enabled',
        doc='If server accepts anonymous bind (yes or no)')

    bind_dn = Option(
        'ldap', 'bind_dn', '',
        doc='For server not accepting anonymous bind, specify a bind_dn and '
            'password.')

    bind_passwd = Option(
        'ldap', 'bind_passwd', '',
        doc='For server not accepting anonymous bind, specify a bind_dn and '
            'password.')

    user_searchbase = Option(
        'ldap', 'user_searchbase', 'dc=company,dc=com',
        doc='Where to look for users. It is usually '
            '"dc=your_company_name,dc=com". Please consult the structure of '
            'your LDAP tree.')

    user_searchfilter = Option(
        'ldap', 'user_searchfilter', 'objectClass=inetOrgPerson',
        doc='Filter for listing valid users. The default '
            '("objectClass=inetOrgPerson") should work for most of the cases.')

    user_field = Option(
        'ldap', 'user_field', 'uid',
        doc="""The LDAP field to match the username and authenticate.""")

    # IPasswordStore methods

    def check_password(self, user, password):
        if not user or not password:
            return None

        # Authenticate a user by checking password
        con = self.init_connection()
        try:
            resp = self._search_users(con, user)

            # Added to prevent empty password authentication (some server allows that)
            if not resp:
                return None

            try:
                dn, attrs = resp[0]
                con.simple_bind_s(dn, password)
            except ldap.INVALID_CREDENTIALS:
                self.log.warning('Invalid credentials: user %s not authenticated', user)
                return False
            else:
                return True
        finally:
            con.unbind()

    def get_users(self):
        # Get list of users from LDAP server
        user_field = self.user_field
        con = self.init_connection()
        try:
            resp = self._search_users(con)
        finally:
            con.unbind()

        for dn, attrs in resp:
            if not dn:
                continue
            usernames = attrs.get(user_field)
            if usernames:
                username = usernames[0]
                if isinstance(username, bytes):
                    username = username.decode('utf-8')
                yield username

    def has_user(self, user):
        con = self.init_connection()
        try:
            resp = self._search_users(con, user)
            return len(resp) != 0
        finally:
            con.unbind()

    def init_connection(self):
        # Initialize LDAP connection
        connection = ldap.initialize(self.bind_server)
        connection.set_option(ldap.OPT_REFERRALS, 0)

        if self.bind_server.startswith('ldaps'):
            # Not verifying the certificate for TLS
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            #connection.start_tls_s()

        if not self.bind_anonymous:
            connection.simple_bind_s(self.bind_dn, self.bind_passwd)

        return connection

    def _search_users(self, con, user=None):
        filters = [self.user_searchfilter]
        if user:
            filters.append(filter_format('{0}=%s'.format(self.user_field),
                                         [user]))
        filter_ = '(&%s)' % ''.join('(%s)' % f for f in filters)
        return con.search_s(self.user_searchbase, ldap.SCOPE_SUBTREE, filter_,
                            ['dn', self.user_field])
