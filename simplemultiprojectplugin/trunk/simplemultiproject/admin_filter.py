# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Cinc
#
# License: 3-clause BSD
#

from genshi.filters.transform import Transformer, InjectorTransformation
from genshi.template.markup import MarkupTemplate
from trac.config import BoolOption
from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket.model import Component as TicketComponent
from trac.ticket.model import Milestone, Version
from trac.ticket.api import IMilestoneChangeListener
from trac.util.html import html as tag
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateStreamFilter, add_script, \
    add_script_data, add_stylesheet

from simplemultiproject.model import SmpModel
from simplemultiproject.smp_model import SmpComponent, SmpProject, \
    SmpVersion, SmpMilestone


class InsertProjectTd(InjectorTransformation):
    """Transformation to insert the project column into the milestone
    and version tables
    """
    _value = None
    _td = 0

    def __init__(self, content, all_proj):
        self._all_proj = all_proj
        super(InsertProjectTd, self).__init__(content)

    def __call__(self, stream):

        for event in stream:
            mark, (kind, data, pos) = event

            if self._value:
                yield event  # Yield the event so the column is closed
                # Depending on the stream data may be '{http://www.w3.org/1999/xhtml}td' or just 'td'
                if mark == 'INSIDE' and kind == 'END' and data.endswith('td'):
                    # The end of a table column, tag: </td>
                    self._td += 1
                    if self._td == 2:
                        try:
                            # Special handling for components. A component may have several projects
                            if isinstance(self._all_proj[self._value], list):
                                self.content = tag.td(((tag.span(item), tag.br) for item in
                                                       self._all_proj[self._value]),
                                                      class_="project")
                            else:
                                self.content = tag.td(self._all_proj[self._value], class_="project")
                        except KeyError:
                            # We end up here when the milestone has no project yet
                            # self.content = tag.td(tag.span("(all projects)", style="color:lightgrey"))
                            self.content = tag.td(class_="project")
                        self._value = None
                        self._td = 0
                        for n, ev in self._inject():
                            yield 'INSIDE', ev
            else:
                if mark == 'INSIDE' and kind == 'START' and data[0].localname == 'input':
                    if data[1].get('type') == u"checkbox":
                        self._value = data[1].get('value') or data[1].get('name')
                        self._td = 0
                yield event


def create_script_tag(input_type="checkbox"):
    """Create javascript tag which holds code to enable/disable 'add'
    button for milestones.

    :param input_type:
    :return: javascript tag (Genshi)
    """
    script = """
    jQuery(document).ready(function($) {
        function anyChecked(){
            var any = false;
            $('#projectlist input:%s').each(function(){
                if (this.checked) {
                    any = true;
                };
            });
            return any;
        };
        if(!anyChecked())
        {
            $('#smp-btn-id').attr('disabled', 'disabled');
        };
        $('#projectlist input:%s').change(function() {
            if(!anyChecked()){
                $('#smp-btn-id').attr('disabled', 'disabled');
            }
            else{
                $('#smp-btn-id').removeAttr('disabled');
            };
        });
    });
    """
    return tag.script(script % (input_type, input_type),
                      type='text/javascript')


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

