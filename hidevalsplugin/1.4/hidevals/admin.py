# -*- coding: utf-8 -*-
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
# Copyright (c) 2008 Iker Jimenez. All rights reserved.

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.web.chrome import ITemplateProvider

from .api import HideValsSystem


class HideValsAdminModule(Component):
    """Admin page for configuring the TracHideVals plugins."""

    implements(IAdminPanelProvider, ITemplateProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            for field in TicketSystem(self.env).get_ticket_fields():
                if 'options' in field:
                    yield ('hidevals', 'Hide Values',
                           field['name'], field['label'])

    def render_admin_panel(self, req, cat, page, path_info):
        fields = TicketSystem(self.env).get_ticket_fields()
        field = {f['name']: f for f in fields}[page]
        values = self.env.db_query("""
                SELECT sid, value FROM hidevals WHERE field=%s
                """, (field['name'],))
        enabled = field['name'] not in HideValsSystem(self.env).dont_filter
        if req.method == 'POST':
            if 'add' in req.args:
                group = req.args['group']
                value = req.args['value']
                if (group, value) not in values:
                    self.env.db_transaction("""
                        INSERT INTO hidevals (sid, field, value)
                        VALUES (%s, %s, %s)
                        """, (group, field['name'], value))
            elif 'remove' in req.args:
                sel = req.args.getlist('sel')
                for val in sel:
                    group, value = val.split('#', 1)
                    self.env.db_transaction("""
                        DELETE FROM hidevals
                        WHERE sid=%s AND field=%s AND value=%s
                        """, (group, field['name'], value))
            elif 'toggle' in req.args:
                new_val = HideValsSystem(self.env).dont_filter[:]
                if enabled:
                    new_val.append(field['name'])
                else:
                    new_val.remove(field['name'])
                self.config.set('hidevals', 'dont_filter',
                                ', '.join(sorted(new_val)))
                self.config.save()

            req.redirect(req.href.admin(cat, page))

        return 'admin_hidevals.html', {
            'field': field,
            'values': [{'group': g, 'value': v} for g, v in values],
            'enabled': enabled
        }

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []
