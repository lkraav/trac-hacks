# -*- coding: utf-8 -*-

from pwd import *
from grp import *
from trac.core import *
from trac.perm import IPermissionGroupProvider
from trac.perm import PermissionSystem


class UnixGroups(Component):
    implements(IPermissionGroupProvider)

    def __init__(self):
        self.ENV = self.env
        self.DEBUG = 0

    # IPermissionGroupProvider methods

    def get_permission_groups(self, username):
        try:
            maingroup = getgrgid(getpwnam(username).pw_gid).gr_name
        except KeyError:
            return []

        permsys = PermissionSystem(self.ENV)
        perm_list = permsys.get_all_permissions()

        if self.DEBUG:
            fp = open('/var/tmp/unixgroups', 'a+')

        groups = list()
        if not perm_list:
            return [maingroup]
        else:
            for perm in perm_list:
                if not perm[0] in groups:
                    groups.append(perm[0])
                    if self.DEBUG:
                        fp.write('appending group: %s\n' % (perm[0]))

        secgroups = list()
        for grp in groups:
            if self.DEBUG:
                fp.write('check group: %s\n' % (grp))
            try:
                members = getgrnam(grp)[3]
            except KeyError, detail:
                continue

            if username in members:
                secgroups.append(grp)
                if self.DEBUG:
                    fp.write('%s in group: %s\n' % (username, grp))

        if self.DEBUG:
            fp.close()

        return [maingroup] + secgroups
