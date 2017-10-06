# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

from trac.core import Component, ExtensionPoint, Interface, TracError, \
                      implements
from trac.config import Option
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import add_notice, add_script, add_stylesheet, \
                            add_warning
from trac.util.html import html
from trac.util.datefmt import format_datetime
from trac.util.translation import _

from tracusermanager.api import UserManager, User

__all__ = ['IUserManagerPanelProvider']


class IUserManagerPanelProvider(Interface):

    def get_usermanager_admin_panels():
        """Returns a list with provided admin panels.
        Format: [('panel_name', 'panel_label', order)]

        @return: list
        """

    def render_usermanager_admin_panel(req, panel, user, path_info):
        """Render's user admin panel.
        This method should return a tuplet of a form:
            (template, data)
        If data has key 'errors' or 'messages',
        those items will be added to user_manager['errors'], ['messages'].
        """


class IUserListCellContributor(Interface):

    def get_userlist_cells(self):
        """Should return a list of provided cells in form of
        [ ('cell_name', _('Cell Label')) ]
        """

    def render_userlist_cell(self, cell_name, user):
        """Should render user cell"""


class UserManagementAdminPage(Component):
    implements(IAdminPanelProvider)

    panel_providers = ExtensionPoint(IUserManagerPanelProvider)
    cells_providers = ExtensionPoint(IUserListCellContributor)

    default_panel = Option('user_manager', 'admin_default_panel', 'profile',
                           """Default user admin panel.""")

    # IAdminPageProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield 'accounts', _("Accounts"), 'users', 'Users'

    def render_admin_panel(self, req, cat, page, path_info):
        username = None
        panel = None
        panel_path_info = None

        data = {}
        um_data = dict(default_panel=self.default_panel,
                       messages=[], errors=[])

        # collecting username, current panel and eventual path_info
        if path_info is not None:
            path_info_list = path_info.split('/')
            username = path_info_list[0]
            if len(path_info_list) > 1:
                panel = path_info_list[1]
            if len(path_info_list) > 2:
                panel_path_info = path_info_list[2:]

        # action handling
        if 'um_session_management' in req.args and panel is None:
            return self._do_session_management(req, cat, page, path_info)

        if req.method == 'POST' and panel is None:
            try:
                if 'um_newuser_create' in req.args:
                    um_data['messages'].append(self._do_create_user(req))
                elif 'um_user_delete' in req.args:
                    um_data['messages'].append(self._do_delete_user(req))
                elif 'um_import_current_users' in req.args:
                    um_data['messages'].append(
                        self._do_import_current_users(req))
            except Exception, e:
                um_data['errors'].append(e)

        if username:
            user = UserManager(self.env).get_user(username)
            panels, providers = self._get_panels(req)
            um_data.update(user=user, panels=panels)
            if panel:
                um_data['default_panel'] = panel
                if panel in providers:
                    um_data.update(panel=panel)
                    provider = providers.get(panel)
                    try:
                        panel_template, data = \
                            provider.render_usermanager_admin_panel(
                                req, panel, user, panel_path_info)
                        um_data.update(template=panel_template)
                    except Exception, e:
                        um_data['errors'].append(e)

                    # Moving messages from data to um_data
                    if 'errors' in data:
                        um_data['errors'].extend(data.pop('errors'))
                    if 'messages' in data:
                        um_data['messages'].extend(data.pop('messages'))

        # adding user list
        um_data.update(users=UserManager(self.env).get_active_users())

        # additional cells
        um_data.update(cells=list(self._get_cells(um_data['users'])))

        # adding usernamager's data to the data dict
        data.update(user_manager=um_data)

        data['sort'] = req.args.get('sort') or 'name'
        data['asc'] = req.args.get('asc') or '1'

        # checking for external users
        trac_managed_users_out = \
            self._do_import_current_users(req, dry_run=True)
        if trac_managed_users_out:
            um_data['errors'].append(
                html.form(html.b(_("WARNING: ")),
                          _(" %(users)s users are not added to the team.",
                            users=', '.join(trac_managed_users_out)),
                          html.input(type='submit',
                                     name='um_import_current_users',
                                     value=_("Add Users")),
                                     action=req.href.admin('accounts/users'),
                                     method='post'))

        try:
            from acct_mgr.api import AccountManager
        except ImportError:
            data.update(account_manager={'has_user': lambda x: False})
            self.log.error("Account manager not loaded")
        else:
            data.update(account_manager=AccountManager(self.env))

        # adding stylesheets
        add_stylesheet(req, 'tracusermanager/css/admin_um.css')
        add_script(req, 'tracusermanager/js/admin_um.js')

        return 'admin_um.html', data

    # Internal methods

    def _do_create_user(self, req):
        """ """
        if not req.args.get('um_newuser_username') or \
                not req.args.get('um_newuser_username').strip():
            raise TracError(_("Username field is mandatory"))

        is_trac_managed = req.args.get('um_newuser_type') == 'trac-managed'
        if is_trac_managed and not req.args.get('um_newuser_password'):
            raise TracError(_("Password field it's mandatory"))

        user = User(req.args.get('um_newuser_username').strip())
        for field in ['name', 'email', 'role'] + (
                is_trac_managed and ['password'] or []):
            if field == 'password':
                if req.args.get('um_newuser_password') == \
                        req.args.get('um_newuser_confirm_password'):
                    try:
                        from acct_mgr.api import AccountManager
                    except ImportError, e:
                        self.log.error(e)
                        raise TracError(_("Unable to set %(user)s's "
                                          "password. Please check out log "
                                          "messages.", user=user.username))
                    else:
                        password = req.args.get('um_newuser_password')
                        AccountManager(self.env).set_password(user.username,
                                                              password)
                else:
                    raise TracError(_("Passwords don't match"))
                continue
            if req.args.get('um_newuser_%s' % field):
                user[field] = req.args.get('um_newuser_%s' % field)

        if UserManager(self.env).create_user(user):
            return _("Successfully created user %(user)s.",
                     user=user.username)

    def _do_delete_user(self, req):
        """ """
        username = req.args.get('um_deleteuser_username')
        if UserManager(self.env).delete_user(username):
            return _("Successfully removed user %(user)s.", user=username)

    def _do_import_current_users(self, req, dry_run=False):
        """ """
        active_users = [user.username for user in
                        UserManager(self.env).get_active_users()]
        try:
            from acct_mgr.api import AccountManager
        except ImportError:
            return []
        known_users = list(AccountManager(self.env).get_users())

        imported_users = []
        for username in known_users:
            if username not in active_users:
                imported_users.append(username)
                if not dry_run:
                    UserManager(self.env).create_user(User(username))
        if dry_run:
            return imported_users

        if imported_users:
            return _("Successfully imported the following users %(user)s.",
                     user=','.join(imported_users))
        else:
            return _("No users imported.")

    def _do_session_management(self, req, cat, panel, path_info):
        if req.method == 'POST' and 'um_session_delete_selected' in req.args:
            sel = req.args.getlist('sel')
            if sel:
                with self.env.db_transaction as db:
                    db.executemany("""
                        DELETE FROM session_attribute WHERE sid=%s
                        """, [(sid,) for sid in sel])
                    db.executemany("""
                        DELETE FROM session WHERE sid=%s
                        """, [(sid,) for sid in sel])
                add_notice(req, "Succesfully removed [%s] sessions."
                           % (",".join(sel)))
            else:
                add_warning(req, "No session ids selected")

        team = [user.username for user in
                UserManager(self.env).get_active_users()]
        sessions = {}
        for username, name, email in self.env.__class__.get_known_users(
                self.env):
            sessions[username] = dict(username=username,
                                      name=name,
                                      email=email, in_team=username in team)

        for username, last_visit in self.env.db_query("""
                SELECT sid,last_visit FROM session WHERE authenticated=1
                """):
            if username in sessions and last_visit:
                sessions[username]['last_visit'] = format_datetime(last_visit)

        data = dict(sessions=sorted(sessions.itervalues(),
                                    key=lambda session: session['username']))

        return 'admin_session_management.html', data

    def _get_panels(self, req):
        """Return a list of available admin panels."""
        panels = []
        providers = {}

        for provider in self.panel_providers:
            p = list(provider.get_usermanager_admin_panels(req))
            for panel in p:
                providers[panel[0]] = provider
            panels += p

        return panels, providers

    def _get_cells(self, user_list):
        for provider in self.cells_providers:
            for cell, label, order in provider.get_userlist_cells():
                yield dict(name=cell, label=label, order=order,
                           render_method=provider.render_userlist_cell)
