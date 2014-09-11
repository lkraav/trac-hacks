# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Component, implements
from trac.config import ListOption
from trac.util.translation import _
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider

import zipfile
import re
import os
from subprocess import Popen, PIPE
from pkg_resources import resource_filename  # @UnresolvedImport
import glob

SECTION = 'logwatcher'


class AppVersion(Component):

    """Display application version information.
    """
    implements(IAdminPanelProvider, ITemplateProvider)

    _app_list = ListOption(SECTION, 'app_list',
                           doc="""List of applications available on this server;
                          use this as prefix for your pattern.""")
    _app_patterns = {}
    _app_ps_patterns = {}
    _app_names = {}

    def __init__(self):
        self.log.info('>>>>>>>>>> init AppVersion; having app-list: %s'
                      % self._app_list)
        if self.config and self._app_list:
            for app in self._app_list:
                app_pat = self.config.getlist(SECTION, app + '.pattern')
                app_ps_pat = self.config.getlist(SECTION, app + '.ps_pattern')
                app_name = self.config.get(SECTION, app + '.name')
                self._app_names[app] = app_name

                if app_pat and len(app_pat) > 0:
                    self._app_patterns[app] = app_pat

                if app_ps_pat and len(app_ps_pat) > 0:
                    self._app_ps_patterns[app] = app_ps_pat

            self.log.debug('read app pattern: %s and app process pattern: %s'
                           % (self._app_patterns, self._app_ps_patterns))

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('logwatcher', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver/Genshi templates.
        """
        return [resource_filename(__name__, 'templates')]

    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN') \
                or req.perm.has_permission("LOG_WATCHER_VIEW"):
            yield ('general', _('General'), 'app_versions', 'App Versions')

    def render_admin_panel(self, req, category, page, path_info):
        html_template = 'app_versions.html'
        data = {}

        print self._app_patterns

        apps = []
        app_info = {}

        self.log.debug(">>>>> START RAEDING INFOS")
        if self._app_patterns and len(self._app_patterns) > 0:
            for app in self._app_patterns:
                self.log.debug("app: %s, pattern: %s" %
                               (app, self._app_patterns[app]))
                app_paths = []
                path_list = self._app_patterns[app]
                len_path_list = len(path_list)

                if len_path_list == 2:
                    paths = glob.glob(path_list[0])
                    self.log.debug("paths: %s" % paths)
                    self.log.debug("search pattern: %s" % path_list[1])
                    for p in paths:
                        for f in os.listdir(p):
                            pat = re.compile(path_list[1])
                            if pat.match(f):
                                if not p[len(p) - 1] in ('/', '\\'):
                                    p += '/'
                                p += f
                                self.log.debug(">>>>>>> found: %s" % p)
                                app_paths.append(p)
                                break
                else:
                    self.log.error("incorrect length of config param "
                                   "'pattern': %s (should be 2)"
                                   % len_path_list)

                if len(app_paths) > 0:
                    for pa in app_paths:
                        app_info = {'path': pa}
                        apps.append(app_info)
                elif len_path_list == 2:
                    self.log.warn("have not found any matching file for "
                                  "pattern %s" % path_list[1])

        if self._app_ps_patterns and len(self._app_ps_patterns) > 0:
            for app in self._app_ps_patterns:
                self.log.debug("app: %s, ps_pattern: %s"
                               % (app, self._app_ps_patterns[app]))
                ps_search = self._app_ps_patterns[app]
                if len(ps_search) == 1:
                    ps_jar, ps_info = self.get_jar_from_ps(ps_search[0])
                    if ps_jar and ps_info:
                        title, version = self.get_manifest(ps_jar)
                        app_info = {'path': ps_jar}
                        app_info['title'] = title
                        app_info['version'] = version
                        app_info['ps_info'] = ps_info
                        apps.append(app_info)

        print "apps (before): ", apps
        print "."
        print "."

        for info in apps:
            print "path: ", info['path']
            title, version = self.get_manifest(info['path'])
            print "title: %s, version: %s" % (title, version)
            info['title'] = title
            info['version'] = version
            print info

        print "app (after): ", apps
        data['apps'] = apps
        return html_template, data

    def get_jar_from_ps(self, pattern):
        platform = os.name
        ps_jar = None
        ps_info = None
        if platform == 'posix':
            process = Popen(
                ['ps', '-eo', 'pid,args'], stdout=PIPE, stderr=PIPE)
            stdout, notused = process.communicate()  # @UnusedVariable
            for line in stdout.splitlines():
                pid, cmdline = line.split(' ', 1)
                pat = re.compile(pattern)
                if pat.search(cmdline):
                    self.log.debug("pid, cmdline: %s, %s" % (pid, cmdline))
                    ps_jar = re.findall(pattern, cmdline)
                    if ps_jar and len(ps_jar) == 1:
                        # should be returned as string instead of list
                        ps_jar = ps_jar[0]
                    ps_info = cmdline
                    self.log.debug("ps_jar: %s" % ps_jar)
        else:
            self.log.error("%s is not a supported platform" % platform)

        return ps_jar, ps_info

    def get_manifest(self, jarname):
        print "try ", jarname
        if zipfile.is_zipfile(jarname):
            zfile = zipfile.ZipFile(jarname, "r")
            data = zfile.read('META-INF/MANIFEST.MF')
            print data
            title = re.findall(
                'Implementation-Title:[ ]*([ 0-9A-Za-z\.]+)', data)
            version = re.findall(
                'Implementation-Version:[ ]*([ _0-9A-Za-z\.]+)', data)
            print version
            return title[0], version[0]
        return None
