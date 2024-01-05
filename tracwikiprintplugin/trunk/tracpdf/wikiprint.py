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
import base64
import re
from pdfkit import from_url
from trac.env import Component, implements
from trac.mimeview.api import IContentConverter
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import add_ctxtnav, add_stylesheet, add_warning, web_context
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage
from trac.wiki.parser import WikiParser

from .admin import coverpage, footertext, pagesize, prepare_data_dict, pdftitle, stylepage, toc
from .pdfbook import parse_makro_content
from .util import get_trac_css, writeResponse


class WikiToPdf(Component):
    """Create a PDF page or a book from a wiki page.

    ==== Configuration
    {{{wkhtmltopdf}}} must be installed and in your path. Get
    it from https://wkhtmltopdf.org/

    [[TracIni(wikiprint)]]
    Configuration can be done on the admin page.
    """

    implements(IContentConverter, IRequestHandler)

    pagesize = pagesize
    pdftitle = pdftitle
    footertext = footertext
    stylepage = stylepage
    coverpage = coverpage
    toc = toc

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/wikiprintparams(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['page'] = match.group(1)
            return True
        # This is a call from the PdfBook makro
        match = re.match(r'/wikiprintpdfbook(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['page'] = match.group(1)
                req.args['createbook'] = True
            return True

    def pagename_version_from_req(self, req):
        """Parse a request to get the name and version of the wiki page.

        :param req: Request object
        return tuple with pagename, version

        'Note that version may be None.
        """
        pagename = req.args.get('page')
        version = None
        if req.args.get('version'):  # Allow version to be empty
            version = req.args.getint('version')
        return pagename, version

    def _get_pdf_book_config(self, req):
        """Get the PDF book configuration from the wiki page holding the PdfBook
        makro.

        :param req: Request object holding wiki page name
        :return dict with:
                {'coverpage': name of wiki page to use as cover,
                 'toc': True|False - wether to add a table of contents,
                 'pages': list of wiki page names
                }
        Note that only one PdfBook makro on the page is supported.
        """
        pagename, version = self.pagename_version_from_req(req)
        page = WikiPage(self.env, pagename, version)

        req.perm(page.resource).require('WIKI_VIEW')

        text = page.text.splitlines()
        conf = []
        in_macro = False
        for line in text:
            if not in_macro:
                block_start_match = None
                if WikiParser.ENDBLOCK not in line:
                    block_start_match = WikiParser._startblock_re.match(line)
                # Handle start of a new block
                if block_start_match:
                    if len(block_start_match.groups()) == 2 and block_start_match.group(2) == 'PdfBook':
                        in_macro = True
                    continue
            else:
                if WikiParser.ENDBLOCK not in line:
                    conf.append(line)
                else:
                    break
        return parse_makro_content('\n'.join(conf))

    def process_request(self, req):
        """Handle the Pdf parameters page.

        After the user adjusted settings like cover page or page size he is
        redirected to the wiki page he came from with format='xxx' arg
        so the download of the PDF will happen. Additional args specify
        the chosen settings and control which kind of PDF will be created."""

        pagename, version = self.pagename_version_from_req(req)

        if req.args.get('download'):
            # Download button on PDF settings page brought us here.
            covpage = req.args.get('coverpage')
            if covpage:
                page = WikiPage(self.env, covpage)

            if covpage and not page.exists:
                add_warning(req, _("The given cover page does not exist."))
            else:
                # User adjusted settings. Now call "Download in other format" again.
                pdf_format = 'pdfbook' if req.args.get('coverpage') else 'pdfpage'
                req.redirect(req.href('wiki', pagename, version=version,
                                      format=pdf_format,
                                      pdftitle=req.args.get('pdftitle'),
                                      pagesize=req.args.get('pagesize'),
                                      footertext=req.args.get('footertext'),
                                      stylepage=req.args.get('stylepage'),
                                      coverpage=req.args.get('coverpage'),
                                      toc=req.args.get('toc'),
                                      download=1,
                                      pages=req.args.getlist('pages')))

        # This overrides global settings from the admin page with adjustments
        # by the user.
        data = prepare_data_dict(self, req)

        if req.args.get('createbook'):
            # We are coming from the macro holding a list of pages to use for the PDF.
            # Update settings with config from macro
            book = self._get_pdf_book_config(req)
            data.update({'coverpage': req.args.get('coverpage') or book['coverpage'],
                         'toc': book['toc']})
        else:
            book = {}
        pages = book['pages'] if 'pages' in book else []

        data.update({'pagename': pagename,
                     'pages': pages,
                     # 'pdfbook' is set when we are coming from 'convert_content()'
                     # 'coverpage' is set when we have a cover page error on the settings page
                     # and reload the page.  In that case the 'pdfbook' info is not available.
                     'pdfbook': req.args.get('pdfbook')})  # or 'coverpage' in req.args})

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
        yield 'pdfbook', _("PDF Book"), 'pdf', 'text/x-trac-wiki', 'application/pdf', 8

    def convert_content(self, req, mimetype, content, key):
        """Convert the given content from mimetype to the output MIME type
        represented by key. Returns a tuple in the form (content,
        output_mime_type) or None if conversion is not possible.
        """
        # Permission handling is done when creating the HTML data
        pagename, version = self.pagename_version_from_req(req)
        if not pagename:
            return None

        # Redirect to settings page. After parameters are chosen the method will be called
        # again but with format='pdfpage'
        if key == 'pdfpagecustom':
            req.redirect(req.href('wikiprintparams', pagename, version=version))
        elif key == 'pdfbook' and not req.args.get('download'):
            # When 'download' is set we are coming from the settings page
            req.redirect(req.href('wikiprintparams', pagename, version=version, pdfbook=1))

        pdfoptions = self.prepare_pdf_options(req, pagename)

        # Wiki urls will be handled using WikiToHtml component
        cover_page = req.args.get('coverpage')
        stylepage = req.args.get('stylepage')
        # If set the known table of content makros are removed from the wiki page
        filterwiki = 1 if key == 'pdfbook' else None

        cover_url = req.abs_href('wikiprint', cover_page, stylepage=stylepage) if cover_page else None

        page_lst = []

        if req.args.get('toc'):
            page_lst.append('toc')

        # 'pages' are available when we create a PDF book from the makro PdfBook. The
        # makro holds a list of pages specified by the user.
        pages = req.args.getlist('pages')
        if pages:
           for page in pages:
               page_lst.append(req.abs_href('wikiprint', page, version=version,
                                     stylepage=stylepage, filterwiki=filterwiki))
        else:
            page_lst.append(req.abs_href('wikiprint', pagename, version=version,
                                     stylepage=stylepage, filterwiki=filterwiki))
        # Now call pdfkit without a file name so it returns the PDF.
        pdf_page = from_url(page_lst, False, options=pdfoptions, cover=cover_url, verbose=True)

        return pdf_page, 'application/pdf'

    def prepare_pdf_options(self, req, pagename):
        """Prepare the global wkhtmltopdf options used when generating a PDF page or book.

        :param req: Request object which may hold page settings
        :param pagename: name of the current wiki page
        :return: dict with wkhtmltopdf global options
        """
        options = {
            'page-size': req.args.get('pagesize') or self.pagesize,
            'encoding': "UTF-8",
            'outline': None,
            'title': req.args.get('pdftitle') or self.pdftitle or pagename,
        }

        for name in ('trac_auth', 'trac_session'):
            if name in req.incookie:
                options['cookie'] = [(name, req.incookie[name].value)]
                break

        authorization = (req.get_header('Authorization') or '').split()
        if len(authorization) == 2 and authorization[0].lower() == 'basic':
            try:
                creds = base64.b64decode(authorization[1])
            except:
                pass
            else:
                creds = creds.split(b':', 1)
                if len(creds) == 2:
                    options['username'] = to_unicode(creds[0])
                    options['password'] = to_unicode(creds[1])

        self._add_footer(options, pagename, req.args.get('footertext'))
        return options

    def _add_footer(self, options, pagename, footertext=None):
        """Add footer information to the global wkhtmltopdf options.

        :param options: dict with global options
        :param pagename: the name of the current wiki page
        :param footertext: footer text specified by the user
        :return: None

        The given options dict is updated in place.
        """
        if not self.footertext and not footertext:
            return

        footertext = footertext or self.footertext
        if '{pagename}' in footertext:
            options.update({'footer-center': footertext.format(pagename=pagename)})
        else:
            options.update({'footer-center': footertext})
        options.update({'footer-line': None,
                        'footer-font-size': 10})


FILTER_WIKI_RES = [
    re.compile(r'\[\[TracGuideToc\]\]'),
    re.compile(r'\[\[PageOutline(\(.*\))?\]\]'),
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
        yield 'htmlpage', _("Printable HTML"), 'html', 'text/x-trac-wiki', 'text/html; charset=utf-8', 8

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
        page = WikiPage(self.env, stylepage)
        if page.exists:
            return page.text

        # Get standard Trac styles
        trac_css = get_trac_css(self.env, 'trac.css')
        wiki_css = get_trac_css(self.env, 'wiki.css')

        return u"%s\n%s" % (trac_css, wiki_css)

    def create_html_page(self, req, wikitext):
        pagename = req.path_info  # This is something like /wiki/WikiStart
        pagename = pagename.split('/')[-1]
        stylepage = req.args.get('stylepage', 'WikiPrint/StylesHtmlPage')

        # Filter out macros e.g. [[TracGuideToc]] or [[PageOutline]]. Usually done
        # when creating a PDF book.
        if req.args.get('filterwiki'):
            for rec in FILTER_WIKI_RES:
                wikitext = rec.sub('', wikitext)

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
