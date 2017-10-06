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
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider, add_warning

from tracusermanager.api import UserManager


class TicketTeamDispatcherAdmin(Component):
    """Provides functions related to registration
    """
    implements(IAdminPanelProvider, IEnvironmentSetupParticipant,
               ITemplateProvider)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        return 'ttd' not in self.config['ticket-custom']

    def upgrade_environment(self, db=None):
        self.config.set('ticket-custom', 'ttd', 'select')
        self.config.set('ticket-custom', 'ttd.label', 'Team')
        self.config.save()

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield 'ticket', 'Ticket System', 'ttd', 'Team Dispatcher'

    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('TICKET_ADMIN')

        users = UserManager(self.env).get_active_users()
        caption = self.get_caption()
        teams = self.get_teams()

        if req.method == 'POST':
            action = req.args.get('action')
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
                for item in req.args.getlist('sel'):
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

            elif action == 'notify':
                self.set_notify_on('create', req.args.get('notify_on_create'))
                self.set_notify_on('change', req.args.get('notify_on_change'))
                self.set_notify_on('delete', req.args.get('notify_on_delete'))

            req.redirect(req.href.admin('ticket/ttd'))

        return 'team_dispatcher_admin.html', {
            'teams': teams,
            'users': users,
            'caption': caption,
            'notify_on_create': self.get_notify_on('create'),
            'notify_on_change': self.get_notify_on('change'),
            'notify_on_delete': self.get_notify_on('delete'),
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

    def get_notify_on(self, opt):
        return self.config.getbool('team-dispatcher', 'notify_on_' + opt)

    def set_notify_on(self, opt, value):
        value = True if value == 'on' else False
        self.config.set('team-dispatcher', 'notify_on_' + opt, value)
        self.config.save()

    def get_teams(self):
        return self.config.getlist('ticket-custom', 'ttd.options', sep='|')

    def set_teams(self, teams):
        self.config.set('ticket-custom', 'ttd.options', '|'.join(teams))
        self.config.save()
