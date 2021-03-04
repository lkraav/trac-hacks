# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2021 Cinc
#
# License: 3-clause BSD
#
from collections import defaultdict
from pkg_resources import resource_filename
from trac.config import BoolOption
from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket.model import Component as TicketComponent
from trac.ticket.model import Milestone, Version
from trac.ticket.api import IMilestoneChangeListener
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, \
    add_script_data, add_stylesheet, ITemplateProvider

from simplemultiproject.compat import JTransformer
from simplemultiproject.milestone import create_projects_table_j
from simplemultiproject.smp_model import SmpComponent, SmpProject, \
    SmpVersion, SmpMilestone


class SmpFilterBase(Component):
    """Must be activated when any of the admin filter components is used."""

    implements(ITemplateProvider)

    # The following are verridden in subclass
    # TODO: this is not used yet
    template_name = ""  # name of html file
    add_form_id = ''  # id of form used to add a new item on main admin page
    table_id = ''  # id of table holding all the items. Is used to hide/show rows and add columns with javascript

    allow_no_project = False
    single_project = False

    def __init__(self):
        self.smp_project = SmpProject(self.env)

    # ITemplateProvider methods

    def get_templates_dirs(self):
        self.log.info(resource_filename(__name__, 'templates'))
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('simplemultiproject', resource_filename(__name__, 'htdocs'))]

    @staticmethod
    def is_valid_request(req, path):
        """Check request for correct path and valid form token"""
        if req.path_info.startswith('/admin/ticket/%s' % path) \
                and req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    @staticmethod
    def create_project_select_ctrl(all_proj):
        div_templ = u"""<div id="smp-ms-sel-div">
    {proj}
    <select id="smp-project-sel">
        <option value="" selected>{all_label}</option>{options}
    </select>
    </div>"""
        options_templ = u"""<option value="{prj}">{prj}</option>"""

        options = u''
        for prj in all_proj:
            options += options_templ.format(prj=prj)

        return div_templ.format(proj=_("Project"), all_projects=all_proj, sel_prj="", all_label=_("All"),
                                options=options)

    def handle_item_admin_page(self, req, prj_per_item, table_id, form_id):
        """Handle the main admin page for milestones and versions

        :param self: self
        :param req: Request object
        :param table_id: id of table holding the items (milestone, version, ...)
        :param form_id: id of form used for adding anew item

        :return: None
        """
        all_proj = {p_id: name for name, p_id in self.smp_project.get_name_and_id()}

        # Note:
        # A milestone without a project may have for historical reasons
        # a project id of '0' instead of missing from the SMP milestone table
        all_item_proj = defaultdict(list)
        all_item_proj_2 = defaultdict(list)
        for ms, p_id in prj_per_item:
            all_item_proj_2[ms].append((u'<span>%s</span><br>' % all_proj[p_id]) if p_id else '')
            all_item_proj[ms].append(all_proj[p_id] if p_id else '')

        add_script_data(req, {'smp_proj_per_item': all_item_proj})

        # Add project column to main version table
        column_data = {}
        for item in all_item_proj_2:
            column_data[item] = ''.join(all_item_proj_2[item])

        add_script_data(req, {'smp_tbl_hdr': {'css': 'table#%s' % table_id,
                                              'html': '<th>%s</th>' % _("Restricted to Project")
                                              },
                              'smp_tbl_cols': column_data,
                              'smp_td_class': 'project',
                              'smp_tbl_selector': '#%s' % table_id
                              })
        add_script(req, 'simplemultiproject/js/smp_insert_column.js')

        filter_list = []
        # Add select control with projects for hiding rows of the table
        known_proj = [name for name, p_id in self.smp_project.get_name_and_id()]
        xform = JTransformer('table#%s' % table_id)
        filter_list.append(xform.before(SmpFilterBase.create_project_select_ctrl(known_proj)))

        # The 'add milestone' part of the page
        input_type = 'radio' if self.single_project else "checkbox"

        # Insert project selection control
        # xpath: //form[@id="addmilestone"]//div[@class="field"][1]
        xform = JTransformer('form#%s div.field:nth-of-type(1)' % form_id)
        filter_list.append(xform.after(create_projects_table_j(self, req,
                                                               input_type=input_type)))
        if filter_list:
            add_script_data(req, {'smp_filter': filter_list})
            add_script(req, 'simplemultiproject/js/jtransform.js')

        # disable button script must be inserted at the end.
        if not self.allow_no_project:
            add_script_data(req, {'smp_input_control': '#projectlist input:' + input_type,
                                  'smp_submit_btn': 'form#%s input[name=add]' % form_id})
            add_script(req, 'simplemultiproject/js/disable_submit_btn.js')

        add_script(req, "simplemultiproject/js/filter_table.js")

    def handle_item_edit_page(self, req):
        """Handle the admin pages for milestone and version edit

        :param self: component
        :param req: Request object

        :returns None
        """
        # "checkbox" is default input type for project selection.
        input_type = 'radio' if self.single_project else "checkbox"

        # Insert project selection control
        # xpath: //form[@id="edit"]//div[@class="field"][1]
        xform = JTransformer('form#edit div.field:nth-of-type(1)')
        filter_list = [xform.after(create_projects_table_j(self, req, input_type=input_type))]

        add_script_data(req, {'smp_filter': filter_list})
        add_script(req, 'simplemultiproject/js/jtransform.js')

        # disable button script must be inserted at the end.
        if not self.allow_no_project:
            add_script_data(req, {'smp_input_control': '#projectlist input:' + input_type,
                                  'smp_submit_btn': 'form#edit input[name=save]'})
            add_script(req, 'simplemultiproject/js/disable_submit_btn.js')


