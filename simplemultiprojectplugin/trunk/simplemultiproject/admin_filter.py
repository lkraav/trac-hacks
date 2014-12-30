# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Cinc
#

# Trac extension point imports
from trac.core import *
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.util.translation import _
from trac.config import BoolOption
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

def _create_script_tag():
    """Create javascript tag which holds code to enable/disable 'add' button for milestones.

    :return: javascript tag (Genshi)
    """
    script = """
    jQuery(document).ready(function($) {
        if($('#project_id').val()=='0'){
                $('#smp-btn-id').attr('disabled', 'disabled');
            };

        $('#project_id').change(function() {
            if($('#project_id').val()=='0'){
                $('#smp-btn-id').attr('disabled', 'disabled');
            }
            else{
                $('#smp-btn-id').removeAttr('disabled');
            };
        });
    });
    """
    return tag.script(script, type='text/javascript')

def create_projects_select_ctrl(smp_model, req, for_add=True, is_ver=False):
    """Create a select control for admin panels holding valid projects (means not closed).

    @param smp_model: SmpModel object
    @param req      : Trac request object
    @param is_ver   : Control is used while modifying/adding a version

    @return DIV tag holding a project select control with label
    """
    all_projects_id = [[project[0], project[1]] for project in sorted(smp_model.get_all_projects(),
                                                                      key=itemgetter(1))]
    all_projects = [name for p_id, name in all_projects_id]

    # no closed projects
    for project_name in all_projects:
        project_info = smp_model.get_project_info(project_name)
        smp_model.filter_project_by_conditions(all_projects, project_name, project_info, req)

    filtered_projects = [[p_id, project_name] for p_id, project_name in all_projects_id
                         if project_name in all_projects]

    cur_project = 0
    select = tag.select(name="project_id", id="project_id", style="margin-bottom:10px;")

    # Note that 'path_info' is not None only when modifying projects
    if is_ver:
        id_project = smp_model.get_id_project_version(req.args['path_info'])
    else:
        id_project = smp_model.get_id_project_milestone(req.args['path_info'])

    if id_project:
        cur_project = id_project[0]

    if not cur_project:
        select.append(tag.option(_("Please, choose a project"), value=0))

    for project_id, project_name in filtered_projects:
        if cur_project and project_id == cur_project:
            select.append(tag.option(project_name, value=project_id, selected="selected"))
        else:
            select.append(tag.option(project_name, value=project_id))

    div = tag.div(tag.label(_("Project")+':', tag.br, select), class_="field")
    return div

class SmpFilterDefaultMilestonePanels(Component):
    """Modify default Trac admin panels for milestones to include a project selection control.

    [[br]]
    Using this component you may associate a milestone with a project using the default Trac admin panels.

    Creation of milestones is only possible when a project is chosen. You may disable this behaviour by setting the
    following in ''trac.ini'':

    {{{
    [simple-multi-project]
    allow_no_project = True
    }}}
    """

    BoolOption("simple-multi-project", "allow_no_project", False, doc="Set this option to {{{True}}} if you want to "
                                                                      "create milestones without associated projects. "
                                                                      "The default value is {{{False}}}.")
    implements(ITemplateStreamFilter, IRequestFilter)

    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):

        if self._is_valid_request(req) and req.method == "POST":
            if 'project_id' in req.args and req.args['project_id'] != u"0" and req.args['name']:
                if 'add' in req.args:
                    self.__SmpModel.insert_milestone_project(req.args['name'], req.args['project_id'])
                elif 'save' in req.args:
                    if self.__SmpModel.get_id_project_milestone(req.args['path_info']):
                        # req.args['path_info'] holds the old name. req.args['name'] holds the modified name.
                        self.__SmpModel.update_milestone_project(req.args['path_info'], req.args['project_id'])
                    else:
                        # If there is no project id this milestone doesn't live in the smp_milestone_project table yet
                        self.__SmpModel.insert_milestone_project(req.args['path_info'], req.args['project_id'])

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
                        # A milestone without a project
                        all_ms_proj[ms] = ""

                stream = stream | Transformer('//table[@id="millist"]//tr').apply(InsertProjectTd("", all_ms_proj))

                # The 'add milestone' part of the page
                if not self._allow_no_project():
                    stream = stream | Transformer('//head').append(_create_script_tag())\
                                    | Transformer('//form[@id="addmilestone"]//input[@name="add"]'
                                                ).attr('id', 'smp-btn-id') # Add id for use from javascript

                # Insert project selection control
                filter_form = Transformer('//form[@id="addmilestone"]//div[@class="field"][1]')
                stream = stream | filter_form.after(create_projects_select_ctrl(self.__SmpModel, req))
            else:
                # 'Modify Milestone' panel
                if not self._allow_no_project():
                    stream = stream | Transformer('//head').append(_create_script_tag()) \
                                    | Transformer('//form[@id="modifymilestone"]//input[@name="save"]'
                                                ).attr('id', 'smp-btn-id') # Add id for use from javascript

                # Insert project selection control
                filter_form = Transformer('//form[@id="modifymilestone"]//div[@class="field"][1]')
                stream = stream | filter_form.after(create_projects_select_ctrl(self.__SmpModel, req))

        return stream

    def _allow_no_project(self):
        """Check config if user enabled milestone creation without prior selection of a project.

        @return: True if milestones may be created without a project
        """
        return self.env.config.getbool("simple-multi-project", "allow_no_project", False)

