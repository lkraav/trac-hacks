# -*- coding: utf-8 -*-
#
# Copyright (C) 2017, 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.prefs.api import IPreferencePanelProvider
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider, add_notice, add_stylesheet,\
    add_script
from trac.web.api import IRequestHandler, IRequestFilter, HTTPException
from pkg_resources import ResourceManager
from trac import __version__ as VERSION

_path_css = '/contextchrome/userstyle.css'
_path_js = '/contextchrome/userscript.js'


class UserStyle(Component):
    """ inject user's own script or style to all page. """
    implements(IPreferencePanelProvider, IRequestFilter,
               IRequestHandler, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        pass  # do nothing
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template and (template.startswith('prefs') or \
                template.startswith('admin')):
            pass  # do nothing, for troubleshoot yourself
            return template, data, content_type
        if _path_css in req.session:
            add_stylesheet(req, _path_css)
        if _path_js in req.session:
            add_script(req, _path_js)
        return template, data, content_type

    # IRequestHandler methods

    def match_request(self, req):
        return _path_css == req.path_info \
            or _path_js == req.path_info

    def process_request(self, req):
        if _path_css == req.path_info:
            content = req.session[_path_css]
            content_type = 'text/css'
        elif _path_js == req.path_info:
            content = req.session[_path_js]
            content_type = 'application/javascript'
        else:
            raise HTTPException('File %s not found', req.path_info)
        req.send_response(200)
        req.send_header('Content-Type', content_type)
        # req.send_header('Last-Modified', last_modified)
        req.send_header('Content-Length', len(content))
        req.write(str(content))

    # IPreferencePanelProvider methods

    def get_preference_panels(self, req):
        yield 'userstyle', _("User Style")

    def render_preference_panel(self, req, panel):
        if req.method == 'POST':
            if 'userstyle' in req.args:
                if _path_css in req.session:
                    req.session.pop(_path_css)
                userstyle = req.args.get('userstyle')
                if userstyle:
                    req.session[_path_css] = userstyle
                add_notice(req, _("Your preferences have been saved."))
            if 'userscript' in req.args:
                if _path_js in req.session:
                    req.session.pop(_path_js)
                userscript = req.args.get('userscript')
                if userscript:
                    req.session[_path_js] = userscript
                add_notice(req, _("Your preferences have been saved."))
            req.redirect(req.href.prefs(panel or None))

        userstyle = req.session[_path_css] if _path_css in req.session else ''
        userscript = req.session[_path_js] if _path_js in req.session else ''
        data = {'userstyle': userstyle,
                'userscript': userscript}
        if VERSION < '1.3.2':
            return 'genshi_prefs_userstyle.html', data
        else:
            return 'prefs_userstyle.html', data

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [ResourceManager().resource_filename('contextchrome',
                                                    'templates')]