projects_tmpl = """
<div xmlns:py="http://genshi.edgewall.org/" id="smp-ms-sel-div" py:if="all_projects">
$proj
<select id="smp-project-sel">
    <option value="" selected="'' == sel_prj or None}">$all_label</option>
    <option py:for="prj in all_projects" value="$prj" selected="${prj == sel_prj or None}">$prj</option>
</select>
</div>
"""

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

    implements(ITemplateStreamFilter, IRequestFilter, IMilestoneChangeListener)

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
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):

        if filename == "admin_milestones.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            add_script(req, "simplemultiproject/js/filter_milestone_table.js")
            if self.single_project:
                input_type = 'radio'
            else:
                input_type = "checkbox"  # Default input type for project selection.
            if not req.args['path_info']:

                all_proj = {}
                for name, p_id in self.smp_project.get_name_and_id():
                    all_proj[p_id] = name

                all_ms_proj = {}
                for ms, p_id in self.smp_model.get_all_milestones_and_id_project_id():
                    try:
                        all_ms_proj[ms].append(all_proj[p_id])
                    except KeyError:
                        if p_id:
                            all_ms_proj[ms] = [all_proj[p_id]]
                        else:
                            # A milestone without a project
                            # For historical reasons these milestones
                            # may have a project id of '0' instead of
                            # missing from the SMP milestone table
                            all_ms_proj[ms] = [""]

                add_script_data(req, {'smp_proj_ms': all_ms_proj})
                # Add project column to main milestone table
                stream |= Transformer('//table[@id="millist"]//th[2]').after(tag.th(_("Project")))
                stream |= Transformer('//table[@id="millist"]//tr').apply(InsertProjectTd("", all_ms_proj))
                # Add select control with projects for hiding milestones
                sel = MarkupTemplate(projects_tmpl)
                all_proj = self.env.config.getlist('ticket-custom', 'project.options', sep='|')
                stream |= Transformer('//table[@id="millist"]').\
                   before(sel.generate(proj=_("Project"), all_projects=all_proj,
                                       sel_prj="", all_label=_("All")))
                # The 'add milestone' part of the page
                if not self.allow_no_project:
                    stream |= Transformer('//head').append(create_script_tag(input_type=input_type))
                    stream |= Transformer('//form[@id="addmilestone"]//input[@name="add"]') \
                              .attr('id', 'smp-btn-id')  # Add id for use from javascript

                # The 'Add milestone' part of the page
                filter_form = Transformer('//form[@id="addmilestone"]//div[@class="field"][1]')
                stream |= filter_form.after(create_projects_table(self, self._SmpModel, req,
                                                                          input_type=input_type))
            else:
                # 'Modify Milestone' panel
                if not self.allow_no_project:
                    stream |= Transformer('//head').append(create_script_tag(input_type=input_type))
                    stream |= Transformer('//form[@id="modifymilestone"]//input[@name="save"]') \
                              .attr('id', 'smp-btn-id')  # Add id for use from javascript
                filter_form = Transformer('//form[@id="modifymilestone" or @id="edit"]//div[@class="field"][1]')
                stream |= filter_form.after(create_projects_table(self, self._SmpModel, req,
                                                                          input_type=input_type))
        return stream

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

    implements(ITemplateStreamFilter, IRequestFilter)

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
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == "admin_versions.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            add_script(req, "simplemultiproject/js/filter_version_table.js")
            if self.single_project:
                input_type = 'radio'
            else:
                input_type = "checkbox"  # Default input type for project selection.
            if not req.args['path_info']:
                all_proj = {}
                for name, p_id in self.smp_project.get_name_and_id():
                    all_proj[p_id] = name

                all_ver_proj = {}
                for ver, p_id in self.smp_model.get_all_versions_and_project_id():
                    try:
                        all_ver_proj[ver].append(all_proj[p_id])
                    except KeyError:
                        # A version without a project
                        all_ver_proj[ver] = [all_proj[p_id]]
                add_script_data(req, {'smp_proj_ver': all_ver_proj})
                # Add project column to main version table
                stream |= Transformer('//table[@id="verlist"]//th[2]').after(tag.th(_("Project")))
                stream |= Transformer('//table[@id="verlist"]//tr').apply(InsertProjectTd("", all_ver_proj))

                sel = MarkupTemplate(projects_tmpl)
                all_proj = self.env.config.getlist('ticket-custom', 'project.options', sep='|')
                stream |= Transformer('//table[@id="verlist"]'). \
                    before(sel.generate(proj=_("Project"), all_projects=all_proj,
                                        sel_prj="", all_label=_("All")))

                # The 'add version' part of the page
                if not self.allow_no_project:
                    stream |= Transformer('//head').append(create_script_tag(input_type=input_type))
                    stream |= Transformer('//form[@id="addversion"]//input[@name="add"]') \
                              .attr('id', 'smp-btn-id')  # Add id for use from javascript
                # Insert project selection control
                filter_form = Transformer('//form[@id="addversion"]//div[@class="field"][1]')
                stream |= filter_form.after(create_projects_table(self, self._SmpModel, req,
                                                                          input_type=input_type))

                # Remove current date/time as release date otherwise the version will be filtered on the roadmap.
                # User probably forgets to change it on creation and would be surprised not finding it.
                stream |= Transformer('//form[@id="addversion"]//input[@id="releaseddate"]').attr("value", '')
            else:
                # 'Modify versions' panel
                if not self.allow_no_project:
                    stream |= Transformer('//head').append(create_script_tag(input_type=input_type))
                    stream |= Transformer('//form[@id="modifyversion"]//input[@name="save"]') \
                              .attr('id', 'smp-btn-id')  # Add id for use from javascript
                filter_form = Transformer('//form[@id="modifyversion" or @id="edit"]//div[@class="field"][1]')
                stream |= filter_form.after(create_projects_table(self, self._SmpModel, req,
                                                                  input_type=input_type))
        return stream


