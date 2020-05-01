# -*- coding: utf-8 -*-
"""
TracFullBlog admin panel for some settings related to the plugin.

License: BSD

(c) 2007 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from trac.core import *
from trac.admin import IAdminPanelProvider
from trac.resource import Resource
from trac.web.chrome import add_warning, Chrome

from core import FullBlogCore


class FullBlogAdminPanel(Component):
    """Admin panel for settings related to FullBlog plugin."""

    implements(IAdminPanelProvider)

    # IAdminPageProvider

    def get_admin_panels(self, req):
        if 'BLOG_ADMIN' in req.perm('blog'):
            yield 'blog', 'Blog', 'settings', 'Settings'

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm(Resource('blog', None)).require('BLOG_ADMIN')

        blog_admin = {}
        blog_core = FullBlogCore(self.env)

        if req.method == 'POST':
            if req.args.get('savesettings'):
                self.config.set('fullblog', 'num_items_front',
                    req.args.getint('numpostsfront'))
                self.config.set('fullblog', 'default_postname',
                    req.args.get('defaultpostname'))
                self.config.save()
            elif req.args.get('savebloginfotext'):
                blog_core.set_bloginfotext(req.args.get('bloginfotext'))
                req.redirect(req.href.admin(req.args['cat_id'],
                                            req.args['panel_id']))
            else:
                self.log.warning('Unknown POST request: %s', req.args)

        blog_admin['bloginfotext'] = blog_core.get_bloginfotext()
        blog_admin['numpostsfront'] = \
                self.config.getint('fullblog', 'num_items_front')
        blog_admin['defaultpostname'] = \
                self.config.get('fullblog', 'default_postname')

        return 'fullblog_admin.html', {'blog_admin': blog_admin}, None
