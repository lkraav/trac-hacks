# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import implements, Component
from trac.mimeview.api import IHTMLPreviewRenderer
from trac.web.chrome import ITemplateProvider


class PdfRenderer(Component):
    """
    HTML renderer for PDF files.  Add application/pdf to mime_map in trac.ini
    """
    implements(IHTMLPreviewRenderer, ITemplateProvider)

    # IHTMLPreviewRenderer methods

    def get_quality_ratio(self, mimetype):
        if mimetype in ['application/pdf']:
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, rev=None):
        href = context.href
        resource = context.resource
        realm = resource.realm
        if realm == 'source':
            version = resource.version
            pdf_url = href('export', version, resource.id)
        elif realm == 'attachment':
            parent = resource.parent
            pdf_url = href(
                    'raw-attachment', parent.realm, parent.id, resource.id)
        viewer_url = href('chrome', 'pdfpreview', 'web', 'viewer.html')
        iframe = """
        <iframe style="width:100%%; height:480px" src="%s?file=%s"></iframe>
        """
        return iframe % (viewer_url, pdf_url)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('pdfpreview', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
