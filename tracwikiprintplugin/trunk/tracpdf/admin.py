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
from trac.config import Option
from trac.perm import IPermissionRequestor
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider


_footer = namedtuple('Footer', 'value label')
footerlst = [_footer('', 'No footer'),
             _footer('[page] / [topage]', '[page] / [topage]'),
             _footer('{pagename}  -  [page] / [topage]', '<Wiki page name>  -  [page] / [topage]'),]


def prepare_data_dict(self, req):
    _ps = namedtuple('PageSize', 'value label')
    return {'pagesizes': [_ps('A3', 'A3 (297 x 420 mm)'),
                          _ps('A4', 'A4 (210 x 297 mm)'),
                          _ps('A5', 'A5 (148 x 210 mm)'),
                          _ps('B4', 'B4 (250 x 353 mm)'),
                          _ps('B5', 'B5 (176 x 250 mm)'),
                          _ps('B6', 'B6 (125 x 176 mm)'),
                          _ps('Folio', 'Folio (210 x 330 mm)'),
                          _ps('Legal', 'Legal (215.9 x 355.6 mm)'),
                          _ps('Letter', 'Letter (215.9 x 279.4 mm)')],
            'footerlst': footerlst,
            'pagesize': req.args.get('pagesize') or self.pagesize,
            'pdftitle': req.args.get('pdftitle') or self.pdftitle,
            'footertext': req.args.get('footertext') or self.footertext,
            }


class WikiPrintAdmin(Component):

    implements(IAdminPanelProvider, IPermissionRequestor, ITemplateProvider)

    pagesize = Option('wikiprint', 'pagesize', 'A4', 'Page size of PDF.')
    pdftitle = Option('wikiprint', 'title', '', 'Title of PDF. Part of the document properties. If left '
                                                'empty the name of the wikipage will be used.')
    footertext = Option('wikiprint', 'footertext', '[page] / [topage]',
                        'Footer text for PDF. Note that the footer must be enabled first.')

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
            self.config.set('wikiprint', 'pagesize', req.args.get('pagesize'))
            self.config.set('wikiprint', 'title', req.args.get('pdftitle'))
            self.config.set('wikiprint', 'footertext', req.args.get('footertext'))
            self.config.save()

        data = prepare_data_dict(self, req)
        return 'wikiprint_admin_parameters.html', data

    # ITemplateProvider methods

    def get_templates_dirs(self):
        """Return the path of the directory containing the provided templates."""
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('wikiprint', resource_filename(__name__, 'htdocs'))]