class SmpFilterDefaultMilestonePanels(SmpFilterBase):
    """Modify default Trac admin panels for milestones to include
    project selection.

    With this component you may associate a milestone with one or more
    projects using the default Trac admin panels.

    ''Note: Make sure to also enable the component **!SmpMilestoneProject**.''
    === Configuration
    Creation of milestones is only possible when a project is chosen.
    You may change this behaviour by setting the following in ''trac.ini'':

    {{{#!ini
    [simple-multi-project]
    milestone_without_project = True
    }}}

    To ensure only a single project is associated with each milestone
    set the following in ''trac.ini'':
    {{{#!ini
    [simple-multi-project]
    single_project_milestones = True
    }}}

    There is also a configuration panel available for this. Go to **Manage Projects** / [[/admin/smproject/basics|Basic Settings]].
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
        super(SmpFilterDefaultMilestonePanels, self).__init__()
        self.smp_model = SmpMilestone(self.env)

    @staticmethod
    def get_milestone_from_trac(env, name):
        try:
            return Milestone(env, name)
        except ResourceNotFound:
            return None

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if SmpFilterDefaultMilestonePanels.is_valid_request(req, 'milestones') and req.method == "POST":
            if req.path_info.startswith('/admin/ticket/milestones'):
                # Removal is handled in change listener
                if 'add' in req.args:
                    # 'Add' button on main milestone panel
                    # Check if we already have this milestone.
                    # Trac will show an error later if so.
                    # Don't change the db for smp if already exists.
                    p_ids = req.args.getlist('sel')
                    if not SmpFilterDefaultMilestonePanels.get_milestone_from_trac(self.env, req.args.get('name')) \
                            and p_ids:
                        # Note this one handles lists and single ids
                        self.smp_model.add(req.args.get('name'), p_ids)  # p_ids may be a list here
                elif 'save' in req.args:
                    # 'Save' button on 'Manage milestone' panel
                    p_ids = req.args.getlist('sel')
                    self.smp_model.delete(req.args.get('path_info'))
                    # Note this one handles lists and single ids
                    self.smp_model.add_after_delete(req.args.get('name'), p_ids)
        return handler

    def post_process_request(self, req, template, data, content_type):
        if data and template == "admin_milestones.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")

            if not req.args['path_info']:
                prj_per_item = self.smp_model.get_all_milestones_and_id_project_id()
                self.handle_item_admin_page(req, prj_per_item, 'millist', 'addmilestone')
            else:
                self.handle_item_edit_page(req)

        return template, data, content_type

    # IMilestoneChangeListener methods

    def milestone_created(self, milestone):
        pass

    def milestone_changed(self, milestone, old_values):
        pass

    def milestone_deleted(self, milestone):
        self.smp_model.delete(milestone.name)


class SmpFilterDefaultVersionPanels(SmpFilterBase):
    """Modify default Trac admin panels for versions to include project selection.

    With this component you may link a version with one or more
    projects using the default Trac admin panels.

    === Configuration
    Creation of versions is only possible when a project is chosen.
    You may disable this behaviour by setting the
    following in ''trac.ini'':

    {{{#!ini
    [simple-multi-project]
    version_without_project = True
    }}}

    To ensure only a single project is associated with each version set
    the following in ''trac.ini'':
    {{{#!ini
    [simple-multi-project]
    single_project_versions = True
    }}}

    There is also a configuration panel available for this. Go to **Manage Projects** / [[/admin/smproject/basics|Basic Settings]].
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
        super(SmpFilterDefaultVersionPanels, self).__init__()
        self.smp_model = SmpVersion(self.env)

    @staticmethod
    def get_version_from_trac(env, name):
        try:
            return Version(env, name)
        except ResourceNotFound:
            return None

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if SmpFilterDefaultVersionPanels.is_valid_request(req, 'versions') and req.method == "POST":
            if req.path_info.startswith('/admin/ticket/versions'):
                if 'add' in req.args:
                    # 'Add' button on main version panel
                    # Check if we already have this version.
                    # Trac will show an error later if so.
                    # Don't change the db for smp if it already exists.
                    p_ids = req.args.getlist('sel')
                    if not SmpFilterDefaultVersionPanels.get_version_from_trac(self.env, req.args.get('name')) \
                            and p_ids:
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

    def post_process_request(self, req, template, data, content_type):
        if data and template == "admin_versions.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")

            if not req.args['path_info']:
                prj_per_item = self.smp_model.get_all_versions_and_project_id()
                self.handle_item_admin_page(req, prj_per_item, 'verlist', 'addversion')
            else:
                # 'Modify versions' panel
                self.handle_item_edit_page(req)

        return template, data, content_type

