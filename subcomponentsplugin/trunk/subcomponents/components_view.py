# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.ticket import model
from trac.util.html import html
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_stylesheet
from trac.perm import IPermissionRequestor
from trac.web.api import IRequestHandler
from trac.web.chrome import Chrome, web_context
from trac.wiki import format_to_html


class ComponentsViewModule(Component):
    """Adds a separate end-user page that lists all components."""

    implements(INavigationContributor, IPermissionRequestor,
               IRequestHandler, ITemplateProvider)

    # IPermissionRequestor methods.

    def get_permission_actions(self):
        return ['COMPONENT_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'components'

    def get_navigation_items(self, req):
        if 'COMPONENT_VIEW' in req.perm:
            yield ('mainnav', 'components',
                   html.a('Components', href=req.href.components()))

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/components'

    def process_request(self, req):
        req.perm.require('COMPONENT_VIEW')

        component_names = []
        subcomponents = []
        for component in model.Component.select(self.env):
            component_names.append(component.name)
            active_tickets = 0
            active_tickets_wo_milestone = 0

            for id_, milestone in self.env.db_query("""
                    SELECT id, milestone FROM ticket
                    WHERE status <> 'closed' AND component=%s
                    """, (component.name,)):
                active_tickets += 1
                if not milestone:
                    active_tickets_wo_milestone += 1

            subname, sublevel = \
                self.get_subcomponent_name(component.name, component_names)
            description = format_to_html(self.env, web_context(req),
                                         component.description, True)

            subcomponents.append({
              'name': component.name,
              'subname': subname,
              'subcomponent_level': sublevel,
              'description': description,
              'active_tickets': active_tickets,
              'active_tickets_without_milestone': active_tickets_wo_milestone,
            })

        data = {
            'components': subcomponents,
            'no_milestone': 'no_milestone' in req.args,
            'hide_description': 'hide_description' in req.args
        }
        add_stylesheet(req, 'subcomponents/subcomponents.css')
        if hasattr(Chrome, 'jenv'):
            return 'components_jinja.html', data
        else:
            return 'components.html', data, None

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('usermanual', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_subcomponent_name(self, name, component_names):
        subname = name
        for component in component_names:
            if not name.startswith(component + '/'):
                continue

            sub = name[len(component):].lstrip('/')
            if len(sub) < len(subname):
                subname = sub

        sublevel = name[:-len(subname)].count('/')
        return subname, sublevel
