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
from collections import namedtuple
from pkg_resources import resource_filename
from trac.env import Component, implements
from trac.config import BoolOption, Option
from trac.perm import IPermissionRequestor
from trac.admin import IAdminPanelProvider
from trac.util.translation import _
from trac.web.chrome import add_warning, ITemplateProvider
from trac.wiki.model import WikiPage


_footer = namedtuple('Footer', 'value label')
footerlst = [_footer('', 'No footer'),
             _footer('[page] / [topage]', '[page] / [topage]'),
             _footer('{pagename}  -  [page] / [topage]', '<Wiki page name>  -  [page] / [topage]'),]


def prepare_data_dict(self, req):
    _pp = namedtuple('PageProp', 'value label')

    stylelst = [_pp('', 'Trac default')]
    with self.env.db_query as db:
        for row in db("SELECT DISTINCT name FROM wiki WHERE name LIKE 'WikiPrint/Styles/%'"):
            stylelst.append(_pp(row[0], row[0].split('/')[-1]))

    return {'pagesizes': [_pp('A3', 'A3 (297 x 420 mm)'),
                          _pp('A4', 'A4 (210 x 297 mm)'),
                          _pp('A5', 'A5 (148 x 210 mm)'),
                          _pp('B4', 'B4 (250 x 353 mm)'),
                          _pp('B5', 'B5 (176 x 250 mm)'),
                          _pp('B6', 'B6 (125 x 176 mm)'),
                          _pp('Folio', 'Folio (210 x 330 mm)'),
                          _pp('Legal', 'Legal (215.9 x 355.6 mm)'),
                          _pp('Letter', 'Letter (215.9 x 279.4 mm)')],
            'footerlst': footerlst,
            'pagesize': req.args.get('pagesize') or self.pagesize,
            'pdftitle': req.args.get('pdftitle') or self.pdftitle,
            'footertext': req.args.get('footertext') or self.footertext,
            'stylepage': req.args.get('stylepage') or self.stylepage,
            'stylelst': stylelst,
            'coverpage': req.args.get('coverpage') or self.coverpage,
            'toc': req.args.get('toc', False) if 'coverpage' in req.args else self.toc,
            }


pagesize = Option('wikiprint', 'pagesize', 'A4',
                  'Page size of PDF. Can be one of {{{A3, A4, A5, B4, B5, B6, Folio, Legal, Letter}}}')
pdftitle = Option('wikiprint', 'title', '', 'Title of PDF. Part of the document properties. If left '
                                            'empty the name of the wikipage will be used.')
footertext = Option('wikiprint', 'footertext', '[page] / [topage]',
                    'Footer text for PDF.[[BR]][[BR]]Note that there is a predefined list of footers used by '
                    'the administration page. Any configured footer not in the list will be overwritten when '
                    'saving parameters. When left empty no footer is added to the PDF. Currently defined '
                    'footers:\n'
                    '* {{{[page] / [topage]}}}\n'
                    '* {{{{pagename}  -  [page] / [topage]}}}\n')
stylepage = Option('wikiprint', 'stylepage', '',
                   'Wiki page holding CSS styles to apply when creating PDF files. If empty the '
                   'Trac default styles will be used.[[BR]][[BR]]'
                   'The style page must be created at {{{WikiPrint/Styles/<StylePage>}}}.')
toc = BoolOption('wikiprint', 'toc', 'enabled', "Whether to add a table of content when creating a PDF book.\n"
                                                "* {{{enabled}}}: add the table of content\n"
                                                "* {{{disabled}}}: don't add a table of content")
coverpage = Option('wikiprint', 'coverpage', '', 'Wiki page to be used as a cover when creating a PDF book. '
                                                 'Leave empty when no cover page should be added.')

class WikiPrintAdmin(Component):
    """Configure PDF page default parameters.

    === Configuration
    The parameters configured on this page are written to ''trac.ini''.
    Here's a description of the relevant section.
    [[TracIni(wikiprint)]]
    """
    implements(IAdminPanelProvider, IPermissionRequestor, ITemplateProvider)

    pagesize = pagesize
    pdftitle = pdftitle
    footertext = footertext
    stylepage = stylepage
    coverpage = coverpage
    toc = toc

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['WIKIPRINT_ADMIN'
        ]

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'WIKIPRINT_ADMIN' in req.perm:
            yield ('wikiprint', 'Wikiprint', 'pdfparameters', 'Page Parameters')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('WIKIPRINT_ADMIN')

        if req.method == 'POST' and req.args.get('save'):
            covpage = req.args.get('coverpage')
            if covpage:
                wpage = WikiPage(self.env, covpage)

            if covpage and not wpage.exists:
                add_warning(req, _("The given cover page does not exist."))
            else:
                self.config.set('wikiprint', 'pagesize', req.args.get('pagesize'))
                self.config.set('wikiprint', 'title', req.args.get('pdftitle'))
                self.config.set('wikiprint', 'footertext', req.args.get('footertext'))
                self.config.set('wikiprint', 'stylepage', req.args.get('stylepage'))
                self.config.set('wikiprint', 'coverpage', req.args.get('coverpage'))
                if req.args.get('toc'):
                    self.config.set('wikiprint', 'toc', 'enabled')
                else:
                    self.config.set('wikiprint', 'toc', '')
                self.config.save()

        data = prepare_data_dict(self, req)
        return 'wikiprint_admin_parameters.html', data

    # ITemplateProvider methods

    def get_templates_dirs(self):
        """Return the path of the directory containing the provided templates."""
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('wikiprint', resource_filename(__name__, 'htdocs'))]
