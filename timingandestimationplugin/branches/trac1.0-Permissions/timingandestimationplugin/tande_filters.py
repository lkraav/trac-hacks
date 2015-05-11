from trac.web.api import ITemplateStreamFilter
from trac.core import *
import genshi
from genshi.core import *
from genshi.builder import tag
from genshi.filters.transform import Transformer
from blackmagic import *
from StringIO import StringIO
import csv
from trac.mimeview.api import (IContentConverter)
from trac.resource import Resource
from trac.web.chrome import (Chrome, web_context)
from trac.util.translation import _
import re


# also in blackmagic ... not sure how to guarantee that one of them 
# will be run in time other than to do it in both places
def textOf(self, **keys):
    return self.render('text', None, **keys)
Stream.textOf = textOf


def denied_fields(comp, req):
    fields = comp.config.getlist(csection, 'fields', [])
    for field in fields:
        comp.log.debug('found : %s' % field)
        perms = comp.config.getlist(csection, '%s.permission' % field, [])
        #comp.log.debug('read permission config: %s has %s' % (field, perms))
        for (perm, denial) in [s.split(":") for s in perms]:
            perm = perm.upper()
            comp.log.debug('testing permission: %s:%s should act= %s' %
                           (field, perm, (not req.perm.has_permission(perm)
                                          or perm == "ALWAYS")))
            if (not req.perm.has_permission(perm) or perm == "ALWAYS") \
                    and denial.lower() in ["remove", "hide"]:
                label = comp.env.config.get(
                    'ticket-custom', field + '.label', field).lower().strip()
                yield (field, label)


# Basically overwriting QueryModule.export_csv = new_csv_export
class TandEFilteredQueryConversions(Component):
    implements(IContentConverter)

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('csv', _('Comma-delimited Text'), 'csv',
               'trac.ticket.Query', 'text/csv', 9)  # higher than QueryModule
        yield ('tab', _('Tab-delimited Text'), 'tsv',
               'trac.ticket.Query', 'text/tab-separated-values', 9)

    def convert_content(self, req, mimetype, query, key):
        if key == 'csv':
            return self._export_csv(req, query, mimetype='text/csv')
        elif key == 'tab':
            return self._export_csv(req, query, '\t',
                                    mimetype='text/tab-separated-values')

    # Internal methods
    def _filtered_columns(self, req, cols):
        # find the columns that should be hidden
        denied = [field for (field, label) in denied_fields(self, req)]
        return [c for c in cols if c not in denied]

    def _export_csv(self, req, query, sep=',', mimetype='text/plain'):
        self.log.debug("T&E plugin has overridden QueryModule.csv_export"
                       " so to enforce field permissions")
        # !!!    BEGIN COPIED CONTENT - from trac1.0/trac/ticket/query.py
        content = StringIO()
        content.write('\xef\xbb\xbf')   # BOM
        cols = query.get_columns()
        # !!!    T&E patch
        cols = self._filtered_columns(req, cols)
        # !!!END T&E patch
        writer = csv.writer(content, delimiter=sep, quoting=csv.QUOTE_MINIMAL)
        writer.writerow([unicode(c).encode('utf-8') for c in cols])

        context = web_context(req)
        results = query.execute(req)
        for result in results:
            ticket = Resource('ticket', result['id'])
            if 'TICKET_VIEW' in req.perm(ticket):
                values = []
                for col in cols:
                    value = result[col]
                    if col in ('cc', 'owner', 'reporter'):
                        value = Chrome(self.env).format_emails(
                            context.child(ticket), value)
                    elif col in query.time_fields:
                        value = format_datetime(value, '%Y-%m-%d %H:%M:%S',
                                                tzinfo=req.tz)
                    values.append(unicode(value).encode('utf-8'))
                writer.writerow(values)
        return (content.getvalue(), '%s;charset=utf-8' % mimetype)


class TicketFormatFilter(Component):
    """Filtering the streams to alter the base format of the ticket"""
    implements(ITemplateStreamFilter)

    def filter_stream(self, req, method, filename, stream, data):
        self.log.debug("TicketFormatFilter executing") 
        if not filename == 'ticket.html':
            self.log.debug("TicketFormatFilter not the correct template")
            return stream
        
        self.log.debug("TicketFormatFilter disabling totalhours and removing header hours")
        stream = disable_field(stream, "totalhours")
        stream = remove_header(stream, "hours")
        return stream 

class QueryColumnPermissionFilter(Component):
    """ Filtering the stream to remove """
    implements(ITemplateStreamFilter)    
    
    ## ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if not filename == "query.html":
            self.log.debug('Not a query returning')
            return stream

        def make_col_helper(field):
            def column_helper (column_stream):
                s =  Stream(column_stream)
                val = s.select('//input/@value').render()
                if val.lower() != field.lower(): #if we are the field just skip it
                    #identity stream filter
                    for kind, data, pos in s:
                        yield kind, data, pos        
            return column_helper

        for (field, label) in denied_fields(self, req):
            # remove from the list of addable 
            stream = stream | Transformer(
                '//select[@id="add_filter"]/option[@value="%s"]' % field
                ).replace(" ")

            # remove from the list of columns
            stream = stream | Transformer(
                '//fieldset[@id="columns"]/div/label'
                ).filter(make_col_helper(field))
                    
            # remove from the results table
            stream = stream | Transformer(
                '//th[@class="%s"]' % field
                ).replace(" ")
            stream = stream | Transformer(
                '//td[@class="%s"]' % field
                ).replace(" ")
            
            # remove from the filters
            stream = stream | Transformer(
                '//tr[@class="%s"]' % field
                ).replace(" ")
        return stream

commasRE = re.compile(r',\s(,\s)+', re.I)
class TimelinePermissionFilter(Component):
    """ Filtering the stream to remove fields from the timeline of changes """
    implements(ITemplateStreamFilter)
    
    ## ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if not filename == "timeline.html":
            self.log.debug('Not a timeline, returning')
            return stream
        denied = [label for (field, label) in denied_fields(self, req)]
        def helper(field_stream):
            try:
                s = Stream(field_stream)
                # without None as the second value we get str instead of unicode
                # and that causes things to break sometimes
                f = s.select('//text()').textOf(strip_markup=True).lower()
                self.log.debug('Timeline Filter: is %r in %r, skip?%r',
                               f, denied, f in denied )
                if f not in denied: #if we are the field just skip it
                #identity stream filter
                    for kind, data, pos in s:
                        yield kind, data, pos
            except Exception, e:
                self.log.exception('Timeline: Stream Filter Exception');
                raise e

        def comma_cleanup(stream):
            text = Stream(stream).textOf()
            self.log.debug( 'Timeline: Commas %r %r' , text, commasRE.sub( text, ', ' ) );
            text = commasRE.sub( ', ' , text)
            for kind, data, pos in tag(text):
                yield kind, data, pos

        stream = stream | Transformer('//dd[@class="editedticket"]/i').filter(helper)
        stream = stream | Transformer('//dd[@class="editedticket"]/text()').filter(comma_cleanup)
                    
        return stream
