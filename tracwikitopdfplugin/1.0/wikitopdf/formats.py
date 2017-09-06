"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

import os
import shutil
import tempfile

from trac.core import Component, implements
from trac.web.api import RequestDone
from trac.wiki.model import WikiPage

from api import IWikiToPdfFormat
from wikitopdf import wiki_to_pdf, html_to_pdf


class WikiToPdfOutput(Component):
    """Output wiki pages as a PDF/PS document using HTMLDOC."""

    implements(IWikiToPdfFormat)

    def wikitopdf_formats(self, req):
        yield 'pdf', 'PDF'
        yield 'ps', 'PS'
        yield 'html', 'HTML'

    def process_wikitopdf(self, req, format, title, subject, pages, version,
                          date, pdfname):

        tmp_dir = tempfile.mkdtemp(prefix='tracwikitopdf-')

        # Dump all pages to HTML files
        files = [self._page_to_file('', req, tmp_dir, p) for p in pages]

        # Setup the title and license pages
        title_template = self.env.config.get('wikitopdf', 'pathtocover')
        if not title_template:
            title_template = self.env.config.get('wikitopdf', 'titlefile')
            if title_template:
                title_template += '/cover.html'
        titlefile = title_template and \
                    self.get_titlepage(title_template, tmp_dir, title, subject,
                                       date, version) or None

        # Prepare html doc arguments
        codepage = self.env.config.get('trac', 'default_charset', 'utf-8')

        oformat = {'pdf': 'pdf14', 'ps': 'ps2', 'html': 'html'}[format]
        htmldoc_args = {'book': '', 'format': oformat, 'charset': codepage}

        if titlefile:
            htmldoc_args['titlefile'] = titlefile
        else:
            htmldoc_args['no-title'] = ''

        htmldoc_args.update(dict(self.env.config.options('wikitopdf-admin')))

        # render
        out = html_to_pdf(self.env, tmp_dir, htmldoc_args, files, codepage)

        # Send the output
        req.send_response(200)
        req.send_header('Content-Type', {'pdf': 'application/pdf',
                                         'ps': 'application/postscript',
                                         'html': 'text/html'}[format])
        req.send_header('Content-Disposition',
                        'attachment; filename=' + pdfname +
                        {'pdf': '.pdf', 'ps': '.ps', 'html': '.html'}[format])
        req.send_header('Content-Length', len(out))
        req.end_headers()
        req.write(out)

        # Clean up
        shutil.rmtree(tmp_dir)
        raise RequestDone

    def _page_to_file(self, header, req, tmp_dir, pagename):
        """Slight modification of some code from Alec's PageToPdf plugin."""

        # htmldoc doesn't support utf-8, we need to use some other input
        # encoding
        codepage = self.env.config.get('trac', 'default_charset',
                                       'iso-8859-1')

        page = WikiPage(self.env, pagename)
        pdf = wiki_to_pdf(page.text, self.env, req, tmp_dir, codepage)

        hfile, hfilename = tempfile.mkstemp('wikitopdf', dir=tmp_dir)
        self.log.debug("WikiToPdf => Writting %s to %s using encoding %s",
                       pagename, hfilename, codepage)
        os.write(hfile, pdf)
        os.close(hfile)
        return hfilename

    def get_titlepage(self, template_path, tmp_dir, title, subject, version,
                      date):

        with open(template_path, 'r') as file_page:
            string_page = file_page.read()

        hfile, hfilename = tempfile.mkstemp('wikitopdf', dir=tmp_dir)
        string_page = string_page.replace('#TITLE#', title)
        string_page = string_page.replace('#SUBJECT#', subject)
        string_page = string_page.replace('#VERSION#', version)
        string_page = string_page.replace('#DATE#', date)

        title_template = self.env.config.get('wikitopdf', 'pathtocover')
        if title_template == '':
            title_template = self.env.config.get('wikitopdf', 'titlefile')
        string_page = string_page.replace('#PATHTOCOVER#', title_template)

        os.write(hfile, string_page)
        os.close(hfile)

        return hfilename
