# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013, 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_script_data
from pkg_resources import resource_filename


class TypeClassToTicket(Component):
    """ set css-class to type on ticket. """
    implements(IRequestFilter, ITemplateProvider)

    def get_resource_tags(self, req, resource):
        try:
            from tractags.wiki import WikiTagProvider
            tag_provider = self.compmgr[WikiTagProvider]
            return tag_provider.get_resource_tags(req, resource)
        except:
            return []

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler  # unchanged

    def post_process_request(self, req, template, data, content_type):
        value = None
        if template == 'ticket.html' and 'ticket' in data:
            ticket = data['ticket'].values
            fields = self.config.getlist('ticket', 'decorate_fields')
            value = ' '.join(['%s_is_%s' % (field, value.rstrip(' ').rstrip(',').replace('"', ''))
                              for field in fields if field in ticket for value in ticket.get(field).split(' ')]
                             # FIXME: custom field of datetime occurs exception; it does not have 'split' attr.
                             + [ticket.get('type')]  # backward compatibility
                             )
        if template == 'wiki_view.html':
            value = ' '.join(['tagged_as_%s' % tag for tag in self.get_resource_tags(req, data['context'].resource)])

        if value:
            add_script(req, "contextchrome/js/bodyclassdecolator.js")
            add_script_data(req, contextchrome_bodyclass=value)
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
