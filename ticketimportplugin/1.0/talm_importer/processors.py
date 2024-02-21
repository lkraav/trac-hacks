#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import re
import time

from trac.ticket import model
from trac.util import get_reporter_id
from trac.util.datefmt import to_timestamp
from trac.util.html import Markup, tag
from trac.util.text import to_unicode
from trac.wiki.formatter import format_to_html

try:
    from trac.web.chrome import web_context
except ImportError:
    from trac.mimeview.api import Context
    def web_context(*args, **kwargs):
        return Context.from_request(*args, **kwargs)

from .compat import basestring, iteritems, unicode


_normalize_newline_re = re.compile('\r?\n|\r')

def _normalize_newline(value):
    if isinstance(value, basestring):
        value = _normalize_newline_re.sub('\r\n', value)
    return value


class ProcessorBase(object):

    def new_ticket(self, tkt_id=None):
        from .ticket import PatchedTicket
        return PatchedTicket(self.env, tkt_id)

    def format_to_html(self, wikidom, **kwargs):
        context = web_context(self.req)
        return format_to_html(self.env, context, wikidom, **kwargs)


class ImportProcessor(ProcessorBase):
    def __init__(self, env, db, req, filename, tickettime):
        self.env = env
        self.db = db
        self.req = req
        self.reporter = get_reporter_id(req)
        self.filename = filename
        self.modified = {}
        self.added = {}

        # TODO: check that the tickets haven't changed since preview
        self.tickettime = tickettime

        self.missingemptyfields = None
        self.missingdefaultedfields = None
        self.computedfields = None
        self.importedfields = None

    def start(self, importedfields, reconciliate_by_owner_also, has_comments):
        # Index by row index, returns ticket id
        self.crossref = []
        self.lowercaseimportedfields = [f.lower() for f in importedfields]

    def process_missing_fields(self, missingfields, missingemptyfields, missingdefaultedfields, computedfields):
        self.missingemptyfields = missingemptyfields
        self.missingdefaultedfields = missingdefaultedfields
        self.computedfields = computedfields

    def process_notimported_fields(self, notimportedfields):
        pass

    def process_comment_field(self, comment):
        pass

    def start_process_row(self, row_idx, ticket_id):
        if ticket_id > 0:
            # existing ticket
            self.ticket = self.new_ticket(tkt_id=ticket_id)
            changetime = to_timestamp(self.ticket['changetime'])

            if changetime > self.tickettime:
                # just in case, verify if it wouldn't be a ticket that has been
                # modified in the future (of course, it shouldn't happen... but
                # who know). If it's the case, don't report it as an error
                if changetime < int(time.time()):
                    # TODO: this is not working yet...
                    #raise TracError("Sorry, can not execute the import. The "
                    #                "ticket #%s has been modified by someone "
                    #                "else since preview. You must re-upload "
                    #                "and preview your file to avoid "
                    #                "overwriting the other changes." %
                    #                ticket_id)
                    pass
        else:
            self.ticket = self.new_ticket()
        self.comment = ''

    def process_cell(self, column, cell):
        cell = _normalize_newline(unicode(cell))
        column = column.lower()
        # if status of new ticket is empty, force to use 'new'
        if not self.ticket.exists and column == 'status' and not cell:
            cell = 'new'
        # this will ensure that the changes are logged, see model.py
        # Ticket.__setitem__
        self.ticket[column] = cell

    def process_comment(self, comment):
        self.comment = _normalize_newline(comment)

    def _tickettime(self):
        try:
            # 'when' is a datetime in 0.11, and an int in 0.10.
            # if we have trac.util.datefmt.to_datetime, we're likely with 0.11
            from trac.util.datefmt import to_datetime
            return to_datetime(self.tickettime)
        except ImportError:
            return self.tickettime

    def _insert_ticket(self, ticket, when=None):
        return ticket.insert(when=when)

    def _save_ticket(self, ticket, with_comment=True):
        if with_comment:
            if self.comment:
                comment = "''Batch update from file " + self.filename + ":'' " + self.comment
            else:
                comment = "''Batch update from file " + self.filename + "''"
        else:
            comment = None

        return ticket.save_changes(self.reporter, comment,
                                   when=self._tickettime())

    def end_process_row(self):
        if self.ticket.id == None:
            if self.missingemptyfields:
                for f in self.missingemptyfields:
                    if f in self.ticket.values and self.ticket[f] is None:
                        self.ticket[f] = ''

            if self.comment:
                description = self.ticket['description']
                if description:
                    description += '\r\n[[BR]][[BR]]\r\n'
                else:
                    description = ''
                self.ticket['description'] = (
                        "%s''Batch insert from file %s:''\r\n%s" %
                        (description, self.filename, self.comment))

            if self.computedfields:
                for f in self.computedfields:
                    if f not in self.lowercaseimportedfields and \
                            self.computedfields[f] is not None and \
                            self.computedfields[f]['set']:
                        self.ticket[f] = self.computedfields[f]['value']

            self._insert_ticket(self.ticket, when=self._tickettime())
            self.added[self.ticket.id] = 1
        else:
            if self.ticket.is_modified() or self.comment:
                self._save_ticket(self.ticket)
                self.modified[self.ticket.id] = 1

        self.crossref.append(self.ticket.id)
        self.ticket = None

    EnumClasses = {'component': model.Component, 'milestone': model.Milestone,
                   'version': model.Version, 'type': model.Type}

    def process_new_lookups(self, newvalues):
        for field, names in iteritems(newvalues):
            if field == 'status':
                continue

            try:
                enum = self.EnumClasses[field]
            except KeyError:
                class enum(model.AbstractEnum):
                    # here, you shouldn't put 'self.' before the class field.
                    type = field
                self.EnumClasses[field] = enum

            for name in names:
                lookup = enum(self.env)
                lookup.name = name
                lookup.insert()

    def process_new_users(self, newusers):
        pass

    # Rows is an array of dictionaries.
    # Each row is indexed by the field names in relativeticketfields.
    def process_relativeticket_fields(self, rows, relativeticketfields):
        # Find the WBS columns, if any.  We never expect to have more
        # than one but this is flexible and easy.  There's no good
        # reason to go to the trouble of ignoring extras.
        wbsfields = []
        for row in rows:
            for f in relativeticketfields:
                if row[f].find('.') != -1 and f not in wbsfields:
                    wbsfields.append(f)

        # If WBS column present, build reverse lookup to find the
        # ticket ID from a WBS number.
        wbsref = {}
        if wbsfields != []:
            row_idx = 0
            for row in rows:
                wbsref[row[wbsfields[0]]] = self.crossref[row_idx]
                row_idx += 1

        row_idx = 0
        for row in rows:
            id = self.crossref[row_idx]

            # Get the ticket (added or updated in the main loop
            ticket = self.new_ticket(tkt_id=id)

            for f in relativeticketfields:
                # Get the value of the relative field column (e.g., "2,3")
                v = row[f]
                # If it's not empty, process the contents
                if len(v) > 0:
                    # Handle WBS numbers
                    if f in wbsfields:
                        if row[f].find('.') == -1:
                            # Top level, no parent
                            ticket[f] = ''
                        else:
                            # Get this task's wbs
                            wbs = row[f]
                            # Remove the last dot-delimited field
                            pwbs = wbs[:wbs.rindex(".")]
                            # Look up the parent's ticket ID
                            ticket[f] = str(wbsref[pwbs])
                    # Handle dependencies
                    else:
                        s = []
                        for r in v.split(","):
                            # Make the string value an integer
                            r = int(r)

                            # The relative ticket dependencies are 1-based,
                            # array indices are 0-based.  Convert and look up
                            # the new ticket ID of the other ticket.
                            i = self.crossref[r-1]

                            # TODO check that i != id
                            s.append(str(i))

                        # Empty or not, use it to update the ticket
                        ticket[f] = ', '.join(s)

            self._save_ticket(ticket, with_comment=False)
            row_idx += 1

    def end_process(self, numrows):
        self.db.commit()

        data = {}
        data['title'] = 'Import completed'
        #data['report.title'] = data['title'].lower()
        notmodifiedcount = numrows - len(self.added) - len(self.modified)

        message = 'Successfully imported ' + str(numrows) + ' tickets (' + str(len(self.added)) + ' added, ' + str(len(self.modified)) + ' modified, ' + str(notmodifiedcount) + ' unchanged).'

        data['message'] = \
            Markup("<style type=\"text/css\">#report-notfound { display:none; }</style>\n") + \
            self.format_to_html(message)

        return 'import_preview.html', data


