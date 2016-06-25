# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer
from nbconvert import HTMLExporter
import nbformat

class JupyterNotebookRenderer(Component):
    """HTML renderer for Jupyter Notebook. Add application/x-ipynb+json:ipynb to mime_map in trac.ini"""

    implements(IHTMLPreviewRenderer)

    def __init__(self):
        pass

    # IHTMLPreviewRenderer methods

    def get_quality_ratio(self, mimetype):
        self.log.info("Jupyter: "+mimetype)
        if mimetype in ['application/x-ipynb',
                        'application/x-ipynb+json',
                       ]:
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, rev=None):
        notebook = nbformat.reads(content.read(), as_version=4)

        html_exporter = HTMLExporter()
        html_exporter.template_file = 'basic'

        (body, resources) = html_exporter.from_notebook_node(notebook)

        return body
