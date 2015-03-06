# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Boris Savelev
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Boris Savelev <boris.savelev@gmail.com>

"""
    Trac support for DOC, PDF format
"""

import os
from subprocess import PIPE, Popen
from tempfile import mkstemp
from trac.util.text import to_unicode

from trac.core import *
from trac.config import Option
from trac.mimeview.api import IHTMLPreviewRenderer


class DocRenderer(Component):
    """Renders doc, pdf files as HTML."""
    implements(IHTMLPreviewRenderer)

    socket = Option('attachment', 'ooo_socket', '', 'socket url to OOo')

    mimetypes_doc = [
        "application/msword",
        "application/vnd.ms-word",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    mimetypes_xls = [
        "application/excel",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    mimetypes_ppt = [
         "application/powerpoint",
         "application/vnd.ms-powerpoint",
         "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ]

    def __init__(self):
        self.mime = None

    def get_quality_ratio(self, mimetype):
        if mimetype in self.mimetypes_doc:
            self.mime = 'doc'
            return 8
        elif mimetype in self.mimetypes_xls:
            self.mime = 'xls'
            return 8
        elif mimetype in self.mimetypes_ppt:
            self.mime = 'ppt'
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, rev=None):
        if hasattr(content, 'read'):
            content = content.read()
        temp = mkstemp()
        f = os.fdopen(temp[0], "w")
        tmp_filename = temp[1]
        f.write(content)
        f.close()

        cmd = ['/opt/libreoffice4.4/program/python',
               '/opt/libreoffice4.4/program/ooextract.py',
               '--connection-string=%s' % self.socket,
               '--format=%s' % self.mime,
               '--stdout',
               '%s' % tmp_filename]
        self.log.debug("Trying to render HTML preview for %s file %s "
                       "using cmd: %s", mimetype, filename, ' '.join(cmd))
        output = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        content_export = output[0]
        self.log.debug("cmd log: %s" % output[1])
        return to_unicode(content_export)
