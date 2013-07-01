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

from genshi.builder import tag
from trac.config import BoolOption
from trac.core import Component, implements
from trac.resource import Resource
from trac.ticket import Version
from trac.util.datefmt import utc
from trac.util.translation import _
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import(
    INavigationContributor, add_stylesheet
)


class ReleasesModule(Component):
    implements(INavigationContributor, IRequestHandler, IRequestFilter)

    roadmap_navigation = BoolOption('extended_version', 'roadmap_navigation',
        'false', doc="""Whether to have the roadmap navigation item link to
        the versions page.""")

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'versions'

    def get_navigation_items(self, req):
        if 'VERSION_VIEW' in req.perm:
            if self.roadmap_navigation:
                yield ('mainnav', 'versions',
                       tag.a(_('Roadmap'), href=req.href.versions()))
            else:
                yield ('mainnav', 'versions',
                       tag.a(_('Versions'), href=req.href.versions()))

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if self.roadmap_navigation and 'VERSION_VIEW' in req.perm:
            self._remove_item(req, 'roadmap')
        return template, data, content_type

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/versions'

    def process_request(self, req):
        req.perm.require('VERSION_VIEW')

        showall = req.args.get('show') == 'all'

        versions = []
        for v in Version.select(self.env):
            resource = Resource('version', v.name)
            is_released = v.time and v.time < datetime.now(utc)

            if (showall or not is_released) and \
                    'VERSION_VIEW' in req.perm(resource):
                v.is_released = is_released
                v.resource = resource
                versions.append(v)

        versions.reverse()

        data = {
            'versions': versions,
            'showall': showall,
            'roadmap_navigation': self.roadmap_navigation
        }
        add_stylesheet(req, 'common/css/roadmap.css')
        return 'versions.html', data, None

    def _remove_item(self, req, name):

        navitems = req.chrome['nav']['mainnav']

        active = False
        for navitem in navitems:
            if navitem['active'] and navitem['name'] == name:
                active = True
            if navitem['name'] == name:
                navitems.remove(navitem)
        if active:
            for navitem in navitems:
                if navitem['name'] == 'versions':
                    navitem['active'] = True
