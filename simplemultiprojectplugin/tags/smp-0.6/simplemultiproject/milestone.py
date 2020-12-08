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
from trac.web.chrome import ITemplateStreamFilter, add_stylesheet

from simplemultiproject.admin_filter import create_projects_table, \
    create_script_tag
from simplemultiproject.model import *
from simplemultiproject.smp_model import SmpProject, SmpMilestone


cur_projects_tmpl = """
<div xmlns:py="http://genshi.edgewall.org/" py:if="all_projects" style="overflow:hidden;">
<div id="project-help-div">
<p class="help">This milestone is connected to the following projects.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th>Project</th></tr>
    </thead>
    <tbody>
    <tr py:for="prj in all_projects">
        <td>${prj}</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>
"""


def create_cur_projects_table(smp_model, name):
    """Create a table holding projects for this milestone.

    @param smp_model: milestone model instance
    @param name: name of the milestone

    @return <div> tag holding a project select control with label
    """
    ms_projects = smp_model.get_project_names_for_item(name)
    tbl = MarkupTemplate(cur_projects_tmpl)
    return tbl.generate(all_projects=ms_projects)


class SmpMilestoneProject(Component):
    """Connect milestones to projects from the roadmap page."""

    implements(IRequestFilter, ITemplateStreamFilter, IMilestoneChangeListener)

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
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):

        if filename == 'milestone_edit.html':
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            if self.single_project:
                input_type = 'radio'
            else:
                input_type = "checkbox"  # Default input type for project selection.

            if not self.allow_no_project:
                stream |= Transformer('//head').append(create_script_tag(input_type=input_type))
                stream |= Transformer('//form[@id="edit"]//div[@class="buttons"]/input[not(@name)]') \
                          .attr('id', 'smp-btn-id')  # Add id for use from javascript
            filter_form = Transformer('//form[@id="edit"]//div[@class="field"][1]')
            stream |= filter_form.after(create_projects_table(self, self._SmpModel, req,
                                                              input_type=input_type,
                                                              item_name=data.get('milestone').name))
        elif filename == 'milestone_view.html':
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            filter_form = Transformer('//div[@class="info"]')
            stream |= filter_form.after(create_cur_projects_table(self.smp_model,
                                                                  data.get('milestone').name))
        return stream

    # IMilestoneChangeListener methods

    def milestone_created(self, milestone):
        pass

    def milestone_changed(self, milestone, old_values):
        pass

    def milestone_deleted(self, milestone):
        self.smp_model.delete(milestone.name)
