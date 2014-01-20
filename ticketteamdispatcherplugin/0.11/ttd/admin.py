# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Alexander von Bremen-Kuehne
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider, add_warning

from tracusermanager.api import UserManager


class TicketTeamDispatcherAdmin(Component):
    """
        Provides functions related to registration
    """
    implements(ITemplateProvider, IAdminPanelProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', 'Ticket System', 'ttd', 'Team Dispatcher')
        
    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('TICKET_ADMIN')

        action = req.args.get('action')
        
        users = UserManager(self.env).get_active_users()
        caption = self.get_caption()
        teams = self.get_teams()
                
        if action:
            if action == 'rename':
                caption = req.args.get('caption')
                self.set_caption(caption)

            elif action == 'addteam':
                new_team = req.args.get('team')
                if new_team:
                    if new_team not in teams:
                        teams.append(new_team)
                        self.set_teams(teams)
                    else:
                        add_warning(req, _('Team "%(team)s" already exists',
                                           team=new_team))

            elif action == 'addtoteam':
                team = req.args.get('team')
                username = req.args.get('subject')
                for user in users:
                    if user.username == username:
                        user[team] = '1'
                        user.save()

            elif action == 'remove':
                sel = req.args.get('sel')
                sel = sel if isinstance(sel, list) else [sel]
                for item in sel:
                    if ':' in item:
                        username, team = item.split(':', 1)
                        for user in users:
                            if user.username == username:
                                user[team] = '0'
                                user.save()
                    else:
                        for user in users:
                            del user[item]
                            user.save()
                        teams.remove(item)
                        self.set_teams(teams)

        return 'ttd_admin.html', {
            'teams': teams,
            'users': users,
            'caption': caption
        }

    # INavigationContributor methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []

    # Internal methods
    def get_caption(self):
        return self.config.get('ticket-custom', 'ttd.label')

    def set_caption(self, caption):
        self.config.set('ticket-custom', 'ttd.label', caption)
        self.config.save()

    def get_teams(self):
        return self.config.getlist('ticket-custom', 'ttd.options', sep='|')

    def set_teams(self, teams):
        self.config.set('ticket-custom', 'ttd.options', '|'.join(teams))
        self.config.save()
