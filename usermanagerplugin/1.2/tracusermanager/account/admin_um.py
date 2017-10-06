# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

from random import Random

from trac.core import Component, TracError, implements
from trac.util.translation import _

from acct_mgr.api import AccountManager

from tracusermanager.admin import IUserManagerPanelProvider


class AccountUserManagerPanel(Component):
    implements(IUserManagerPanelProvider)

    def get_usermanager_admin_panels(self, req):
        return [('account', _('Authentication'))]

    def render_usermanager_admin_panel(self, req, panel, user, path_info):

        data = {
            'TYPES': ['trac-managed', 'server-managed'],
            'set_password_enabled':
                AccountManager(self.env).supports('set_password'),
            'delete_enabled':
                AccountManager(self.env).supports('delete_user')
        }
        messages = []
        errors = []

        if req.method == 'POST':
            if 'um_account_update_type' in req.args:
                if req.args.get('um_account_type') == 'trac-managed' and \
                        not AccountManager(self.env).has_user(user.username):
                    AccountManager(self.env).set_password(
                        user.username,
                        ''.join(Random().choice('pleaseChangeThisPassword')
                                for x in range(10)))
                    messages.append(_("Successfully changed %(user)s's "
                                      "authentication method",
                                      user=user.username))
                elif req.args.get('um_account_type') == 'server-managed':
                    AccountManager(self.env).delete_user(user.username)
                    messages.append(_("Successfully changed %(user)s's "
                                      "authentication method",
                                      user=user.username))
                else:
                    raise TracError("Unknow account type")
            elif 'um_account_change_password' in req.args:
                if req.args['um_account_confirm_password'] == \
                        req.args['um_account_new_password']:
                    AccountManager(self.env)\
                        .set_password(user.username,
                                      req.args['um_account_new_password'])
                    messages.append(
                        _("Successfully changed %(user)s's password",
                          user=user.username))
                else:
                    errors.append(_("Passwords don't match"))
            else:
                raise TracError("Unknow action")

        # Adding type
        data.update(type=AccountManager(self.env).has_user(user.username) and
                    'trac-managed' or 'server-managed')

        return 'admin_um_account.html', {'um_account': data,
                                         'messages': messages,
                                         'errors': errors}
