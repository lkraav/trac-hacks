# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Cinc
#
# License: 3-clause BSD
#
from collections import defaultdict
from trac.config import BoolOption
from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket.model import Component as TicketComponent
from trac.ticket.model import Milestone, Version
from trac.ticket.api import IMilestoneChangeListener
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, \
    add_script_data, add_stylesheet

from simplemultiproject.compat import JTransformer
from simplemultiproject.milestone import create_projects_table_j
from simplemultiproject.model import SmpModel
from simplemultiproject.smp_model import SmpComponent, SmpProject, \
    SmpVersion, SmpMilestone


def _allow_no_project(self):
    """Check config if user enabled milestone creation without prior
    selection of a project.

    @return: True if milestones may be created without a project
    """
    return self.env.config.getbool("simple-multi-project", "allow_no_project", False)


def get_milestone_from_trac(env, name):
    try:
        return Milestone(env, name)
    except ResourceNotFound:
        return None

projects_tmpl = u"""
<div xmlns:py="http://genshi.edgewall.org/" id="smp-ms-sel-div" py:if="all_projects">
$proj
<select id="smp-project-sel">
    <option value="" selected="'' == sel_prj or None}">$all_label</option>
    <option py:for="prj in all_projects" value="$prj" selected="${prj == sel_prj or None}">$prj</option>
</select>
</div>
"""

def create_project_select_ctrl(all_proj):
    div_templ = u"""<div id="smp-ms-sel-div">
{proj}
<select id="smp-project-sel">
    <option value="" selected>{all_label}</option>
    {options}
</select>
</div>"""
    options_templ = u"""<option value="{prj}">{prj}</option>"""

    if not all_proj:
        return ''

    options = u''
    for prj in all_proj:
        options += options_templ.format(prj=prj)

    return div_templ.format(proj=_("Project"), all_projects=all_proj, sel_prj="", all_label=_("All"),
                            options=options)


