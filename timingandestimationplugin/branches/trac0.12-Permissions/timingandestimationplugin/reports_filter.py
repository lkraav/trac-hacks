from trac.web.api import ITemplateStreamFilter
from trac.core import *
from genshi.core import *
from genshi.builder import tag
from trac.perm import PermissionError
try: 
    set 
except NameError: 
    from sets import Set as set     # Python 2.3 fallback 

from genshi.filters.transform import Transformer
import re
import dbhelper

from trac.ticket.report import ReportModule
from trac.util.datefmt import format_datetime, format_time
import csv
from trac.web.api import RequestDone
from trac.web.chrome import add_script
from trac.web.api import IRequestFilter

class ReportsFilter(Component):
    """This component Removed rows from the report that require the 
       management screen to supply values"""
    implements(IRequestFilter)
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'report_list.html':
            add_script(req, "billing/report_filter.js")
        return (template, data, content_type)

# This can go away once they fix http://genshi.edgewall.org/ticket/136
# At that point we should use Transformer.filter
# THIS IS STILL SOLVING PROBLEMS WELL AFTER THAT TICKET HAS BEEN CLOSED - A new ticket #290 [1000] has fixed the bug, but is
# not the trac default yet
# Without this (using the default filter) I was getting omitted closing tags for some tags (Based on whitespace afaict)
class FilterTransformation(object):
    """Apply a normal stream filter to the selection. The filter is called once
    for each contiguous block of marked events."""

    def __init__(self, filter):
        """Create the transform.

        :param filter: The stream filter to apply.
        """
        self.filter = filter

    def __call__(self, stream):
        """Apply the transform filter to the marked stream.

        :param stream: The marked event stream to filter
        """
        def flush(queue):
            if queue:
                for event in self.filter(queue):
                    yield event
                del queue[:]

        queue = []
        for mark, event in stream:
            if mark:
                queue.append(event)
            else:
                for e in flush(queue):
                    yield None,e
                yield None,event
        for event in flush(queue):
            yield None,event                

billing_report_regex = re.compile("\{(?P<reportid>\d*)\}")
def report_id_from_text(text):
    m = billing_report_regex.match(text)
    if m:
        return int(m.groupdict()["reportid"])

def get_billing_reports(comp):
    billing_reports = set()
    rows = dbhelper.get_all(comp.env, "SELECT id FROM custom_report")[1]
    if rows:
        billing_reports = set([x[0] for x in rows])
    return billing_reports

class ReportScreenFilter(Component):
    """Hides TandE reports even when you just go to the url"""
    implements(ITemplateStreamFilter)
    def __init__(self):
        self.billing_reports = get_billing_reports(self)
        self.log.debug('ReportScreenFilter: self.billing_reports= %r' % self.billing_reports)

    def filter_stream(self, req, method, filename, stream, data):
        if not filename in ('report_view.html', 'report_list.html'):
            return stream
        reportid = [None]

        def idhelper(strm):
            header = strm[0][1]
            if not reportid[0]:
                self.log.debug("ReportScreenFilter: helper: %s %s %s"%(strm,header,report_id_from_text(header)))
                reportid[0] = report_id_from_text(header)
            for kind, data, pos in strm:
                yield kind, data, pos       
                
        def permhelper(strm):
            id = reportid[0]
            self.log.debug("ReportScreenFilter: id:%s, in bill: %s   has perm:%s" % (id, id in self.billing_reports, req.perm.has_permission("TIME_VIEW")))
            if id and id in self.billing_reports and not req.perm.has_permission("TIME_VIEW"):
                self.log.debug("ReportScreenFilter: No time view, prevent render")
                msg = "YOU MUST HAVE TIME_VIEW PERMSSIONS TO VIEW THIS REPORT"
                for kind, data, pos in tag.span(msg).generate():
                    yield kind, data, pos
            else:
                for kind, data, pos in strm:
                    yield kind, data, pos

        self.log.debug("ReportScreenFilter: About to begin filtering of billing reports without permissions")
        stream = stream | Transformer('//div[@id="content"]/h1/text()').apply(FilterTransformation(idhelper))
        stream = stream | Transformer('//div[@id="content"]').apply(FilterTransformation(permhelper))
        return stream

## ENFORCE PERMISSIONS ON report exports

billing_report_fname_regex = re.compile("report_(?P<reportid>\d*)")
def report_id_from_filename(text):
    if text:
        m = billing_report_fname_regex.match(text)
        if m:
            return int(m.groupdict()["reportid"])
    return -1;

unwrapped_send_csv = ReportModule._send_csv
def _send_csv(self, req, cols, rows, sep=',', mimetype='text/plain',
              filename=None):
    self.env.log.debug("T&E: In Wrapped _send_csv")
    id = report_id_from_filename(filename)
    reports = get_billing_reports(self)
    if id in reports and not req.perm.has_permission("TIME_VIEW"):
        raise PermissionError("You must have TIME_VIEW permission in order to view this report")
    unwrapped_send_csv(self, req, cols, rows, sep, mimetype, filename)
    
ReportModule._send_csv = _send_csv
