# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Etienne PIERRE <e.ti.n.pierre_AT_gmail.com>
#
# TracBuildbot is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# TracBuildbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import re
import xmlrpclib

from genshi.builder import tag
from trac.config import IntOption, Option
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_ctxtnav
from trac.web.main import IRequestHandler
from trac.util import TracError, pathjoin


class BuildBotPlugin(Component):
    """A plugin to integrate Buildbot into Trac
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    buildbot_url = Option('buildbot', 'url',
        doc="""URL of the BuildBot instance.""")

    num_builds_display = IntOption('buildbot', 'numbuilds', 5,
        doc="""Number of builds to display.""")

    @property
    def xmlrpc_url(self):
        return pathjoin(self.buildbot_url, 'xmlrpc')

    def get_builder_url(self, builder_name):
        return pathjoin(self.buildbot_url, 'builders', builder_name)

    def get_build_url(self, builder_name, build_number):
        return pathjoin(self.get_builder_url(builder_name), build_number)

    def get_server(self):
        return xmlrpclib.ServerProxy(self.xmlrpc_url)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'buildbot'

    def get_navigation_items(self, req):
        yield ('mainnav', 'buildbot',
               tag.a('BuildBot', href=req.href.buildbot()))

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracbb', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/buildbot(/([^\/]*))?(/(\d+))?$', req.path_info)
        if match:
            if match.group(2):
                req.args['builder'] = match.group(2)
                if match.group(4):
                    req.args['buildnum'] = match.group(4)
            return True
        return False

    def get_builders(self, req):
        try:
            server = self.get_server()
            builders = server.getAllBuilders()
        except:
            raise TracError("Can't get access to buildbot at %s"
                            % self.xmlrpc_url)
        ret = []
        for builder in builders:
            lastbuilds = server.getLastBuilds(builder, 1)
            if len(lastbuilds) > 0:
                last_build = lastbuilds[0]
                last_number = last_build[1]
                last_status = last_build[5]
                last_branch = last_build[3]
                build = {
                    'name': builder,
                    'status': last_status,
                    'url': req.href.buildbot(builder),
                    'lastbuild': last_number,
                    'lastbuildurl': self.get_build_url(builder, last_number),
                    'lastbranch': last_branch
                }
            else:
                build = {
                    'name': builder,
                    'status': 'missing',
                    'url': req.href.buildbot(builder),
                    'lastbuild': None,
                    'lastbuildurl': None,
                    'lastbranch': None
                }

            ret.append(build)

        return ret

    def get_last_builds(self, builder):
        try:
            server = self.get_server()
            builds = server.getLastBuilds(builder, self.num_builds_display)
        except:
            raise TracError("Can't get builder %s on url %s"
                            % (builder, self.xmlrpc_url))
        #last build first
        builds.reverse()
        ret = []
        for build in builds:
            thisbuild = {
                'status': build[5],
                'number': build[1],
                'url': self.get_build_url(builder, build[1]),
                'branch': build[3]
            }
            ret.append(thisbuild)

        return ret

    def process_request(self, req):
        add_ctxtnav(req, 'Buildbot Server',
                    self.buildbot_url)
        add_ctxtnav(req, 'Waterfall display',
                    pathjoin(self.buildbot_url, 'waterfall'))
        add_ctxtnav(req, 'Grid display',
                    pathjoin(self.buildbot_url, 'grid'))
        add_ctxtnav(req, 'Latest Build',
                    pathjoin(self.buildbot_url, 'one_box_per_builder'))
        data = {'buildbot_url': self.buildbot_url}
        if 'builder' not in req.args:
            data['title'] = 'BuildBot'
            data['bb_builders'] = self.get_builders(req)
            template = 'tracbb_overview.html'
        else:
            builder = req.args['builder']
            builds = self.get_last_builds(builder)
            data['title'] = 'Builder ' + builder
            data['bb_builder'] = builder
            data['bb_builds'] = builds
            template = 'tracbb_builder.html'
        return template, data, None
