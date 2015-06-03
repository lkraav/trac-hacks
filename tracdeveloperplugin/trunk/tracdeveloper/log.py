# Created by Noah Kantrowitz on 2008-09-27.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import logging

from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import Chrome, add_script
from genshi.core import END
from genshi.builder import tag


class TracDeveloperHandler(logging.Handler):
    """A custom logging handler to implement the TracDeveloper log console."""

    def __init__(self):
        logging.Handler.__init__(self)
        self.buf = []

    def emit(self, record):
        self.buf.append(record)


class DeveloperLogModule(Component):
    """A plugin to display the Trac log."""

    implements(IRequestFilter, ITemplateStreamFilter)

    def __init__(self):
        self.log_handler = TracDeveloperHandler()
        self.log_handler.setFormatter(self.log._trac_handler.formatter)
        self.log.addHandler(self.log_handler)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if not isinstance(handler, Chrome) and \
                req.get_header('X-Requested-With') != 'XMLHttpRequest' and \
                'TRAC_DEVELOP' in req.perm:
            if self.log_handler not in self.log.handlers:
                self.log.addHandler(self.log_handler)
            req._tracdeveloper_hdlr = self.log_handler
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if not hasattr(req, '_tracdeveloper_hdlr'):
            return stream

        if method != 'xhtml':
            req._tracdeveloper_hdlr.formatter = None
            del req._tracdeveloper_hdlr.buf[:]
            self.log.removeHandler(req._tracdeveloper_hdlr)
            del req._tracdeveloper_hdlr
            return stream

        add_script(req, 'developer/js/log.js')

        def fn(stream):
            for kind, data, pos in stream:
                if kind is END and data.localname == 'body':
                    first_time = req._tracdeveloper_hdlr.buf \
                                 and req._tracdeveloper_hdlr.buf[0].created

                    elm = tag.div(tag.table(tag.thead(tag.tr(
                        tag.th('Time'),
                        tag.th('Module'),
                        tag.th('Level'),
                        tag.th('Message'),
                    )), class_='listing')([
                        tag.tr(
                            tag.td(int((r.created - first_time) * 1000)),
                            tag.td(r.module),
                            tag.td(r.levelname),
                            tag.td(r.getMessage()),
                            class_=(i%2 and 'even' or 'odd'),
                        )
                        for i, r in enumerate(req._tracdeveloper_hdlr.buf)
                    ]), id='tracdeveloper-log')
                    for evt in elm.generate():
                        yield evt
                    del elm
                    req._tracdeveloper_hdlr.formatter = None
                    del req._tracdeveloper_hdlr.buf[:]
                    self.log.removeHandler(req._tracdeveloper_hdlr)
                    del req._tracdeveloper_hdlr
                yield kind, data, pos
        return stream | fn


