# -*- coding: utf-8 -*-
#
# Copyright (C) 2004-2015 Edgewall Software
# Copyright (C) 2015 Sergio Talens-Oliag
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Sergio Talens-Oliag <sto@iti.es>
# Adapted from ManPageRendererPlugin by Piers O'Hanlon <p.ohanlon@cs.ucl.ac.uk>

"""Trac Renderer for asciidoc pages using Asciidoctor"""

from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer, content_to_unicode
from trac.util import NaivePopen
from trac.web.chrome import add_stylesheet

class AsciidocRenderer(Component):
    """Renders Asciidoc text as HTML using Asciidoctor"""
    implements(IHTMLPreviewRenderer)

    def get_quality_ratio(self, mimetype):
        if mimetype in ['text/asciidoc','text/x-asciidoc']:
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, rev=None):
        req = context.req
        cmdline = self.config.get('mimeviewer', 'asciidoctor_path')
        if len(cmdline) == 0:
            cmdline = '/usr/bin/asciidoctor'
        self.env.log.debug("asciidoctor got command line: %s" % cmdline)
        cmdline += ' -s -Ssecure -'
        self.env.log.debug("asciidoctor command line: %s" % cmdline)
        content = content_to_unicode(self.env, content, mimetype)
        cont=content.encode('utf-8')
        np = NaivePopen(cmdline, cont, capturestderr=1)
        if np.errorlevel or np.err:
            err = 'Running (%s) failed: %s, %s.' % (cmdline, np.errorlevel, np.err)
            raise Exception, err
        add_stylesheet(req, 'tracasciidoctor/css/asciidoc.css')
        return np.out
