# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Alexander von Bremen-Kuehne
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.web.chrome import ITemplateProvider

from tracusermanager.api import UserManager


class TicketTeamDispatcherAdmin(Component):
    """
        Provides functions related to registration
    """
    implements(ITemplateProvider, IAdminPanelProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', 'Ticket System', 'ttd', 'Ticket Team Dispatcher')
        
    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('TICKET_ADMIN')

        action = req.args.get('action')
        
        users = UserManager(self.env).get_active_users()
        caption = self.get_caption()
        teams = self.get_teams()
                
        if action:
            # load data from post
            if action == 'rename':
                caption = req.args.get('caption')
                self.set_caption(caption)
            elif action == 'add':
                new_team = req.args.get('newTeam')
                
                can_add = True
                for team in teams:
                    if team == new_team:
                        can_add = False
                        break
                
                if can_add:
                    teams.append(new_team)
                    for user in users:
                        user[new_team] = '0'
                        user.save()
                    self.set_teams(teams)
            elif action == 'up':
                id = req.args.get('id')
                i = teams.index(id)
                if i > 0:
                    tmp = teams[i-1]
                    teams[i-1] = teams[i]
                    teams[i] = tmp
                    self.set_teams(teams)
            elif action == 'down':
                id = req.args.get('id')
                i = teams.index(id)
                if i < len(teams)-1:
                    tmp = teams[i+1]
                    teams[i+1] = teams[i]
                    teams[i] = tmp
                    self.set_teams(teams)
            elif action == 'delete':
                id = req.args.get('id')
                teams.remove(id)
                for user in users:
                    del user[id]
                    user.save()
                self.set_teams(teams)
            elif action == 'updateUsers':
                for user in users:
                    for team in teams:
                        if req.args.get('%s_%s' % (user.username, team)):
                            user[team] = '1'
                        else:
                            user[team] = '0'
                    user.save()

        return 'ttd_admin.html', {
            'teams' : teams,
            'users' : users,
            'caption' : caption
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
