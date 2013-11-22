"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from trac.admin.api import IAdminPanelProvider
from trac.core import Component, ExtensionPoint, TracError, implements
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider, add_script
from trac.wiki.api import WikiSystem

from api import IWikiToPdfFormat


class WikiToPdfAdmin(Component):
    """A plugin allowing the export of multiple wiki pages in a single file."""

    formats = ExtensionPoint(IWikiToPdfFormat)

    implements(IAdminPanelProvider, ITemplateProvider)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('wikitopdf', resource_filename(__name__, 'htdocs'))]

    # IAdminPanelsProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('WIKI_ADMIN'):
            yield ('general', _('General'), 'wikitopdf', _('WikiToPdf'))

    def render_admin_panel(self, req, cat, page, path_info):
        allpages = list(WikiSystem(self.env).get_pages())
        rightpages = req.session.get('wikitopdf_rightpages', '')
        rightpages = filter(None, rightpages.split(','))

        formats = {}
        for provider in self.formats:
            for format, name in provider.wikitopdf_formats(req):
                formats[format] = {
                    'name': name,
                    'provider': provider,
                }
        
        if req.method == 'POST':
            rightpages = req.args.get('rightpages_all')
            title = req.args.get('title') or self.env.project_name
            subject = req.args.get('subject')
            date = req.args.get('date')
            version = req.args.get('version')
            format = req.args.get('format')

            req.session['wikitopdf_rightpages'] = rightpages
            rightpages = rightpages.split(',')

            if not format or format not in formats:
                raise TracError('Bad format given for WikiToPdf output.')

            pdfbookname = title
            pdfbookname = pdfbookname.replace(' ', '')
            pdfbookname = pdfbookname.replace(':', '')
            pdfbookname = pdfbookname.replace(',', '') 
            
            return formats[format]['provider'].process_wikitopdf(req, format, title, subject, rightpages, date, version, pdfbookname)
            
        data = {
            'allpages': allpages,
            'leftpages': sorted(x for x in allpages if x not in rightpages),
            'rightpages': rightpages,
            'formats': formats,
        }

        add_script(req, 'wikitopdf/js/admin_wikitopdf.js') 

        return 'admin_wikitopdf.html', {'wikitopdf': data}
