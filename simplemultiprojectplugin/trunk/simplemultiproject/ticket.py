# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
from collections import defaultdict
from trac.core import Component as TracComponent, implements
from trac.ticket.model import Component
from trac.web.api import IRequestFilter
from simplemultiproject.smp_model import PERM_TEMPLATE, SmpComponent, SmpProject


class SmpTicket(TracComponent):
    """Filtering of components for now"""
    implements(IRequestFilter)

    def __init__(self):
        self.smp_project = SmpProject(self.env)
        self.smp_component = SmpComponent(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if data and template == "ticket.html":
            # Create a new list of available components for the ticket
            try:
                comp_field = data['fields_map']['component']
            except KeyError:
                pass  # May have been filtered but one of the ticket field filter plugins
            else:
                data['fields'][comp_field]['options'] = self.get_components_for_user(req)

        return template, data, content_type

    def get_components_for_user(self, req):
        """Check if user has access tothis milestone. Returns True if access is possible otherwise False-"""
        # dict with key: milestone, val: list of project ids
        components = defaultdict(list)
        for comp in self.smp_component.get_all_components_and_project_id():
            components[comp[0]].append(comp[1])  # comp[0]: name, comp[1]: project id

        comps = []
        all_comps = Component.select(self.env)
        for comp in all_comps:
            if comp.name in components:
                project_ids = components[comp.name]
                for project in project_ids:
                    if (PERM_TEMPLATE % project) in req.perm:
                        comps.append(comp.name)
                del components[comp.name]
            else:
                comps.append(comp.name)

        return comps