class SmpFilterDefaultVersionPanels(Component):
    """Modify default Trac admin panels for versions to include project selection."""

    implements(ITemplateStreamFilter, IRequestFilter)

    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):

        if self._is_valid_request(req) and req.method == "POST":
            if 'project_id' in req.args and req.args['project_id'] != u"0" and req.args['name']:
                if 'add' in req.args:
                    self.__SmpModel.insert_version_project(req.args['name'], req.args['project_id'])
                elif 'save' in req.args:
                    if self.__SmpModel.get_id_project_version(req.args['path_info']):
                        # req.args['path_info'] holds the old name. req.args['name'] holds the modified name.
                        self.__SmpModel.update_version_project(req.args['path_info'], req.args['project_id'])
                    else:
                        # If there is no project id this milestone doesn't live in the smp_milestone_project table yet
                        self.__SmpModel.insert_version_project(req.args['path_info'], req.args['project_id'])

        return handler

    def _is_valid_request(self, req):
        """Check request fir cirrect path and valid form token"""
        if req.path_info.startswith('/admin/ticket/versions') and req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    def post_process_request(self, req, template, data, content_type):

        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):

        if filename == "admin_versions.html":
            if not req.args['path_info']:
                # Add project column to main version table
                stream = stream | Transformer('//table[@id="verlist"]//th[@class="sel"]').after(tag.th(_("Project")))

                all_proj={}
                for dat in self.__SmpModel.get_all_projects():
                    all_proj[dat[0]] = dat[1]

                all_ver_proj={}
                for ver, p_id in self.__SmpModel.get_all_versions_with_id_project():
                    try:
                        all_ver_proj[ver] = all_proj[p_id]
                    except KeyError:
                        # A version without a project
                        all_ver_proj[ver] = ""

                stream = stream | Transformer('//table[@id="verlist"]//tr').apply(InsertProjectTd("", all_ver_proj))

                # The 'add version' part of the page
                if not self._allow_no_project():
                    stream = stream | Transformer('//head').append(_create_script_tag())\
                                    | Transformer('//form[@id="addversion"]//input[@name="add"]'
                                                ).attr('id', 'smp-btn-id') # Add id for use from javascript

                # Insert project selection control
                filter_form = Transformer('//form[@id="addversion"]//div[@class="field"][1]')
                stream = stream | filter_form.after(create_projects_select_ctrl(self.__SmpModel, req))
                # Remove current date/time as release date otherwise the version will be filtered on the roadmap.
                # User probably forgets to change it on creation and would be surprised not finding it.
                stream = stream | Transformer('//form[@id="addversion"]//input[@id="releaseddate"]').attr("value", '')
            else:
                # 'Modify versions' panel
                filter_form = Transformer('//form[@id="modifyversion"]//div[@class="field"][1]')
                stream = stream | filter_form.after(create_projects_select_ctrl(self.__SmpModel, req, is_ver=True))

        return stream

    def _allow_no_project(self):
        """Check config if user enabled milestone creation without prior selection of a project.

        @return: True if milestones may be created without a project
        """
        return self.env.config.getbool("simple-multi-project", "allow_no_project", False)
