# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

from trac.core import Component, implements
from trac.perm import PermissionSystem
from trac.util.translation import _
from trac.web.chrome import add_stylesheet, add_script

from tracusermanager.admin import IUserManagerPanelProvider


class PermissionUserManagerPanel(Component):
    implements(IUserManagerPanelProvider)

    def get_usermanager_admin_panels(self, req):
        return [('permissions', _("Permissions"))]

    def render_usermanager_admin_panel(self, req, panel, user, path_info):
        user_actions = self._get_user_permissions(user)
        all_user_actions = \
            PermissionSystem(self.env).get_user_permissions(user.username)
        actions = PermissionSystem(self.env).get_actions() + \
                  list(set(group for group, permissions in
                           PermissionSystem(self.env).get_all_permissions()))
        data = dict(actions=actions, all_user_actions=all_user_actions,
                    user_actions=user_actions,
                    permsys=PermissionSystem(self.env), messages=[],
                    errors=[])

        if req.method == 'POST':
            for action in actions:
                if action in req.args.getlist('um_permission'):
                    if action not in all_user_actions:
                        try:
                            PermissionSystem(self.env).grant_permission(
                                user.username, action)
                        except Exception, e:
                            data['errors'].append(e)
                        else:
                            data['messages'].append(
                                _("Granted permission %(action)s for user "
                                  "%(user).", action=action,
                                  user=user.username))
                else:
                    if action in user_actions:
                        try:
                            PermissionSystem(self.env).revoke_permission(
                                user.username, action)
                        except Exception, e:
                            data['errors'].append(e)
                        else:
                            data['messages'].append(
                                _("Revoked permission %(action)s for user "
                                  "%(user).", action=action,
                                  user=user.username))
            if not data['errors']:
                data['messages'].append(
                    _("Successfully updated user permissions for user "
                      "%(user)s", user=user.username))

            # Updating data
            data['user_actions'] = self._get_user_permissions(user)
            data['all_user_actions'] = \
                PermissionSystem(self.env).get_user_permissions(user.username)

        add_stylesheet(req, 'tracusermanager/css/admin_um_permissions.css')
        add_script(req, 'tracusermanager/js/admin_um_permissions.js')

        return 'admin_um_permissions.html', data

    def _get_user_permissions(self, user):
        return dict((action, True)
                    for username, action
                    in PermissionSystem(self.env).get_all_permissions()
                    if username == user.username)
