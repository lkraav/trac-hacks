# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The TracTweakUI Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
# ----------------------------------------------------------------------------

import os
import re
import urllib
from pkg_resources import resource_filename

from genshi.filters.transform import Transformer
from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.util.html import Markup, tag
from trac.util.text import to_unicode
from trac.web.api import ITemplateStreamFilter, IRequestHandler, RequestDone
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script

from model import schema, schema_version, schema_version_key, TracTweakUIModel

__all__ = ['TracTweakUIModule']


class TracTweakUIModule(Component):

    implements(IAdminPanelProvider, IEnvironmentSetupParticipant,
               IPermissionRequestor, IRequestHandler,
               ITemplateProvider, ITemplateStreamFilter)

    # ITemplateProvider

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('tractweakui', resource_filename(__name__, 'htdocs'))]

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['TRACTWEAKUI_VIEW', 'TRACTWEAKUI_ADMIN']
        return actions

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.env.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(schema_version, schema_version_key)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        dbm.create_tables(schema)
        dbm.set_database_version(schema_version, schema_version_key)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRACTWEAKUI_ADMIN' in req.perm:
            yield 'ticket', 'Ticket System', 'tweakui', 'Tweak UI'

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TRACTWEAKUI_ADMIN')

        data = {}

        # Analyze url
        action = ''
        if path_info:
            action = path_info.split('?', 1)[0].strip('/') \
                if '?' in path_info else path_info.strip('/')

        if action == 'edit_path_pattern':
            # edit path_pattern
            if req.method == 'POST':
                # TODO
                if 'save' in req.args:
                    # save filter
                    path_pattern = req.args.get("path_pattern", "").strip()
                    self._save_path_pattern(req)
                    req.redirect(req.href.admin(cat, page))

                elif 'delete' in req.args:
                    # delete filter
                    path_pattern = req.args.get("path_pattern", "").strip()
                    self._del_path_pattern(req)
                    req.redirect(req.href.admin(cat, page))

            else:
                # list filters
                path_pattern = req.args.get("path_pattern", "").strip()
                data["filter_names"] = self._get_filters()
                data["path_pattern"] = \
                    req.args.get("path_pattern", "").strip()
                return 'tractweakui_admin_list_filter.html', data

        elif action.startswith('edit_filter_script'):
            # edit script
            if req.method == 'POST':
                if 'save' in req.args:
                    # save filter
                    self._save_tweak_script(req)
                    path_pattern = req.args.get("path_pattern", "").strip()
                    data["filter_names"] = self._get_filters()
                    data["path_pattern"] = \
                        req.args.get("path_pattern", "").strip()
                    return 'tractweakui_admin_list_filter.html', data

                elif 'load_default' in req.args:
                    # load_default js script
                    data['path_pattern'] = \
                        req.args.get("path_pattern", "").strip()
                    data['filter_name'] = \
                        req.args.get("filter_name", "").strip()
                    data['tweak_script'] = self._load_default_script(req)
                    return 'tractweakui_admin_edit_filter.html', data

            else:
                # display filter details
                path_pattern = req.args.get("path_pattern", "").strip()
                filter_name = req.args.get("filter_name", "").strip()
                tweak_script = TracTweakUIModel.get_tweak_script(
                    self.env, path_pattern, filter_name)
                data['tweak_script'] = tweak_script
                data['path_pattern'] = path_pattern
                data['filter_name'] = filter_name
                return 'tractweakui_admin_edit_filter.html', data

        elif action == 'add_path_pattern' and req.method == 'POST':
            if 'add' in req.args:
                self._add_path_pattern(req)
                req.redirect(req.href.admin(cat, page))
        else:
            # list all path patterns
            data["path_patterns"] = TracTweakUIModel.get_path_patterns(
                self.env)
            return 'tractweakui_admin_list_path.html', data

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        # get all path patterns
        path_patterns = TracTweakUIModel.get_path_patterns(self.env)
        # try to match pattern
        for path_pattern in path_patterns:
            if re.match(path_pattern, req.path_info):
                break
        else:
            return stream

        filter_names = \
            TracTweakUIModel.get_path_filters(self.env, path_pattern)
        for filter_name in filter_names:
            self._apply_filter(req, path_pattern, filter_name)

        js_files = TracTweakUIModel.get_path_scripts(
            self.env, path_pattern)
        if js_files:
            script = ";\n".join(js_files)
        else:
            script = ""

        stream = stream | Transformer('head').append(
            tag.script(Markup(script), type="text/javascript")())
        return stream

    # IRequestHandler methods

    def match_request(self, req):
        return False

    def process_request(self, req):
        tweakui_js_path = '/tractweakui/tweakui_js'
        if req.path_info.startswith(tweakui_js_path):
            path_pattern = urllib.unquote(
                req.path_info[len(tweakui_js_path) + 1: -3])
            js_files = TracTweakUIModel.get_path_scripts(
                self.env, path_pattern)
            if js_files:
                script = ";\n".join(js_files)
            else:
                script = ""
            self._send_response(req, script)

    # Internal methods

    def _filter_path(self, *args):
        base_path = resource_filename(__name__, 'htdocs')
        return os.path.normpath(os.path.join(base_path, 'tractweakui', *args))

    def _apply_filter(self, req, path_pattern, filter_name):
        filter_path = self._filter_path(filter_name)
        if not os.path.exists(filter_path):
            return

        css_files = self._find_filter_files(filter_path, ".css")
        js_files = self._find_filter_files(filter_path, ".js")

        for css_file in css_files:
            add_stylesheet(req, 'site/tractweakui/%s/%s'
                                % (filter_name, css_file))

        for js_file in js_files:
            if js_file != "__template__.js":
                add_script(req, 'site/tractweakui/%s/%s'
                                % (filter_name, js_file))

    def _find_filter_files(self, filter_path, file_type):
        if not os.path.exists(filter_path):
            return []
        return [file
                for file in os.listdir(filter_path)
                if file.endswith(file_type)]

    def _get_filters(self):
        return [file for file in os.listdir(self._filter_path())]

    def _send_response(self, req, message):
        """
        """
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/x-javascript')
        # req.send_header('Content-Length', len(message))

        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone

    def _add_path_pattern(self, req):
        """ add filter
        """
        path_pattern = req.args.get("path_pattern", "").strip()

        # add to db
        TracTweakUIModel.insert_path_pattern(self.env, path_pattern)

    def _save_path_pattern(self, req):
        """ add filter
        """
        path_pattern = req.args.get("path_pattern", "").strip()
        path_pattern_orig = req.args.get("path_pattern_orig", "").strip()

        # add to db
        TracTweakUIModel.save_path_pattern(
            self.env, path_pattern, path_pattern_orig)

    def _del_path_pattern(self, req):
        """ del filter
        """
        path_pattern = req.args.get("path_pattern", "").strip()

        # add to db
        TracTweakUIModel.del_path_pattern(self.env, path_pattern)

    def _save_tweak_script(self, req):
        """ save tweak_script
        """
        filter_name = req.args.get("filter_name", "").strip()
        path_pattern = req.args.get("path_pattern", "").strip()
        tweak_script = req.args.get("tweak_script", "").strip()

        # add to db
        TracTweakUIModel.save_tweak_script(
            self.env, path_pattern, filter_name, tweak_script)

    def _load_default_script(self, req):
        """
        """
        filter_name = req.args.get("filter_name", "").strip()

        template_path = self._filter_path(filter_name, '__template__.js')
        if not os.path.exists(template_path):
            return ''

        try:
            return to_unicode(open(template_path).read())
        except Exception as e:
            self.log.error("Load js template failed.", exc_info=True)
            return ""