class PreviewProcessor(ProcessorBase):

    def __init__(self, env, db, req):
        self.env = env
        self.db = db
        self.req = req
        self.data = {'rows': []}
        self.ticket = None
        self.rowmodified = False
        self.styles = None
        self.modified = {}
        self.added = {}

    def start(self, importedfields, reconciliate_by_owner_also, has_comments):
        self.data['title'] = 'Preview Import'

        self.message = u''

        if 'ticket' in [f.lower() for f in importedfields]:
            self.message += ' * A \'\'\'ticket\'\'\' column was found: Existing tickets will be updated with the values from the file. Values that are changing appear in italics in the preview below.\n'
        elif 'id' in [f.lower() for f in importedfields]:
            self.message += ' * A \'\'\'id\'\'\' column was found: Existing tickets will be updated with the values from the file. Values that are changing appear in italics in the preview below.\n'
        else:
            self.message += ' * A \'\'\'ticket\'\'\' column was not found: tickets will be reconciliated by summary' + (reconciliate_by_owner_also and ' and by owner' or '') + '. If an existing ticket with the same summary' + (reconciliate_by_owner_also and ' and the same owner' or '') + ' is found, values that are changing appear in italics in the preview below. If no ticket with same summary ' + (reconciliate_by_owner_also and ' and same owner' or '') + 'is found, the whole line appears in italics below, and a new ticket will be added.\n'

        self.data['headers'] = [{ 'col': 'ticket', 'title': 'ticket' }]

        # we use one more color to set a style for all fields in a row...
        # the CS templates happens 'color' + color + '-odd'
        italic_selectors = [".color-new-odd td", ".color-new-even td",
                            ".modified-ticket-imported"]
        columns = importedfields[:]
        if has_comments:
            columns.append('comment')
        for col in columns:
            if col.lower() != 'ticket' and col.lower() != 'id':
                title = col.capitalize()
                self.data['headers'].append({ 'col': col, 'title': title })
                italic_selectors.append(".modified-%s" % col)
        self.styles = tag.style(
            "\n",
            ".ticket-imported, .modified-ticket-imported { width: 40px; }\n",
            "%s { font-style: italic; }\n" % ", ".join(italic_selectors),
            type='text/css')

    # This could be simplified...
    def process_missing_fields(self, missingfields, missingemptyfields, missingdefaultedfields, computedfields):
        self.message += ' * Some Trac fields are not present in the import. They will default to:\n\n'
        self.message += "   || '''field''' || '''Default value''' ||\n"
        if missingemptyfields:
            self.message += u"   || %s || ''(Empty value)'' ||\n" \
                            % u', '.join([to_unicode(x.capitalize()) for x in missingemptyfields])
        for f in missingdefaultedfields:
            self.message += u'   || %s || %s ||\n' % (to_unicode(f.capitalize()), computedfields[f]['value'])

        self.message += '(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).\n'

    def process_notimported_fields(self, notimportedfields):
        fields = tag()
        for idx, x in enumerate(notimportedfields):
            if idx:
                fields.append(', ')
            fields.append(to_unicode(x) if x else tag.em('(empty name)'))
        fields.append('.')
        self.message += (
            u" * Some fields will not be imported because they don't exist in Trac:\n"
            u'   {{{#!html\n'
            + unicode(fields) + u'\n' +
            u'}}}\n'
        )

    # Rows is an array of arrays.
    # Each row is indexed by the field names in relativeticketfields.
    def process_relativeticket_fields(self, rows, relativeticketfields):
        self.message += ' * Relative ticket numbers will be processed in: ' + ', '.join([x and x or "''(empty name)''" for x in relativeticketfields])  + '.\n'
        wbsfields=[]
        for row in rows:
            for f in relativeticketfields:
                self.env.log.debug("f %s, row '%s'" % (f, row[f]))
                if row[f].find('.') != -1:
                    self.env.log.debug("found")
                    if f not in wbsfields:
                        wbsfields.append(f)
        if wbsfields != []:
            self.message += '    WBS numbers processed in: ' + ', '.join([x and x or "''(empty name)''" for x in wbsfields])  + '.\n'

    def process_comment_field(self, comment):
        self.message += u' * The field "%s" will be used as comment when modifying tickets, and appended to the description for new tickets.\n' % comment

    def start_process_row(self, row_idx, ticket_id):
        self.ticket = None
        self.cells = []
        self.rowmodified = False
        self.row_idx = row_idx
        if ticket_id > 0:
            # existing ticket. Load the ticket, to see which fields will be modified
            self.ticket = self.new_ticket(ticket_id)

    def process_cell(self, column, cell):
        if self.ticket and not (column.lower() in self.ticket.values and self.ticket[column.lower()] == cell):
            self.cells.append( { 'col': column, 'value': cell, 'style': 'modified-' + column })
            self.rowmodified = True
        else:
            # if status of new ticket is empty, force to use 'new'
            if not self.ticket and column.lower() == 'status' and not cell:
                cell = 'new'
            self.cells.append( { 'col': column, 'value': cell, 'style': column })

    def process_comment(self, comment):
        column = 'comment'
        self.cells.append( { 'col': column, 'value': comment, 'style': column })

    def end_process_row(self):
        odd = len(self.data['rows']) % 2
        if self.ticket:
            if self.rowmodified:
                self.modified[self.ticket.id] = 1
                style = ''
                ticket = self.ticket.id
            else:
                style = ''
                ticket = self.ticket.id
        else:
            self.added[self.row_idx] = 1
            style = odd and 'color-new-odd' or 'color-new-even'
            ticket = '(new)'

        self.data['rows'].append({ 'style': style, 'cells': [{ 'col': 'ticket', 'value': ticket, 'style': '' }] + self.cells })

    def process_new_lookups(self, newvalues):
        if 'status' in newvalues:
            if len(newvalues['status']) > 1:
                msg = u' * Some values for the "Status" field do not exist: %s. They will be imported, but will result in invalid status.\n\n'
            else:
                msg = u' * A value for the "Status" field does not exist: %s. It will be imported, but will result in an invalid status.\n\n'

            self.message += (msg % u','.join(newvalues['status']))
            del newvalues['status']

        if newvalues:
            self.message += ' * Some lookup values are not found and will be added to the possible list of values:\n\n'
            self.message += "   || '''field''' || '''New values''' ||\n"
            for field in sorted(newvalues):
                value = newvalues[field]
                self.message += u"   || %s || %s ||\n" % (to_unicode(field.capitalize()), u', '.join(value))

    def process_new_users(self, newusers):
        self.message += u' * Some user names do not exist in the system: %s. Make sure that they are valid users.\n' % (u', '.join(newusers))

    def end_process(self, numrows):
        notmodifiedcount = numrows - len(self.added) - len(self.modified)
        self.message = 'Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the \'\'\'Execute Import\'\'\' button.\n' + ' * ' + str(numrows) + ' tickets will be imported (' + str(len(self.added)) + ' added, ' + str(len(self.modified)) + ' modified, ' + str(notmodifiedcount) + ' unchanged).\n' + self.message
        self.data['message'] = Markup(self.styles) + "\n" + \
                               self.format_to_html(self.message)

        return 'import_preview.html', self.data
