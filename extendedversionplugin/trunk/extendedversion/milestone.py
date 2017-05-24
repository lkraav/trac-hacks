# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Malcolm Studd <mestudd@gmail.com>
# Copyright (C) 2012-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from genshi.filters.transform import StreamBuffer, Transformer
from trac.core import Component, implements
from trac.resource import Resource, ResourceNotFound
from trac.ticket.api import IMilestoneChangeListener
from trac.ticket.model import Milestone
from trac.util.html import html as tag
from trac.util.datefmt import to_timestamp
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import INavigationContributor, web_context

from extendedversion.version import VisibleVersion


class MilestoneVersion(Component):
    """Add a 'Version' attribute to milestones.
    """

    implements(IMilestoneChangeListener, INavigationContributor,
               IRequestFilter, ITemplateStreamFilter)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'versions'

    def get_navigation_items(self, req):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        action = req.args.get('action', 'view')
        name = req.args.get('name')
        version = req.args.get('version')
        if req.path_info.startswith('/milestone') and \
                req.method == 'POST' and action == 'edit':
            # Removal is handled in change listener
            if name:
                self._delete_milestone_version(name)
                if version and action == 'edit':
                    self._insert_milestone_version(name, version)

        if req.path_info.startswith('/admin/ticket/milestones') and \
                req.method == 'POST' and \
                req.args.get('__FORM_TOKEN') == req.form_token:
            # Removal is handled in change listener
            if 'add' in req.args:
                # 'Add' button on main milestone panel
                if not self._get_milestone(name) and version:
                    self._insert_milestone_version(name, version)
            elif 'save' in req.args:
                # 'Save' button on 'Manage milestone' panel
                old_name = req.args.get('path_info')
                self._delete_milestone_version(old_name)
                if version:
                    self._insert_milestone_version(name, version)

        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        # Allow setting version for milestone
        if filename == 'milestone_edit.html':
            xformer = Transformer('//fieldset[1]')
            return stream | xformer.before(self._version_edit(data))

        # Display version for milestone
        elif filename == 'milestone_view.html':
            milestone = data.get('milestone').name
            xformer = Transformer('//div[@id="content" and '
                                  '      @class="milestone"]'
                                  '/div/p[@class="date"]')
            return stream | xformer.append(self._version_display(req,
                                                                 milestone))
        elif filename == 'roadmap.html':
            return self._milestone_versions(stream, req)
        elif filename == 'admin_milestones.html':
            if req.args['path_info']:
                xformer = Transformer('//fieldset/div[1]')
                return stream | xformer.after(self._version_edit(data))
            else:
                xformer = Transformer('//form[@id="addmilestone"]'
                                      '/fieldset/div[1]')
                return stream | xformer.after(self._version_edit(data))
        return stream

    # IMilestoneChangeListener methods

    def milestone_created(self, milestone):
        pass

    def milestone_changed(self, milestone, old_values):
        pass

    def milestone_deleted(self, milestone):
        self._delete_milestone_version(milestone.name)

    # Internal methods

    def _get_milestone(self, name):
        try:
            return Milestone(self.env, name)
        except ResourceNotFound:
            return None

    def _delete_milestone_version(self, milestone):
        self.env.db_transaction("""
            DELETE FROM milestone_version WHERE milestone=%s
            """, (milestone,))

    def _insert_milestone_version(self, milestone, version):
        self.env.db_transaction("""
                INSERT INTO milestone_version (milestone, version)
                VALUES (%s, %s)
                """, (milestone, version))

    def _milestone_versions(self, stream, req):
        buffer = StreamBuffer()

        def apply_version():
            return self._version_display(req, buffer.events[1][1])

        filter = Transformer('//*[@class="milestone"]/div/h2/a/em') \
            .copy(buffer).end() \
            .select('//*[@class="milestone"]//p[@class="date"]') \
            .append(apply_version)
        return stream | filter

    def _version_display(self, req, milestone):
        resource = Resource('milestone', milestone)
        context = web_context(req, resource)
        for ver, in self.env.db_query("""
                SELECT version FROM milestone_version WHERE milestone=%s
                """, (milestone,)):
            link = VisibleVersion(self.env)._render_link(context, ver, ver)
            return tag.span("; For ", link, class_='date')
        else:
            return []

    def _version_edit(self, data):
        if data.get('milestone'):
            milestone = data.get('milestone').name
        else:
            milestone = ''
        for version, in self.env.db_query("""
                SELECT version FROM milestone_version WHERE milestone=%s
                """, (milestone,)):
            break
        else:
            version = None

        return tag.div(
            tag.label(
                'Version:',
                tag.br(),
                tag.select(
                    tag.option(),
                    [tag.option(name, selected=(version == name or None))
                     for name, in self.env.db_query("""
                        SELECT name FROM version
                        WHERE time IS NULL OR time = 0 OR time>%s OR name = %s
                        ORDER BY name""", (to_timestamp(None), version))],
                    name="version")),
            class_="field")
