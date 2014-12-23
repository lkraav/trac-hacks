# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Cinc
#

# Trac extension point imports
from trac.core import *
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.util.translation import _

# genshi
from genshi.builder import tag
from genshi.filters.transform import Transformer, InjectorTransformation

from operator import itemgetter

# Model Class
from model import SmpModel

__author__ = 'Cinc'


class InsertProjectTd(InjectorTransformation):
    """Transformation to insert the project column into the milestone table"""
    _value = None

    def __init__(self, content, all_proj):
        self._all_ms_proj = all_proj
        super(InsertProjectTd, self).__init__(content)

    def __call__(self, stream):

        for event in stream:
            mark, (kind, data, pos) = event

            if self._value:
                yield event # Yield the event so the column is closed
                if mark == 'INSIDE' and kind == 'END' and data == '{http://www.w3.org/1999/xhtml}td':
                    # The end of a table column, tag: </td>
                    try:
                        self.content = tag.td(self._all_ms_proj[self._value])
                    except KeyError:
                        # We end up here when the milestone has no project yet
                        self.content = tag.td()

                    self._value = None
                    for n, ev in self._inject():
                        yield 'INSIDE', ev
            else:
                if mark == 'INSIDE' and kind == 'START' and data[0].localname == 'input':
                    if data[1].get('type') ==u"checkbox":
                        self._value = data[1].get('value')
                yield event

class SmpFilterDefaultMilestonePanels(Component):
    """Modify default Trac admin panels for milestones to include project selection."""

    implements(ITemplateStreamFilter, IRequestFilter)

    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):

        if self._is_valid_request(req) and req.method == "POST":
            if 'add' in req.args:
                if 'project_id' in req.args and req.args['project_id'] != 0:
                    self.__SmpModel.insert_milestone_project(req.args['name'], req.args['project_id'])
            elif 'save' in req.args:
                self.__SmpModel.update_milestone_project(req.args['path_info'], req.args['project_id'])

        return handler

    def _is_valid_request(self, req):
        """Check request for correct path and valid form token"""
        if req.path_info.startswith('/admin/ticket/milestones') and req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    def post_process_request(self, req, template, data, content_type):

        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):

        if filename == "admin_milestones.html":
            if not req.args['path_info']:
                # Add project column to main milestone table
                stream = stream | Transformer('//table[@id="millist"]//th[@class="sel"]').after(tag.th(_("Project")))

                all_proj={}
                for dat in self.__SmpModel.get_all_projects():
                    all_proj[dat[0]] = dat[1]

                all_ms_proj={}
                for ms, p_id in self.__SmpModel.get_all_milestones_with_id_project():
                    try:
                        all_ms_proj[ms] = all_proj[p_id]
                    except KeyError:
                        all_ms_proj[ms] = ""

                stream = stream | Transformer('//table[@id="millist"]//tr').apply(InsertProjectTd("", all_ms_proj))

                # The 'add milestone' part of the page
                filter_form = Transformer('//form[@id="addmilestone"]//div[@class="field"][1]')
                stream = stream | filter_form.after(self._create_projects_select_ctrl(req, True))
                # Add id for use from javascript
                filter_id = Transformer('//form[@id="addmilestone"]//input[@name="add"]')
                stream = stream | filter_id.attr('id', 'add_btn').attr('disabled', 'disabled')
                filter_script = Transformer('//head')
                stream = stream | filter_script.append(self._create_script_tag())
            else:
                # 'Modify Milestone' panel
                filter_form = Transformer('//form[@id="modifymilestone"]//div[@class="field"][1]')
                stream = stream | filter_form.after(self._create_projects_select_ctrl(req, False))

        return stream

    def _create_script_tag(self):
        """Create javascript tag which holds code to enable/disable 'add' button for milestones.

        :return: javascript tag (Genshi)
        """
        script = """
        jQuery(document).ready(function($) {

            $('#project_id').change(function() {
                if($('#project_id').val()=='0'){
                    $('#add_btn').attr('disabled', 'disabled');
                }
                else{
                    $('#add_btn').removeAttr('disabled');
                };
            });
        });
        """
        return tag.script(script, type='text/javascript')

    def _create_projects_select_ctrl(self, req, for_add=True):
        all_projects_id = [[project[0], project[1]] for project in sorted(self.__SmpModel.get_all_projects(),
                                                                          key=itemgetter(1))]
        all_projects = [name for p_id, name in all_projects_id]

        # no closed projects
        for project_name in all_projects:
            project_info = self.__SmpModel.get_project_info(project_name)
            self.__SmpModel.filter_project_by_conditions(all_projects, project_name, project_info, req)

        filtered_projects = [[p_id, project_name] for p_id, project_name in all_projects_id
                             if project_name in all_projects]

        cur_project = None
        select = tag.select(name="project_id", id="project_id", style="margin-bottom:10px;")
        if for_add:
            select.append(tag.option(_("Please choose a project"), value=0))
        else:
            # Note that 'path_info' is not None only when modifying projects
            cur_project = self.__SmpModel.get_id_project_milestone(req.args['path_info'])[0]

        for project_id, project_name in filtered_projects:
            if cur_project and project_id == cur_project:
                select.append(tag.option(project_name, value=project_id, selected="selected"))
            else:
                select.append(tag.option(project_name, value=project_id))

        div = tag.div(tag.label(_("Project")+':', tag.br, select), class_="field")
        return div
