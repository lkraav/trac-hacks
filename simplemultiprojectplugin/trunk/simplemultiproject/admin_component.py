# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering
#

# Trac core imports
from trac.core import *
from trac.config import *
from trac.util.translation import _
from trac.ticket import model
from trac.perm import PermissionSystem
from trac.web.chrome import Chrome, add_notice

# Trac extension point imports
from trac.web.api import ITemplateStreamFilter
from trac.perm import IPermissionRequestor
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider, add_notice

# Model Class
from simplemultiproject.model import *

# genshi
from genshi.builder import tag
from genshi.filters.transform import Transformer

from operator import itemgetter

class SmpComponentAdminPanel(Component):
    """Allows to specify project dependent components"""

    implements(IAdminPanelProvider, ITemplateProvider, ITemplateStreamFilter)
    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == "smp_admin_components.html" and data.get('component'):
            filter = Transformer('//form[@id="modcomp"]/fieldset/div[1]')
            return stream | filter.after(self.__edit_project(data))

        return stream

    def __edit_project(self, data):
        component = data.get('component').name
        all_projects = self.__SmpModel.get_all_projects()
        id_project_component = self.__SmpModel.get_id_projects_component(component)
        id_projects_selected = []

        for id_project in id_project_component:
            id_projects_selected.append(id_project[0])

        return tag.div(
                       tag.label(
                       'Available in Project(s):',
                       tag.br(),
                       tag.select(
                       tag.option("All", value="0"),
                       [tag.option(row[1], selected=(row[0] in id_projects_selected or None), value=row[0]) for row in sorted(all_projects, key=itemgetter(1))],
                       name="project", multiple="multiple", size="10")
                       ),
                       class_="field")

    # IAdminPanelProvider
    def render_admin_panel(self, req, category, page, component):
        req.perm.require('PROJECT_ADMIN')
        # Detail view?
        if component:
            comp = model.Component(self.env, component)
            cprojects = self.__SmpModel.get_projects_component(comp.name)
            cprojects = [cproj[0] for cproj in cprojects]
            
            all_projects = self.__SmpModel.get_all_projects()
            
            if req.method == 'POST':
                if req.args.get('apply'):
                    cprojects = req.args.get('sel')
                    self.__SmpModel.delete_component_projects(comp.name)
                    if cprojects and 'all' not in cprojects:
                        self.__SmpModel.insert_component_projects(comp.name, cprojects)
                        
                    add_notice(req, _('Your changes have been saved.'))
                    req.redirect(req.href.admin(category, page))
                    
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(category, page))

            Chrome(self.env).add_wiki_toolbars(req)
            data = {'view': 'detail', 'component': comp, 'component_projects': cprojects, 'projects': all_projects }

        else:
            projects = {}
            for comp in model.Component.select(self.env):
                comp_name = comp.name
                cprojects = self.__SmpModel.get_projects_component(comp_name)
                cprojects = [cproj[0] for cproj in cprojects]
                                    
                projects[comp_name] = cprojects
                
            data = {'view': 'list', 'components': model.Component.select(self.env), 'projects': projects}

        return 'smp_admin_components.html', data

    def get_admin_panels(self, req):
        if 'PROJECT_ADMIN' in req.perm('projects'):
            return (('projects', _('Manage Projects'), 'components', _('Components')),)

    # ITemplateProvider
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('simplemultiproject', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