class SmpFilterDefaultMilestonePanels(Component):
    """Modify default Trac admin panels for milestones to include
    project selection.

    Using this component you may associate a milestone with one or more
    projects using the default Trac admin panels.

    Creation of milestones is only possible when a project is chosen.
    You may disable this behaviour by setting the following in ''trac.ini'':

    {{{
    [simple-multi-project]
    milestone_without_project = True
    }}}

    To ensure only a single project is associated with each milestone
    set the following in ''trac.ini'':
    {{{
    [simple-multi-project]
    single_project_milestones = True
    }}}
    """

    allow_no_project = BoolOption(
        'simple-multi-project', 'milestone_without_project', False,
        doc="""Set this option to {{{True}}} if you want to create milestones
               without associated projects. The default value is {{{False}}}.
               """)
    single_project = BoolOption(
        'simple-multi-project', 'single_project_milestones', False,
        doc="""If set to {{{True}}} only a single project can be associated
               with a milestone. The default value is {{{False}}}.
               """)

    implements(IRequestFilter, IMilestoneChangeListener)

    def __init__(self):
        self._SmpModel = SmpModel(self.env)
        self.smp_model = SmpMilestone(self.env)
        self.smp_project = SmpProject(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if self._is_valid_request(req) and req.method == "POST":
            if req.path_info.startswith('/admin/ticket/milestones'):
                # Removal is handled in change listener
                if 'add' in req.args:
                    # 'Add' button on main milestone panel
                    # Check if we already have this milestone.
                    # Trac will show an error later if so.
                    # Don't change the db for smp if already exists.
                    p_ids = req.args.getlist('sel')
                    if not get_milestone_from_trac(self.env, req.args.get('name')) and p_ids:
                        # Note this one handles lists and single ids
                        self.smp_model.add(req.args.get('name'), p_ids)  # p_ids may be a list here
                elif 'save' in req.args:
                    # 'Save' button on 'Manage milestone' panel
                    p_ids = req.args.getlist('sel')
                    self.smp_model.delete(req.args.get('path_info'))
                    # Note this one handles lists and single ids
                    self.smp_model.add_after_delete(req.args.get('name'), p_ids)
        return handler

    @staticmethod
    def _is_valid_request(req):
        """Check request for correct path and valid form token"""
        if req.path_info.startswith('/admin/ticket/milestones') and \
                req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    def post_process_request(self, req, template, data, content_type):
        if data and template == "admin_milestones.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            if self.single_project:
                input_type = 'radio'
            else:
                input_type = "checkbox"  # Default input type for project selection.
            filter_list = []
            if not req.args['path_info']:

                all_proj = {}
                for name, p_id in self.smp_project.get_name_and_id():
                    all_proj[p_id] = name

                # Note:
                # A milestone without a project may have for historical reasons
                # a project id of '0' instead of missing from the SMP milestone table
                all_ms_proj = defaultdict(list)
                all_ms_proj_2 = defaultdict(list)
                for ms, p_id in self.smp_model.get_all_milestones_and_id_project_id():
                    all_ms_proj_2[ms].append((u'<span>%s</span><br>' % all_proj[p_id]) if p_id else '')
                    all_ms_proj[ms].append(all_proj[p_id] if p_id else '')

                add_script_data(req, {'smp_proj_per_item': all_ms_proj})

                # Add project column to main version table
                column_data = {}
                for item in all_ms_proj_2:
                    column_data[item] = ''.join(all_ms_proj_2[item])

                add_script_data(req, {'smp_tbl_hdr': {'css': 'table#millist',
                                                      'html': '<th>%s</th>' % _("Restricted to Project")
                                                      },
                                      'smp_tbl_cols': column_data,
                                      'smp_td_class': 'project',
                                      'smp_tbl_selector': '#millist'
                                      })
                add_script(req, 'simplemultiproject/js/smp_insert_column.js')

                # Add select control with projects for hiding milestones
                known_proj = self.env.config.getlist('ticket-custom', 'project.options', sep='|')
                xform = JTransformer('table#millist')
                filter_list.append(xform.before(create_project_select_ctrl(known_proj)))

                # The 'add milestone' part of the page
                # Insert project selection control
                # xpath: //form[@id="addmilestone"]//div[@class="field"][1]
                xform = JTransformer('form#addmilestone div.field:nth-of-type(1)')
                filter_list.append(xform.after(create_projects_table_j(self, self._SmpModel, req,
                                                                       input_type=input_type)))
                if filter_list:
                    add_script_data(req, {'smp_filter': filter_list})
                    add_script(req, 'simplemultiproject/js/jtransform.js')

                # disable button script must be inserted at the end.
                if not self.allow_no_project:
                    add_script_data(req, {'smp_input_control': '#projectlist input:' + input_type,
                                          'smp_submit_btn': 'form#addmilestone input[name=add]'})
                    add_script(req, 'simplemultiproject/js/disable_submit_btn.js')

                add_script(req, "simplemultiproject/js/filter_table.js")
            else:
                # Insert project selection control
                # xpath: //form[@id="edit"]//div[@class="field"][1]
                xform = JTransformer('form#edit div.field:nth-of-type(1)')
                filter_list.append(xform.after(create_projects_table_j(self, self._SmpModel, req,
                                                                       input_type=input_type)))
                if filter_list:
                    add_script_data(req, {'smp_filter': filter_list})
                    add_script(req, 'simplemultiproject/js/jtransform.js')

                # disable button script must be inserted at the end.
                if not self.allow_no_project:
                    add_script_data(req, {'smp_input_control': '#projectlist input:' + input_type,
                                          'smp_submit_btn': 'form#edit input[name=save]'})
                    add_script(req, 'simplemultiproject/js/disable_submit_btn.js')

        return template, data, content_type

    # IMilestoneChangeListener methods

    def milestone_created(self, milestone):
        self.log.debug("Milestone '%s' created.", milestone.name)
        pass

    def milestone_changed(self, milestone, old_values):
        pass

    def milestone_deleted(self, milestone):
        self.smp_model.delete(milestone.name)


def get_version_from_trac(env, name):
    try:
        return Version(env, name)
    except ResourceNotFound:
        return None


class SmpFilterDefaultVersionPanels(Component):
    """Modify default Trac admin panels for versions to include project selection.

    Creation of versions is only possible when a project is chosen.
    You may disable this behaviour by setting the
    following in ''trac.ini'':

    {{{
    [simple-multi-project]
    version_without_project = True
    }}}

    To ensure only a single project is associated with each version set
    the following in ''trac.ini'':
    {{{
    [simple-multi-project]
    single_project_versions = True
    }}}
    """

    implements(IRequestFilter)

    allow_no_project = BoolOption(
        'simple-multi-project', 'version_without_project', False,
        doc="""Set this option to {{{True}}} if you want to create versions
               without associated projects. The default value is {{{False}}}.
               """)

    single_project = BoolOption(
        'simple-multi-project', 'single_project_versions', False,
        doc="""If set to {{{True}}} only a single project can be associated
               with a version. The default value is {{{False}}}.
               """)

    def __init__(self):
        self._SmpModel = SmpModel(self.env)
        self.smp_project = SmpProject(self.env)
        self.smp_model = SmpVersion(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if self._is_valid_request(req) and req.method == "POST":
            if req.path_info.startswith('/admin/ticket/versions'):
                if 'add' in req.args:
                    # 'Add' button on main milestone panel
                    # Check if we already have this milestone.
                    # Trac will show an error later if so.
                    # Don't change the db for smp if already exists.
                    p_ids = req.args.getlist('sel')
                    if not get_version_from_trac(self.env, req.args.get('name')) and p_ids:
                        self.smp_model.add(req.args.get('name'), p_ids)
                elif 'remove' in req.args:
                    # 'Remove' button on main version panel
                    self.smp_model.delete(req.args.getlist('sel'))
                elif 'save' in req.args:
                    # 'Save' button on 'Manage version' panel
                    p_ids = req.args.getlist('sel')
                    self.smp_model.delete(req.args.get('path_info'))
                    self.smp_model.add_after_delete(req.args.get('name'), p_ids)
        return handler

    @staticmethod
    def _is_valid_request(req):
        """Check request for correct path and valid form token"""
        if req.path_info.startswith('/admin/ticket/versions') and \
                req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    def post_process_request(self, req, template, data, content_type):
        if data and template == "admin_versions.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")

            filter_list = []
            if self.single_project:
                input_type = 'radio'
            else:
                input_type = "checkbox"  # Default input type for project selection.

            if not req.args['path_info']:
                all_proj = {}
                for name, p_id in self.smp_project.get_name_and_id():
                    all_proj[p_id] = name

                all_ver_proj = defaultdict(list)  # Needed for filtering
                all_ver_proj_2 = defaultdict(list)  # Needed for column insertion
                for ver, p_id in self.smp_model.get_all_versions_and_project_id():
                    all_ver_proj[ver].append(all_proj[p_id])
                    all_ver_proj_2[ver].append(u'<span>%s</span><br>' % all_proj[p_id])
                add_script_data(req, {'smp_proj_per_item': all_ver_proj})

                # Add project column to main version table
                column_data = {}
                for item in all_ver_proj_2:
                    column_data[item] = ''.join(all_ver_proj_2[item])

                add_script_data(req, {'smp_tbl_hdr': {'css': 'table#verlist',
                                                      'html': '<th>%s</th>' % _("Restricted to Project")
                                                      },
                                      'smp_tbl_cols': column_data,
                                      'smp_td_class': 'project',
                                      'smp_tbl_selector': '#verlist'
                                      })
                add_script(req, 'simplemultiproject/js/smp_insert_column.js')

                known_proj = self.env.config.getlist('ticket-custom', 'project.options', sep='|')
                xform = JTransformer('table#verlist')
                filter_list.append(xform.before(create_project_select_ctrl(known_proj)))

                # Insert project selection control
                # xpath: //form[@id="addversion"]//div[@class="field"][1]
                xform = JTransformer('form#addversion div.field:nth-of-type(1)')
                filter_list.append(xform.after(create_projects_table_j(self, self._SmpModel, req,
                                                                       input_type=input_type)))

                # Remove current date/time as release date otherwise the version will be filtered on the roadmap.
                # User probably forgets to change it on creation and would be surprised not finding it.
                #stream |= Transformer('//form[@id="addversion"]//input[@id="releaseddate"]').attr("value", '')

                if filter_list:
                    add_script_data(req, {'smp_filter': filter_list})
                    add_script(req, 'simplemultiproject/js/jtransform.js')

                # disable button script must be inserted at the end.
                if not self.allow_no_project:
                    add_script_data(req, {'smp_input_control': '#projectlist input:' + input_type,
                                          'smp_submit_btn': 'form#addversion input[name=add]'})
                    add_script(req, 'simplemultiproject/js/disable_submit_btn.js')

                add_script(req, "simplemultiproject/js/filter_table.js")
            else:
                # 'Modify versions' panel

                # Insert project selection control
                # xpath: //form[@id="edit"]//div[@class="field"][1]
                xform = JTransformer('form#edit div.field:nth-of-type(1)')
                filter_list.append(xform.after(create_projects_table_j(self, self._SmpModel, req,
                                                                       input_type=input_type)))
                if filter_list:
                    add_script_data(req, {'smp_filter': filter_list})
                    add_script(req, 'simplemultiproject/js/jtransform.js')

                # disable button script must be inserted at the end.
                if not self.allow_no_project:
                    add_script_data(req, {'smp_input_control': '#projectlist input:' + input_type,
                                          'smp_submit_btn': 'form#edit input[name=save]'})
                    add_script(req, 'simplemultiproject/js/disable_submit_btn.js')

        return template, data, content_type


def get_component_from_trac(env, name):
    try:
        return TicketComponent(env, name)
    except ResourceNotFound:
        return None


class SmpFilterDefaultComponentPanels(Component):
    """Modify default Trac admin panels for components to include
    project selection.

    You need ''TICKET_ADMIN'' rights so the component panel is visible
    in the ''Ticket System'' section.

    After enabling this component you may disable the component panel
    in the ''Manage Projects'' section by adding the following to ''trac.ini'':
    {{{
    [components]
    simplemultiproject.admin_component.* = disabled
    }}}
    """
    implements(IRequestFilter)

    def __init__(self):
        self._SmpModel = SmpModel(self.env)
        self.smp_model = SmpComponent(self.env)
        self.smp_project = SmpProject(self.env)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if self._is_valid_request(req) and req.method == 'POST':
            if req.path_info.startswith('/admin/ticket/components'):
                if 'add' in req.args:
                    # 'Add' button on main component panel
                    # Check if we already have this component.
                    # Trac will show an error later if so.
                    # Don't change the db for smp.
                    p_ids = req.args.getlist('sel')
                    if not get_component_from_trac(self.env, req.args.get('name')) and p_ids:
                        self.smp_model.add(req.args.get('name'), p_ids)
                elif 'remove' in req.args:
                    # 'Remove' button on main component panel
                    self.smp_model.delete(req.args.getlist('sel'))
                elif 'save' in req.args:
                    # 'Save' button on 'Manage Component' panel
                    p_ids = req.args.getlist('sel')
                    self.smp_model.delete(req.args.get('path_info'))
                    self.smp_model.add_after_delete(req.args.get('name'), p_ids)
        return handler

    @staticmethod
    def _is_valid_request(req):
        """Check request for correct path and valid form token"""
        if req.path_info.startswith('/admin/ticket/components') \
                and req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    def post_process_request(self, req, template, data, content_type):

        if data and template == "admin_components.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            filter_list = []
            if not req.args.get('path_info'):
                # Main components page
                all_proj = { p_id: name for name, p_id in self.smp_project.get_name_and_id()}
                all_comp_proj = defaultdict(list)  # key is component name, value is a list of projects
                for comp, p_id in self.smp_model.get_all_components_and_project_id():
                    all_comp_proj[comp].append(u'<span>%s</span><br>' % all_proj[p_id])

                # The 'Add component' part of the page
                # xpath: //form[@id="addcomponent"]//div[@class="field"][2]
                xform = JTransformer('form#addcomponent div.field:nth-of-type(2)')
                filter_list.append(xform.after(create_projects_table_j(self, self._SmpModel, req)))

                # xpath: //table[@id="complist"]
                xform = JTransformer('table#complist')
                filter_list.append(xform.before('<p class="help">%s</p>' %
                                                _("A component is visible for all projects when not associated with "
                                                  "any project.")))
                # Add project column to component table. This is done with javascript
                column_data = {}
                for item in all_comp_proj:
                    column_data[item] = ''.join(all_comp_proj[item])
                add_script_data(req, {'smp_tbl_hdr': {'css': 'table#complist',
                                                      'html': '<th>%s</th>' % _("Restricted to Project")
                                                      },
                                      'smp_tbl_cols': column_data,
                                      'smp_td_class': 'project'
                                      })
                add_script(req, 'simplemultiproject/js/smp_insert_column.js')
            else:
                # 'Edit Component' panel
                # xform: //form[@id="modcomp" or @id="edit"]//div[@class="field"][1] where is modcomp used?
                # xform: //form[@id="edit"]//div[@class="field"][1]
                xform = JTransformer('form#edit div.field:nth-of-type(1)')
                filter_list.append(xform.after(create_projects_table_j(self, self._SmpModel, req)))

            if filter_list:
                add_script_data(req, {'smp_filter': filter_list})
                add_script(req, 'simplemultiproject/js/jtransform.js')

        return template, data, content_type
