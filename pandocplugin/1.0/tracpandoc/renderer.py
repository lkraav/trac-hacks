# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer
from tracpandoc.any2html import Docx2Html

extensions_docx = ['.docx', '.docm', '.dotx', '.dotm']
mimetypes_docx = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
mimetypes_doc = ['application/msword']

def has_docx_extension(filename):
    for extension in extensions_docx:
        if filename.endswith(extension):
            return True
    return False

class DocxRenderer(Component):
    """HTML renderer for docx. Add application/vnd.openxmlformats-officedocument.wordprocessingml.document:docx to mime_map in trac.ini """
    implements(IHTMLPreviewRenderer)

    def __init__(self):
        self.docx2html = Docx2Html()

    # IHTMLPreviewRenderer methods

    def get_quality_ratio(self, mimetype):
        if not self.docx2html.is_available():
            return 0
        if mimetype in mimetypes_docx:
            return 8
        # svn seems to automatically add svn:mime-type=application/msword to *.docx files
        if mimetype in mimetypes_doc:
            return 1
        return 0

    def render(self, context, mimetype, content, filename=None, rev=None):
        if mimetype in mimetypes_doc and not has_docx_extension(filename):
            self.env.log.warn(filename + " cannot be rendered by DocxRenderer")
            return
        html = self.docx2html.render(content)
        return html
