# -*- coding: utf-8 -*-
#
# Copyright (C) Mark Ryan
# Copyright (C) Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import re

from .jtransformer import JTransformer
from trac.cache import cached
from trac.config import IntOption
from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket.api import ITicketManipulator, ITicketChangeListener, TicketSystem
from trac.ticket.model import Ticket
from trac.util.html import html as tag
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, Chrome, ITemplateProvider, web_context


try:
    unicode
except NameError:
    unicode = str

INDENT_PERCENT = 3


class ChildTicketsModule(Component):
    """Component which inserts the child ticket data into the ticket page"""

    implements(IRequestFilter, ITemplateProvider,
               ITicketChangeListener, ITicketManipulator)

    max_view_depth = IntOption('childtickets', 'max_view_depth', default=3,
                               doc="Maximum depth of child ticket tree shown on the ticket page.")
    recursiondepth = IntOption('childtickets', 'recursion_warn', default=7,
                               doc="Depth of tree at which we assume that there is a loop in our "
                                     "ticket tree.")

    @cached
    def childtickets(self):
        x = {}  # { parent -> children } - 1:n

        for child, parent in self.env.db_query("""
                SELECT ticket,value FROM ticket_custom WHERE name='parent'
                """):
            parent = parent or ''
            pids = parent.split()
            for pid in pids:
                if pid and re.match(r'#\d+', pid):
                    x.setdefault(int(pid.lstrip('#')), []).append(child)
        return x

    @cached
    def parents(self):
        x = {}
        for ticket, parent in self.env.db_query("""
                        SELECT ticket,value FROM ticket_custom WHERE name='parent' AND NOT value=''
                        """):
            parent = parent or ''
            pids = parent.split()
            for pid in pids:
                if pid and re.match(r'#\d+', pid):
                    x.setdefault(ticket, []).append(int(pid.lstrip('#')))
        return x

    def create_childticket_tree_html(self, req, ticket):

        # Modify ticket.html with sub-ticket table, create button, etc...
        # As follows:
        # - If ticket has no child tickets and child tickets are NOT allowed then skip.
        # - If ticket has child tickets and child tickets are NOT allowed (ie. rules changed or ticket type changed after children were assigned),
        #   print list of tickets but do not allow any tickets to be created.
        # - If child tickets are allowed then print list of child tickets or 'No Child Tickets' if non are currently assigned.
        if ticket and ticket.exists:
            def indented_table(req, tkt, treecolumns, indent=0):
                """Create a table from the ticket tkt which may be indented.

                :param tkt:            a Trac ticket
                :param treecolumns:    list of column names
                :param indent:         level of indentation for this table. Int value starting with 0.

                The table has a header holding the items described by treecolums. Next row
                are the data items matching the header. The following row spans all columns
                and holds the ticket description.
                If the description contains wiki data it will be porperly parsed and inserted
                into the result.
                For each level of indentation (0, 1, 2, ...) the table will be indented by a
                percentage defined as INDENT_PERCENT (usually 3..5%).
                """
                from trac.wiki.formatter import format_to_html
                def recursion_warning():
                    return tag.table(
                        tag.tbody(self._table_row(req, tkt, treecolumns),
                                  tag.tr(
                                      tag.td(
                                          _("Recursion detected! Check if you have a loop in your ticket tree."),
                                          colspan="%s" % str(1 + len(treecolumns))),
                                      class_="error",
                                  ),
                                  ),
                        class_="listing tickets",
                        style="margin-left: 10%; width : 80%",
                    )
                # Admin may have removed a custom field still in the list of table headers
                treecolumns = [col for col in treecolumns if col in field_names]
                desc = format_to_html(self.env, web_context(req), tkt['description'])

                if indent == self.recursiondepth - 1:
                    return recursion_warning()

                if tkt['status'] == 'closed':
                    cls = "listing ct-table closed"
                else:
                    cls = "listing ct-table"

                # Return the table
                return tag.table(
                    tag.thead(
                        tag.tr(tag.th("Ticket", class_="id"),
                               [tag.th(field_names[col], class_=col) for col in treecolumns]
                               )
                    ),
                    tag.tbody(self._table_row(req, tkt, treecolumns),
                              tag.tr(
                                  tag.td(desc, class_="description", colspan="%s" % str(1 + len(treecolumns))),
                                  class_="hilightrow",
                              ),
                              tag.tr(
                                  tag.td(_("(Rest of the child ticket tree is hidden)"),
                                         class_="system-message notice", colspan="%s" % str(1 + len(treecolumns))),
                                  class_="hilightrow",
                              ) if tkt.max_view else None,
                              ),
                    class_=cls,
                    style="margin-left: %s%%; width : %s%%" % (str(indent * INDENT_PERCENT),
                                                               str(100 - indent * INDENT_PERCENT)),
                )

            def create_table_tree(req, tickets):
                """
                    Create a tree of ticket tables from the tickets in the list tickets.
                """
                childtree = []
                for tkt in tickets:
                    # if tkt['indent'] == 1:
                    if tkt.indent == 1:
                        div = tag.div(class_="ct-tables")
                        childtree.append(div)

                    treecolumns = self.config.getlist('childtickets', 'parent.%s.table_headers' % tkt['type'],
                                                      default=['summary', 'owner'])
                    # The description will always be displayed in separate td no matter whats defined in the ini
                    if 'description' in treecolumns:
                        treecolumns.remove('description')

                    # div.append(indented_table(req, tkt, treecolumns, tkt['indent'] - 1))
                    div.append(indented_table(req, tkt, treecolumns, tkt.indent - 1))
                return childtree

            # Are child tickets allowed?
            childtickets_allowed = self.config.getbool('childtickets', 'parent.%s.allow_child_tickets' % ticket['type'])

            # Are there any child tickets to display?
            childtickets = [Ticket(self.env, n) for n in self.childtickets.get(ticket.id, [])]
            # (tempish) fix for #8612 : force sorting by ticket id
            childtickets = sorted(childtickets, key=lambda t: t.id)

            parents = self._get_parents(ticket)
            # If there are no childtickets and the ticket should not
            # have any child tickets, we can simply drop out here.
            if not childtickets_allowed and not childtickets and not parents:
                return '', ''

            field_names = TicketSystem(self.env).get_ticket_field_labels()

            # The additional section on the ticket is built up of (potentially) three parts: header, ticket table, buttons. These
            # are all 'wrapped up' in a 'div' with the 'attachments' id (we'll just pinch this to make look and feel consistent with any
            # future changes!)
            snippet = tag.div(id="ct-children", class_="collapsed")  # foldable child tickets area
            parsnippet = tag.div(id="ct-parents", class_="collapsed")  # foldable parent tickets area

            # Our 'main' display consists of divs.
            buttonform = tag.div()
            treediv = tag.div()  # This is for displaying the child ticket tree

            if parents:
                parentdiv = create_table_tree(req, parents)  # This is a list but this is handled gracefully
            else:
                parentdiv = tag.div(tag.p(_("No parent tickets.")), )

            # Test if the ticket has children: If so, then list in pretty table.
            if childtickets:
                all_tickets = []  # We need this var for the recursive _indent_children() collecting the tickets
                self._indent_children(ticket, all_tickets)
                # This is a list of whole trees of child->grandchild->etc
                # for each child ticket
                treediv = create_table_tree(req, all_tickets)

            # trac.ini : child tickets are allowed - Set up 'create new ticket' buttons.
            if childtickets_allowed:
                # Can user create a new ticket? If not, just display title (ie. no 'create' button).
                if 'TICKET_CREATE' in req.perm(ticket.resource):
                    # Always pass these fields
                    default_child_fields = (tag.input(type="hidden", name="parent", value='#' + str(ticket.id)),)

                    # Pass extra fields defined in inherit parameter of parent
                    inherited_child_fields = [
                        tag.input(type="hidden", name="%s" % field, value=ticket[field]) for field in
                        self.config.getlist('childtickets', 'parent.%s.inherit' % ticket['type'])
                    ]

                    # If child types are restricted then create a set of buttons for the allowed types (This will override 'default_child_type).
                    restrict_child_types = self.config.getlist('childtickets',
                                                               'parent.%s.restrict_child_type' % ticket['type'],
                                                               default=[])

                    if not restrict_child_types:
                        # trac.ini : Default 'type' of child tickets?
                        default_child_type = self.config.get('childtickets',
                                                             'parent.%s.default_child_type' % ticket['type'],
                                                             default=self.config.get('ticket', 'default_type'))

                        # ... create a default submit button
                        if ticket['status'] == 'closed':
                            submit_button_fields = (
                                tag.input(type="submit", disabled="disabled", name="childticket",
                                          value="New Child Ticket", title="Create a child ticket"),
                                tag.input(type="hidden", name="type", value=default_child_type),)
                        else:
                            submit_button_fields = (
                                tag.input(type="submit", name="childticket", value="New Child Ticket",
                                          title="Create a child ticket"),
                                tag.input(type="hidden", name="type", value=default_child_type),)
                    else:
                        if ticket['status'] == 'closed':
                            submit_button_fields = [
                                tag.input(type="submit", disabled="disabled", name="type", value="%s" % ticket_type,
                                          title="Create a %s child ticket" % ticket_type) for ticket_type in
                                restrict_child_types]
                        else:
                            submit_button_fields = [tag.input(type="submit", name="type", value="%s" % ticket_type,
                                                              title="Create a %s child ticket" % ticket_type) for
                                                    ticket_type in restrict_child_types]
                    buttonform = tag.form(tag.p(_("Create New Ticket")),
                        tag.div(default_child_fields, inherited_child_fields, submit_button_fields),
                        method="get", action=req.href.newticket(),
                        class_="child-ticket-form", )

            # Add our new elements to the stream
            if parents:
                parsnippet.append(tag.h3("Parent Tickets ",
                                         tag.span('(%s)' % len(parents), class_="trac-count"),
                                         class_="foldable"))
                parsnippet.append(tag.div(parentdiv, id="parenttickets"))

            snippet.append(tag.h3("Child Tickets ",
                                  tag.span('(%s)' % len(childtickets), class_="trac-count"),
                                  class_="foldable"))
            if childtickets:
                snippet.append(tag.div(treediv, buttonform, id="childtickets"))
            else:
                snippet.append(tag.div(buttonform))

            return snippet, parsnippet
        else:
            return '', ''

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):

        if data and template == 'ticket.html':
            # Get the ticket info.
            ticket = data.get('ticket')
            html, parent_html = self.create_childticket_tree_html(req, ticket)

            filter_lst = []
            if html:
                # xpath: //div[@id="ticket"]
                xform = JTransformer('div#ticket')
                filter_lst.append(xform.after(unicode(html)))
            if parent_html:
                # xpath: //div[@id="ticket"]
                xform = JTransformer('div#ticket')
                filter_lst.append(xform.after(unicode(parent_html)))
            if html or parent_html:
                # Add our own styles for the ticket lists.
                add_stylesheet(req, 'ct/css/childtickets.css')
                add_script_data(req, {'childtkt_filter': filter_lst})
                add_script(req, 'ct/js/ct_jtransform.js')

        return template, data, content_type

    # ITicketChangeListener methods

    def ticket_changed(self, ticket, comment, author, old_values):
        if 'parent' in old_values:
            del self.childtickets

    def ticket_created(self, ticket):
        del self.childtickets

    def ticket_deleted(self, ticket):
        # NOTE: Is there a way to 'block' a ticket deletion if it still
        # has child tickets?
        del self.childtickets

    # ITicketManipulator methods

    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):

        # Don't allow ticket to be 'resolved' if any child tickets are
        # still open.
        if req.args.get('action') == 'resolve':
            for t in self.childtickets.get(ticket.id, []):
                if Ticket(self.env, t)['status'] != 'closed':
                    yield '', "Cannot resolve ticket while child ticket " \
                              "(#%s) is still open." % t

        # Check if the 'parent' field is being used.
        if not ticket.values.get('parent'):
            return

        par = ticket.values.get('parent').split()
        # Is it of correct 'format'?
        for item in par:
            if not re.match(r'^#\d+', item):
                yield 'parent', "The parent id must be of the form '#id' where 'id' is a valid ticket id."

        # Strip the '#' to get parent id.
        pids = []
        for item in par:
            pids.append(int(item.lstrip('#')))

        # Check we're not being daft and setting own id as parent.
        for item in pids:
            if ticket.id and item == ticket.id:
                yield 'parent', "The ticket has same id as parent id."

        # Recursive/Circular ticket check : Does ticket recursion goes too
        # deep (as defined by 'recursion_warn' in 'trac.ini')?
        max_depth = self.recursiondepth

        # The 'family tree' already consists of this ticket id plus the parent
        for pid in pids:
            fam_tree = [ticket.id, pid]
            for grandad in self._get_parent_id(pid):
                fam_tree.append(grandad)
                if ticket.id == grandad:
                    dependencies = ' --> '.join('#%s' % x for x in fam_tree)
                    yield 'parent', "The tickets have a circular dependency " \
                                    "upon each other : %s" % dependencies
                if len(fam_tree) > max_depth:
                    yield 'parent', "Parent/Child relationships go too deep, " \
                                    "'max_depth' exceeded (%s) : %s" % (
                    max_depth, ' - '.join(['#%s' % x for x in fam_tree]))
                    break

        # Try creating parent ticket instance : it should exist.
        for pid in pids:
            try:
                parent = Ticket(self.env, pid)
            except ResourceNotFound:
                yield 'parent', "The parent ticket #%d does not exist." % pid

            else:
                # NOTE: The following checks are checks on the parent ticket
                # being defined in the 'parent' box rather than on the child
                # ticket actually being created. It is therefore possible to
                # 'legally' create this child ticket but then for the restrictions
                # or type of the parent ticket to change - I have NOT restricted
                # the possibility to modify parent type after children have been
                # assigned, however, further modifications to the children
                # themselves would then throw up some errors and force the users
                # to re-set the child type.)

                # Does the parent ticket 'type' even allow child tickets?
                if not self.config.getbool('childtickets',
                                           'parent.%s.allow_child_tickets' %
                                                   parent['type']):
                    yield 'parent', "The parent ticket (#%s) has type %s which " \
                                    "does not allow child tickets." \
                                    % (pid, parent['type'])

                # It is possible the parent restricts the allowed type of children
                allowedtypes = self.config.getlist('childtickets',
                                                   'parent.%s.restrict_child_type'
                                                   % parent['type'], default=[])
                if allowedtypes and ticket['type'] not in allowedtypes:
                    yield 'parent', "The parent ticket (#%s) has type %s which " \
                                    "does not allow child type '%s'. Must be " \
                                    "one of : %s." \
                                    % (pid, parent['type'], ticket['type'],
                                       ','.join(allowedtypes))

                # If the parent is 'closed' then we should not be allowed to
                # create a new child ticket against that parent.
                if parent['status'] == 'closed':
                    yield 'parent', "The parent ticket (#%s) is not an active " \
                                    "ticket (status: %s)." \
                                    % (pid, parent['status'])

                self.log.debug("TracchildticketsModule : parent.ticket.type: %s",
                               parent['type'])

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ct', resource_filename(__name__, 'htdocs'))]

    def _table_row(self, req, ticket, columns):
        # Is the ticket closed?
        ticket_class = ''
        if ticket['status'] == 'closed':
            ticket_class = 'closed'

        chrome = Chrome(self.env)

        def get_value(field):
            if field == 'owner':
                return chrome.authorinfo(req, ticket[field])
            else:
                return ticket[field]

        return tag.tr(
            tag.td(tag.a("#%s" % ticket.id, href=req.href.ticket(ticket.id),
                         title="Child ticket #%s" % ticket.id,
                         class_=ticket_class), class_="id"),
            [tag.td(get_value(s), class_=s) for s in columns],
        )

    def _get_parent_id(self, ticket_id):
        # Create a temp dict to hold direct child->parent relationships.
        parenttickets = {}
        for parent, childtickets in self.childtickets.items():
            for child in childtickets:
                parenttickets[child] = parent
        while ticket_id in parenttickets:
            yield parenttickets[ticket_id]
            ticket_id = parenttickets[ticket_id]

    def _get_parents(self, ticket):
        tickets = []
        for tkt in self.parents.get(ticket.id, []):
            tckt = Ticket(self.env, tkt)
            tckt.indent = 1
            # We don't call self._indented_table() so we have to init it here
            tckt.max_view = False

            # tckt['indent'] = 1
            tickets.append(tckt)
        return sorted(tickets, key=lambda t: t.id)

    def _indent_children(self, ticket, all_tickets, indent=0):
        ticket.max_view = False
        if ticket.id in self.childtickets:
            indent += 1
            # Stop recursion when indentation exceeds the specified value
            if indent > self.recursiondepth:
                return
            for child in self.childtickets[ticket.id]:
                if indent > self.max_view_depth:
                    ticket.max_view = True  # Mark that we don't want to show more children
                    return
                child = Ticket(self.env,child)
                child.indent = indent
                # child['indent'] = indent
                all_tickets.append(child)
                self._indent_children(child, all_tickets, indent)
