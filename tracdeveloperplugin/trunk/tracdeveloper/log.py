# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018 Ryan Ollos
# Copyright (C) 2012-2013 Olemis Lang
# Copyright (C) 2008-2009 Noah Kantrowitz
# Copyright (C) 2008 Christoper Lenz
# Copyright (C) 2007-2008 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import logging

from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import Chrome, add_script, add_script_data


class TracDeveloperHandler(logging.Handler):
    """A custom logging handler to implement the TracDeveloper log console."""

    def __init__(self):
        super(TracDeveloperHandler, self).__init__()
        self.buf = []

    def emit(self, record):
        self.buf.append(record)


class DeveloperLogModule(Component):
    """A plugin to display the Trac log."""

    implements(IRequestFilter)

    def __init__(self):
        self.log_handler = TracDeveloperHandler()
        self.log_handler.setFormatter(self.log.handlers[0].formatter)
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
        if hasattr(req, '_tracdeveloper_hdlr'):
            add_script(req, 'developer/js/log.js')
            first_time = 0
            if req._tracdeveloper_hdlr.buf:
                first_time = req._tracdeveloper_hdlr.buf[0].created
            add_script_data(req, log_data=[
                (int((r.created - first_time) * 1000), r.module,
                 r.levelname, r.getMessage())
                for r in req._tracdeveloper_hdlr.buf
            ])
            req._tracdeveloper_hdlr.formatter = None
            del req._tracdeveloper_hdlr.buf[:]
            self.log.removeHandler(req._tracdeveloper_hdlr)
            del req._tracdeveloper_hdlr
        return template, data, content_type
