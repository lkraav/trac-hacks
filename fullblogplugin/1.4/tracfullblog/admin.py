# -*- coding: utf-8 -*-
"""
TracFullBlog admin panel for some settings related to the plugin.

License: BSD

(c) 2007 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from trac.core import *
from trac.admin import IAdminPanelProvider
from trac.resource import Resource
from trac.web.chrome import Chrome, add_warning

from .core import FullBlogCore


class FullBlogAdminPanel(Component):
    """Admin panel for settings related to FullBlog plugin."""

    implements(IAdminPanelProvider)

    # IAdminPageProvider

    def get_admin_panels(self, req):
        if 'BLOG_ADMIN' in req.perm('blog'):
            yield 'blog', 'Blog', 'settings', 'Settings'

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm(Resource('blog')).require('BLOG_ADMIN')

        blog_admin = {}
        blog_core = FullBlogCore(self.env)

        if req.method == 'POST':
            self.config.set('fullblog', 'num_items_front',
                req.args.getint('numpostsfront'))
            self.config.set('fullblog', 'default_postname',
                req.args.get('defaultpostname'))
            self.config.save()
            blog_core.set_bloginfotext(req.args.get('bloginfotext'))
            req.redirect(req.href.admin(req.args['cat_id'],
                                        req.args['panel_id']))

        blog_admin['bloginfotext'] = blog_core.get_bloginfotext()
        blog_admin['numpostsfront'] = \
                self.config.getint('fullblog', 'num_items_front')
        blog_admin['defaultpostname'] = \
                self.config.get('fullblog', 'default_postname')

        chrome = Chrome(self.env)
        chrome.add_auto_preview(req)
        chrome.add_wiki_toolbars(req)

        return 'fullblog_admin.html', {'blog_admin': blog_admin}
