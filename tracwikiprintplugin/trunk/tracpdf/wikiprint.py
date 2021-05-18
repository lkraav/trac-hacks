# -*- coding: utf-8 -*-
# Copyright (c) 2021 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import re
from collections import namedtuple
from pdfkit import from_url
from trac.env import Component, implements
from trac.config import Option
from trac.mimeview.api import IContentConverter
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import add_ctxtnav, add_stylesheet, web_context
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage

from .admin import prepare_data_dict
from .util import get_trac_css, writeResponse


FIX_HTML_RES = [
    # removing empty <tr> reportlab/platypus/tables.py chokes on, see #14012
    re.compile(r'<tr.*>\s*</tr>')
]

default_page_tmpl =u"""<!DOCTYPE html>
<html>
  <head>
      <title>
      </title>
      <style>
        {style}
      </style>
  </head>
  <body>
    {wiki}
  </body>
</html>
"""


class WikiToPdf(Component):
    """Create PDF page from a wiki page.

    {{{wkhtmltopdf}}} must be installed and in your path. Get
    it from https://wkhtmltopdf.org/

    Go to the admin page for customization.
    """

    implements(IContentConverter, IRequestHandler)

    pagesize = Option('wikiprint', 'pagesize')
    pdftitle = Option('wikiprint', 'title')
    footertext = Option('wikiprint', 'footertext')
    stylepage = Option('wikiprint', 'stylepage')

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/wikiprintparams(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['page'] = match.group(1)
            return True

    def process_request(self, req):
        """Pdf parameters page."""
        pagename = req.args.get('page')
        version = None
        if req.args.get('version'):  # Allow version to be empty
            version = req.args.getint('version')

        if req.args.get('download'):
            req.redirect(req.href('wiki', pagename, version=version,
                                  format='pdfpage',
                                  pdftitle=req.args.get('pdftitle'),
                                  pagesize=req.args.get('pagesize'),
                                  footertext=req.args.get('footertext'),
                                  stylepage=req.args.get('stylepage')))
        data = prepare_data_dict(self, req)

        data.update({'pagename': pagename})

        add_stylesheet(req, 'wikiprint/css/wikiprint.css')
        add_ctxtnav(req, _("Back to %s" % pagename), req.href('wiki', pagename, version=version))
        return 'wikiprint_parameters.html', data

    # IContentConverter methods

    def get_supported_conversions(self):
        """Return an iterable of tuples in the form (key, name, extension,
        in_mimetype, out_mimetype, quality) representing the MIME conversions
        supported and
        the quality ratio of the conversion in the range 0 to 9, where 0 means
        no support and 9 means "perfect" support. eg. ('latex', 'LaTeX', 'tex',
        'text/x-trac-wiki', 'text/plain', 8)"""
        yield 'pdfpage', _("PDF Page"), 'pdf', 'text/x-trac-wiki', 'application/pdf', 8
        yield 'pdfpagecustom', _("PDF Page (custom settings)"), 'pdf', 'text/x-trac-wiki', 'application/pdf', 8

    def convert_content(self, req, mimetype, content, key):
        """Convert the given content from mimetype to the output MIME type
        represented by key. Returns a tuple in the form (content,
        output_mime_type) or None if conversion is not possible.
        """
        pagename = req.args.get('page')
        if not pagename:
            return None
        version = None
        if req.args.get('version'):  # Allow version to be empty
            version = req.args.getint('version')

        # Redirect to settings page. After parameters are chosen the method will be called
        # again but with format='pdfpage'
        if key == 'pdfpagecustom':
            req.redirect(req.href('wikiprintparams', pagename, version=version))

        options = {
            'page-size': req.args.get('pagesize') or self.pagesize,
            'encoding': "UTF-8",
            'outline': None,
            'title':  req.args.get('pdftitle') or self.pdftitle or pagename,
            'cookie': [
                ('trac_auth', req.incookie['trac_auth'].value),
            ]
        }
        self._add_footer(options, pagename, req.args.get('footertext'))

        # This will be handled by the WikiToHtml component
        url = req.abs_href('wikiprint', pagename, version=version, stylepage=req.args.get('stylepage'))
        pdf_page = from_url([url], False, options=options)

        return pdf_page, 'application/pdf'

    def _add_footer(self, options, pagename, footertext=None):
        if not self.footertext and not footertext:
            return

        footertext = footertext or self.footertext
        if '{pagename}' in footertext:
            options.update({'footer-center': footertext.format(pagename=pagename)})
        else:
            options.update({'footer-center': footertext})
        options.update({'footer-line': None,
                        'footer-font-size': 10})


class WikiToHtml(Component):
    """Create a HTML page from a wiki page. The page only holds the wiki content
    for easy printing."""

    implements(IContentConverter, IRequestHandler)

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/wikiprint(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['page'] = match.group(1)
            return True

    def process_request(self, req):
        """Create a HTML page from a wiki page omitting the Trac chrome."""
        pagename = req.args.get('page')
        # We allow page versions
        version = req.args.get('version', None)
        page = WikiPage(self.env, pagename, version)

        req.perm(page.resource).require('WIKI_VIEW')

        if page.exists:
            html_page = self.create_html_page(req, page.text)
        else:
            html_page = ''
        writeResponse(req, html_page, content_type='text/html; charset=utf-8')

    # IContentConverter methods

    def get_supported_conversions(self):
        """Return an iterable of tuples in the form (key, name, extension,
        in_mimetype, out_mimetype, quality), eg. ('latex', 'LaTeX', 'tex',
        'text/x-trac-wiki', 'text/plain', 8)"""
        yield 'htmlpage', _("Show Content only"), 'html', 'text/x-trac-wiki', 'text/html; charset=utf-8', 8

    def convert_content(self, req, mimetype, content, key):
        """Returns a tuple in the form (content,
        output_mime_type) or None if conversion is not possible.
        """
        pagename = req.args.get('page')
        if not pagename:
            return None
        version = None
        if req.args.get('version'):  # Allow version to be empty
            version = req.args.getint('version')

        # We don't send data for downloading here but redirect to a page only
        # showing the contents (no Trac chrome).
        req.redirect(req.href('wikiprint', pagename, version=version))

        # html_page = self.create_html_page(req, content)
        # return html_page, 'text/html; charset=utf-8'

    # Helper methods for IContentConverter

    page_tmpl = default_page_tmpl

    def _get_styles(self, stylepage):
        self.log.info('#### ###### %s' % stylepage)
        page = WikiPage(self.env, stylepage)
        if page.exists:
            self.log.info('#### ###### %s' % page.text)
            return page.text

        # Get standard Trac styles
        trac_css = get_trac_css(self.env, 'trac.css')
        wiki_css = get_trac_css(self.env, 'wiki.css')
        return "%s\n%s" % (trac_css, wiki_css)

    def create_html_page(self, req, wikitext):
        pagename = req.path_info  # This is something like /wiki/WikiStart
        pagename = pagename.split('/')[-1]
        stylepage = req.args.get('stylepage', 'WikiPrint/StylesHtmlPage')

        wiki_html = wiki_to_html(self.env, req, pagename, wikitext)
        return self.page_tmpl.format(wiki=wiki_html, style=self._get_styles(stylepage))


def wiki_to_html(env, req, pagename, wikitext):
    """Convert the given wikitext to html.

    :param env: Trac Environment object
    :param req: Request object
    :param pagename: name of the wiki page
    :param wikitext: raw eiki page content as users type it
    :return html data as a string. Note that this is a fragment, meaning no
            '<html></html>' tags, no doctype and friends.
    """
    context = web_context(req, 'wiki', pagename)
    page_html = format_to_html(env, context, wikitext)

    # Insert style information
    return to_unicode(page_html)
