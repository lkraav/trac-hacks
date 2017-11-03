# -*- coding: utf-8 -*-
# Copyright (C) 2008 Abbywinters.com
# trac-dev@abbywinters.com
# Contributor: Zach Miller

import re
from datetime import datetime

from genshi.filters.transform import Transformer
from trac.config import ListOption
from trac.core import Component, implements
from trac.perm import IPermissionRequestor, PermissionError
from trac.ticket import TicketSystem
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.util import as_int
from trac.util.datefmt import utc
from trac.util.html import html
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.main import IRequestHandler


class GridModifyModule(Component):

    implements(IPermissionRequestor, IRequestHandler,
               ITemplateProvider, ITemplateStreamFilter)

    fields = ListOption('gridmodify', 'fields', '', doc="""
        List of fields that will be modifiable.
        """)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TICKET_GRID_MODIFY', ('TICKET_ADMIN', ['TICKET_GRID_MODIFY'])]

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('gridmod', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/gridmod(?:/.*)?$', req.path_info)

    def process_request(self, req):
        try:
            if 'TICKET_GRID_MODIFY' in req.perm:

                id = as_int(req.args.get('ticket'), None)
                ticket = Ticket(self.env, id)
                action = 'leave'

                # Save the action controllers we need to call side-effects
                # for before we save the changes to the ticket.
                controllers = list(self._get_action_controllers(req, ticket,
                                                                action))

                for field in TicketSystem(self.env).get_ticket_fields():
                    field_name = field['name']

                    if field_name not in req.args:
                        continue

                    val = req.args.get(field_name)
                    if field['type'] == 'select':
                        if val in field['options'] or val == '':
                            ticket[field_name] = val
                    elif field['type'] == 'text':
                        ticket[field_name] = val
                    elif field['type'] == 'checkbox':
                        if val == 'True' or val == '1':
                            val = '1'
                        else:
                            val = '0'
                        ticket[field_name] = val
                    elif field['type'] == 'radio':
                        ticket[field_name] = val
                    # Note: We are ignoring TextArea for now, as there are
                    # several complications including:
                    #   * Rendering is handled differently in the report form
                    #   * TextAreas support Wiki formatting so would need to
                    #     use the Wiki engine

                now = datetime.now(utc)
                ticket.save_changes(req.authname, None, now)

                tn = TicketNotifyEmail(self.env)
                try:
                    tn.notify(ticket, newticket=False, modtime=now)
                except Exception, e:
                    self.log.info("Failure sending notification on change to "
                                  "ticket #%s: %s", ticket.id, e)

                # After saving the changes, apply the side-effects.
                for controller in controllers:
                    self.log.info('Side effect for %s',
                                  controller.__class__.__name__)
                    controller.apply_action_side_effects(req, ticket, action)
            else:
                raise PermissionError("Permission denied")
        except Exception:
            import traceback
            self.log.error("GridModifyModule: Failure editing grid.\n%s",
                           traceback.format_exc())
            req.send_error(traceback.format_exc(), content_type='text/plain')
        else:
            req.send('OK', 'text/plain')

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        """Modifies query page to add modifiable components"""

        # We create an invisible storage div in the document for the default
        # tag values. JQuery then uses this information to update the
        # relevant fields on the page.
        if filename in ('query.html', 'report_view.html') and \
                'TICKET_GRID_MODIFY' in req.perm:
            add_script(req, 'gridmod/gridmod.js')
            div = html.div(id='table_inits_holder', style='display:none;')
            div.append('\n')
            ts = TicketSystem(self.env)

            for field in ts.get_ticket_fields():
                if field['name'] == 'owner':
                    ts.eventually_restrict_owner(field)

                # SELECT tags
                if field['type'] == 'select' and 'options' in field and \
                        (field['name'] in self.fields or not self.fields):
                    select = html.select(name=field['name'],
                                         class_='gridmod_form')
                    select.append('\n')
                    # HACK: For some reason custom fields that have a blank
                    # value as a valid option don't actually have that blank
                    # value among the options in field['options'] so
                    # we force a blank option in in the case where the
                    # _default_ value is blank.
                    if 'value' in field and field['value'] == '' and \
                            '' not in field['options']:
                        select.append(html.option())
                        select.append('\n')
                    for option in field['options']:
                        select.append(html.option(option, value=option))
                        select.append('\n')
                    div.append(select)

                # INPUT TEXT tags
                elif field['type'] == 'text' and field['name'] in self.fields:
                    text = html.input(type='text', name=field['name'],
                                      class_='gridmod_form')
                    if 'value' in field:
                        text.append(field['value'])
                    else:
                        text.append('')
                    div.append(text)

                # INPUT CHECKBOX tags
                elif field['type'] == 'checkbox' and \
                        field['name'] in self.fields:
                    checkbox = html.input(type='checkbox', name=field['name'],
                                          class_='gridmod_form')
                    if 'value' in field:
                        checkbox.append(field['value'])
                        if field['value'] == 1 or field['value'] is True:
                            checkbox(checked='checked')
                    else:
                        checkbox.append('0')
                    div.append(checkbox)

                # INPUT RADIO tags
                elif field['type'] == 'radio' and \
                        field['name'] in self.fields:
                    # This is slightly complicated.
                    # We convert the radio values into a SELECT tag for
                    # screen real estate reasons.
                    # It gets handled as a SELECT at the server end of the
                    # AJAX call, which appears to work fine.
                    # Note: If none of the RADIO buttons is checked, we
                    # default here to checking the first one, for code safety.
                    # That should never happen.
                    default_decided = False
                    radio_select = html.select(name=field['name'],
                                               class_='gridmod_form')
                    default_val = None
                    if 'value' in field:
                        default_val = field['value']
                        default_decided = True
                    for option in field['options']:
                        select_option = html.option(option, value=option)
                        if option == default_val or not default_decided:
                            select_option(selected="selected")
                            default_decided = True
                        radio_select.append(select_option)
                        radio_select.append('\n')
                    div.append(radio_select)
                div.append('\n')

            stream |= Transformer('//div[@id="content"]').append(div)
        return stream

    def _get_action_controllers(self, req, ticket, action):
        """Generator yielding the controllers handling the given `action`"""
        for controller in TicketSystem(self.env).action_controllers:
            actions = [a for w, a in
                       controller.get_ticket_actions(req, ticket)]
            if action in actions:
                yield controller
