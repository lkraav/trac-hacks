# -*- coding: utf-8 -*-

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.web.chrome import web_context

from tracdownloads.api import DownloadsApi


class DownloadsWebAdmin(Component):
    """
        The WebAdmin module implements downloads plugin administration.
    """
    implements(IAdminPanelProvider)

    # IAdminPageProvider

    def get_admin_panels(self, req):
        if 'DOWNLOADS_ADMIN' in req.perm:
            yield ('downloads', 'Downloads System', 'downloads', 'Downloads')
            yield ('downloads', 'Downloads System', 'architectures',
                   'Architectures')
            yield ('downloads', 'Downloads System', 'platforms', 'Platforms')
            yield ('downloads', 'Downloads System', 'types', 'Types')

    def render_admin_panel(self, req, category, page, path_info):
        # Create request context.
        context = web_context(req, 'downloads-admin')

        # Set page name to request.
        req.args['page'] = page
        if page == 'architectures':
            req.args['architecture'] = path_info
        elif page == 'platforms':
            req.args['platform'] = path_info
        elif page == 'types':
            req.args['type'] = path_info
        elif page == 'downloads':
            req.args['download'] = path_info

        # Process request and return content.
        api = self.env[DownloadsApi]
        return api.process_downloads(context)
