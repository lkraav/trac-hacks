# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Malcolm Studd <mestudd@gmail.com>
# Copyright (C) 2012-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from datetime import datetime

from trac.core import Component, implements
from trac.resource import Resource
from trac.ticket.model import Version
from trac.ticket.roadmap import RoadmapModule
from trac.util.datefmt import utc
from trac.util.html import html as tag
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, add_stylesheet


class ReleasesModule(Component):
    implements(INavigationContributor, IRequestHandler)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'versions'

    def get_navigation_items(self, req):
        if 'VERSION_VIEW' in req.perm:
            if self.env.enabled[RoadmapModule]:
                label = _("Versions")
            else:
                label = _("Roadmap")
            yield ('mainnav', 'versions',
                   tag.a(label, href=req.href.versions()))

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/versions'

    def process_request(self, req):
        req.perm.require('VERSION_VIEW')

        show_all = req.args.get('show') == 'all'

        versions = []
        for version in Version.select(self.env):
            resource = Resource('version', version.name)
            is_released = version.time and version.time < datetime.now(utc)

            if (show_all or not is_released) and \
                    'VERSION_VIEW' in req.perm(resource):
                version.is_released = is_released
                version.resource = resource
                versions.append(version)

        versions.reverse()

        data = {
            'versions': versions,
            'showall': show_all,
            'roadmapmodule_disabled': not self.env.enabled[RoadmapModule]
        }
        add_stylesheet(req, 'common/css/roadmap.css')
        return 'versions.html', data, None