# TODO: use the base class SmpFilterBase here
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
    implements(IRequestFilter, ITemplateProvider)

    # TODO: When using a base class this may go away
    allow_no_project = True
    single_project = False

    def __init__(self):
        self.smp_model = SmpComponent(self.env)
        self.smp_project = SmpProject(self.env)

    @staticmethod
    def is_valid_request(req, path):
        """Check request for correct path and valid form token"""
        if req.path_info.startswith('/admin/ticket/%s' % path) \
                and req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    @staticmethod
    def get_component_from_trac(env, name):
        try:
            return TicketComponent(env, name)
        except ResourceNotFound:
            return None

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if SmpFilterDefaultComponentPanels.is_valid_request(req, 'components') and req.method == 'POST':
            if req.path_info.startswith('/admin/ticket/components'):
                if 'add' in req.args:
                    # 'Add' button on main component panel
                    # Check if we already have this component.
                    # Trac will show an error later if so.
                    # Don't change the db for smp.
                    p_ids = req.args.getlist('sel')
                    if not SmpFilterDefaultComponentPanels.get_component_from_trac(self.env, req.args.get('name')) \
                            and p_ids:
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

    def post_process_request(self, req, template, data, content_type):

        if data and template == "admin_components.html":
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            filter_list = []
            if not req.args.get('path_info'):
                # Main components page
                all_proj = {p_id: name for name, p_id in self.smp_project.get_name_and_id()}
                all_comp_proj = defaultdict(list)  # key is component name, value is a list of projects
                for comp, p_id in self.smp_model.get_all_components_and_project_id():
                    all_comp_proj[comp].append(u'<span>%s</span><br>' % all_proj[p_id])

                # The 'Add component' part of the page
                # xpath: //form[@id="addcomponent"]//div[@class="field"][2]
                xform = JTransformer('form#addcomponent div.field:nth-of-type(2)')
                filter_list.append(xform.after(create_projects_table_j(self,  req)))

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
                filter_list.append(xform.after(create_projects_table_j(self, req)))

            if filter_list:
                add_script_data(req, {'smp_filter': filter_list})
                add_script(req, 'simplemultiproject/js/jtransform.js')

        return template, data, content_type

    # ITemplateProvider methods

    def get_templates_dirs(self):
        self.log.info(resource_filename(__name__, 'templates'))
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('simplemultiproject', resource_filename(__name__, 'htdocs'))]
