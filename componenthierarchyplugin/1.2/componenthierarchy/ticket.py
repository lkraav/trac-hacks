# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 falkb
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.ticket import model
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, \
                            add_script_data, add_stylesheet

from componenthierarchy.model import ComponentHierarchyModel


class ComponentHierarchyTicket(Component):

    implements(IRequestFilter, ITemplateProvider)

    def __init__(self):
        self._ChModel = ComponentHierarchyModel(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            all_components = model.Component.select(self.env)
            component_children = {}

            for comp in all_components:
                comp_children = self._ChModel.get_direct_children(comp.name)
                if comp_children:
                    component_children[comp.name] = comp_children

            component_children = {'component_children': component_children}
            add_script_data(req, component_children)
            add_stylesheet(req,
                           'componenthierarchy/css/component_hierarchy.css')
            add_script(req,
                       'componenthierarchy/create_component_hierarchy.js')

        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('componenthierarchy', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
