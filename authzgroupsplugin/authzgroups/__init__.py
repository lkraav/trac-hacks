# Copyright David Abrahams 2007. Distributed under the Boost
# Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
from trac.core import *
from trac.perm import IPermissionGroupProvider
from trac.versioncontrol.svn_authz import SubversionAuthorizer, \
                                          RealSubversionAuthorizer

class SvnAuthzGroupProvider(Component):
    implements(IPermissionGroupProvider)

    def get_permission_groups(self, username):
        authz = SubversionAuthorizer(self.env, None, username)
        if isinstance(authz, RealSubversionAuthorizer):
            return authz._groups()
        else:
            return []
