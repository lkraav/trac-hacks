# -*- coding: utf-8 -*-
#
# Copyright (C) 2009, 2011, 2013 John Szakmeister
# Copyright (C) 2016-2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import get_distribution, parse_version
from trac.core import Component, implements
from trac.prefs import IPreferencePanelProvider
from trac.ticket.api import TicketSystem
from trac.util.translation import _
from trac.web.chrome import add_notice, add_stylesheet


class MultiProjectBacklogPrefPanel(Component):
    implements(IPreferencePanelProvider)

    # Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
    # creation using trac.util.html.tag and friends
    pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')

    _ticket_fields = [
        (u'id', u'Id'), (u'summary', u'Summary'), (u'component', u'Component'),
        (u'version', u'Version'), (u'type', u'Type'), (u'owner', u'Owner'),
        (u'status', u'Status'), (u'time_created', u'Created')
    ]

    # IPreferencePanelProvider methods

    def get_preference_panels(self, req):
        yield ('mpbacklog', _('Backlog'))

    def render_preference_panel(self, req, panel):
        if req.method == 'POST':
            fields = req.args.getlist('backlog_fields')
            req.session['backlog_fields'] = fields
            add_notice(req, _("Your preferences have been saved."))
            req.redirect(req.href.prefs(panel or None))

        custom_fields = [(cf['name'], cf['label']) for cf in
                         TicketSystem(self.env).get_custom_fields()]
        add_stylesheet(req, 'mpbacklog/css/backlog.css')
        data = {
            'fields': self._ticket_fields + custom_fields,
            'shown_fields':
                req.session.get('backlog_fields') or [field[0] for field in self._ticket_fields]
            }
        if self.pre_1_3:
            return 'prefs_backlog.html', data
        else:
            return 'mp_prefs_backlog.html', data
