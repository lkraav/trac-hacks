# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: BSD
#

from genshi.filters import Transformer
from genshi.template.markup import MarkupTemplate
from trac.config import BoolOption
from trac.core import Component, implements
from trac.ticket.api import IMilestoneChangeListener
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet

from simplemultiproject.compat import JTransformer
from simplemultiproject.model import *
from simplemultiproject.smp_model import SmpProject, SmpMilestone


table_tmpl = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
 restrictions are imposed.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>{tr}
    </tbody>
</table>
</div>
<div></div>
</div>"""
tr_templ = u"""<tr>
        <td class="name">
            <input name="sel" value="{p_id}" type="{input_type}"{sel}>
        </td>
        <td>{p_name}</td>
    </tr>"""

def create_projects_table_j(self, _SmpModel, req, input_type='checkbox',
                          item_name=''):
    """Create a table for admin panels holding valid projects (means not closed).

    @param self: Component with 'self.smp_project = SmpProject(self.env)'
    @param _SmpModel: SmpModel object
    @param req      : Trac request object
    @param input_type: either 'checkbox' or 'radio'. Allows single or multiple paroject selection
    @param item_name: name of the milestone currently edited

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

    # This different tr initialization is for now so Genshi output and string format output are identical for the tests
    if filtered_projects:
        tr = u"\n    "
    else:
        tr = u""
    for prj in filtered_projects:
        sel = ' checked' if prj[1] in comp_prj else ''
        tr += tr_templ.format(p_id=prj[0], p_name=prj[1], input_type=input_type, sel=sel)

    return table_tmpl.format(tr=tr)


def create_cur_projects_table(smp_model, name):
    """Create a table holding projects for this milestone.

    @param smp_model: milestone model instance
    @param name: name of the milestone

    @return <div> tag holding a project select control with label. If name is 'None' or '' return ''.
    """
    cur_project_tmpl = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">This milestone is connected to the following projects.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th>Project</th></tr>
    </thead>
    <tbody>
    {tr}
    </tbody>
</table>
</div>
<div></div>
</div>"""

    cur_tr_templ = u"""<tr>
        <td>{p_name}</td>
    </tr>"""

    ms_projects = smp_model.get_project_names_for_item(name)

    if not ms_projects:
        return ''

    tr = ''
    for prj in ms_projects:
       tr += cur_tr_templ.format(p_name=prj)

    return cur_project_tmpl.format(tr=tr)


class SmpMilestoneProject(Component):
    """Connect milestones to projects from the roadmap page."""

    implements(IRequestFilter, IMilestoneChangeListener)

    single_project = BoolOption(
        'simple-multi-project', 'single_project_milestones', False,
        doc="""If set to {{{True}}} only a single project can be associated
               with a milestone. The default value is {{{False}}}.
               """)

    allow_no_project = BoolOption(
        'simple-multi-project', 'milestone_without_project', False,
        doc="""Set this option to {{{True}}} if you want to create milestones
               without associated projects. The default value is {{{False}}}.
               """)

    def __init__(self):
        self._SmpModel = SmpModel(self.env)
        self.smp_model = SmpMilestone(self.env)
        self.smp_project = SmpProject(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if self._is_valid_request(req) and not req.args.get('cancel'):
            action = req.args.get('action', 'view')
            # Deletion of milestones is handled in IMilestoneChangeListener
            if action == 'edit':
                # This one may be a new one or editing of an existing milestone
                ms_id = req.args.get('id')  # holds the old name if there was a name change, empty if new
                p_ids = req.args.getlist('sel')
                if not ms_id:
                    self.smp_model.add(req.args.get('name'), p_ids)
                else:
                    self.smp_model.delete(ms_id)
                    self.smp_model.add(req.args.get('name'), p_ids)
        return handler

    @staticmethod
    def _is_valid_request(req):
        """Check request for correct path and valid form token"""
        if req.path_info.startswith('/milestone') and \
                req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    def post_process_request(self, req, template, data, content_type):

        if data and template == 'milestone_edit.html':
            # 'new Milestone' or 'edit milestone' page opened from the roadmap page
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            if self.single_project:
                input_type = 'radio'
            else:
                input_type = "checkbox"  # Default input type for project selection.

            # xpath: //form[@id="edit"]//div[@class="field"][1]
            xform = JTransformer('form#edit div.field:nth-of-type(1)')
            filter_list = [xform.after(create_projects_table_j(self, self._SmpModel, req,
                                                            input_type=input_type,
                                                            item_name=data.get('milestone').name))]
            add_script_data(req, {'smp_filter': filter_list})
            add_script(req, 'simplemultiproject/js/jtransform.js')

            # disable button script must be inserted last.
            if not self.allow_no_project:
                add_script_data(req, {'smp_input_control': '#projectlist input:' + input_type,
                                      'smp_submit_btn': 'form#edit input[name=save]'
                                      if req.args.get('action') == 'edit'
                                      else 'form#edit input[name=add]'})
                add_script(req, 'simplemultiproject/js/disable_submit_btn.js')
        elif data and template == 'milestone_view.html':
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")

            # xpath: //div[contains(@class, "info")]
            xform = JTransformer('div.info')
            filter_list = [xform.after(create_cur_projects_table(self.smp_model,
                                                                 data.get('milestone').name))]
            add_script_data(req, {'smp_filter': filter_list})
            add_script(req, 'simplemultiproject/js/jtransform.js')

        return template, data, content_type

    # IMilestoneChangeListener methods

    def milestone_created(self, milestone):
        pass

    def milestone_changed(self, milestone, old_values):
        pass

    def milestone_deleted(self, milestone):
        self.smp_model.delete(milestone.name)