table_tmpl = """
<div xmlns:py="http://genshi.edgewall.org/"  style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
 restrictions are imposed.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr py:for="prj in all_projects">
        <td class="name">
            <input name="sel" value="${prj[0]}"
                   py:attrs="{'checked': 'checked'} if prj[1] in comp_prj else {}" type="$input_type" />
        </td>
        <td>${prj[1]}</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>
"""


def create_projects_table(self, _SmpModel, req, input_type='checkbox',
                          item_name=''):
    """Create a table for admin panels holding valid projects (means not closed).

    @param self: Component instance filtering an admin page
    @param _SmpModel: SmpModel object
    @param req      : Trac request object

    @return DIV tag holding a project select control with label
    """
    # project[0] is the id, project[1] the name
    all_projects = [[project[0], project[1]]
                    for project in self.smp_project.get_all_projects()]
    all_project_names = [name for p_id, name in all_projects]

    # no closed projects
    for project_name in list(all_project_names):
        project_info = _SmpModel.get_project_info(project_name)
        _SmpModel.filter_project_by_conditions(all_project_names, project_name,
                                               project_info, req)

    filtered_projects = [[p_id, project_name]
                         for p_id, project_name in all_projects
                         if project_name in all_project_names]

    item = req.args.get('path_info', "")
    if not item:
        item = item_name
    comp_prj = self.smp_model.get_project_names_for_item(item)
    tbl = MarkupTemplate(table_tmpl)
    return tbl.generate(all_projects=filtered_projects, comp_prj=comp_prj,
                        input_type=input_type)


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
    implements(ITemplateStreamFilter, IRequestFilter)

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
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == "admin_components.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            if not req.args['path_info']:
                # Main components page
                all_proj = {}
                for name, p_id in self.smp_project.get_name_and_id():
                    all_proj[p_id] = name
                all_comp_proj = {}  # key is component name, value is a list of projects
                for comp, p_id in self.smp_model.get_all_components_and_project_id():
                    try:
                        all_comp_proj[comp].append(all_proj[p_id])
                    except KeyError:
                        # Component is not in dict 'all_comp_proj' yet
                        # all_comp_proj[comp] = all_proj[p_id]
                        all_comp_proj[comp] = [all_proj[p_id]]

                # The 'Add component' part of the page
                filter_form = Transformer('//form[@id="addcomponent"]//div[@class="field"][2]')
                stream |= filter_form.after(create_projects_table(self, self._SmpModel, req))

                stream |= Transformer('//table[@id="complist"]').before(
                    tag.p(_("A component is visible for all projects when not associated with any project."),
                          class_="help"))
                # Add project column to component table
                stream |= Transformer('//table[@id="complist"]//th[2]').\
                    after(tag.th(_("Restricted to Project")))
                stream |= Transformer('//table[@id="complist"]//tr').apply(InsertProjectTd("", all_comp_proj))
            else:
                # 'Manage Component' panel
                filter_form = Transformer('//form[@id="modcomp" or @id="edit"]//div[@class="field"][1]')
                stream |= filter_form.after(create_projects_table(self, self._SmpModel, req))
        return stream
