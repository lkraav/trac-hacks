# Copyright (C) 2011 Brent Atkinson
# All rights reserved.
#
# This software is licensed as described in the file LICENSE.txt, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.prefs import IPreferencePanelProvider
from trac.ticket.api import TicketSystem
from trac.util.translation import _
from trac.web.chrome import add_notice, add_stylesheet


class MultiProjectBacklogPrefPanel(Component):
    implements(IPreferencePanelProvider)

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
            fields = req.args.get('backlog_fields')
            req.session['backlog_fields'] = fields
            add_notice(req, _("Your backlog preferences have been saved."))
            req.redirect(req.href.prefs(panel or None))

        custom_fields = [(cf['name'], cf['label']) for cf in
                         TicketSystem(self.env).get_custom_fields()]
        add_stylesheet(req, 'mpbacklog/css/backlog.css')
        return 'prefs_backlog.html', {
            'fields': self._ticket_fields + custom_fields,
            'shown_fields':
                req.session.get('backlog_fields') or [field[0] for field in
                                                      self._ticket_fields]
        }
