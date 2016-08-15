# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2012 Colin Guthrie <trac@colin.guthr.ie>
# Copyright (c) 2011-2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.admin.api import IAdminPanelProvider
from trac.core import Component, implements
from trac.web.chrome import add_notice
from trac.util.translation import _


class WorklogAdminPanel(Component):
    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'WORK_ADMIN' in req.perm:
            yield ('ticket', _("Ticket System"), 'worklog', _("Work Log"))

    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('WORK_ADMIN')

        settings = ('autostop', 'autostopstart', 'autoreassignaccept',
                    'comment', 'timingandestimation', 'trachoursplugin')

        if req.method == 'POST' and 'update' in req.args:
            for field in settings:
                if field in req.args:
                    self.config.set('worklog', field, True)
                else:
                    self.config.set('worklog', field, False)
                roundup = 1
                if 'roundup' in req.args:
                    try:
                        if int(req.args.get('roundup')) > 0:
                            roundup = int(req.args.get('roundup'))
                    except:
                        pass
                self.config.set('worklog', 'roundup', roundup)

            self.config.save()
            add_notice(req, _("Changes have been saved."))

        data = {'view': 'settings'}
        for field in settings:
            if self.config.getbool('worklog', field):
                data[field] = 'checked'

        if self.config.getint('worklog', 'roundup'):
            data['roundup'] = self.config.getint('worklog', 'roundup')

        return 'worklog_admin.html', data
