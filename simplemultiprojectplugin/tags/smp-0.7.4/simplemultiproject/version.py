# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering
# Copyright (C) falkb
# Copyright (C) 2021 Cinc
#

import re
from datetime import datetime, timedelta
from operator import itemgetter

from pkg_resources import get_distribution, parse_version, resource_filename
from trac.attachment import AttachmentModule
from trac.config import BoolOption, ExtensionOption
from trac.core import *
from trac.ticket.model import Version
from trac.perm import PermissionError
from trac.ticket.query import QueryModule
from trac.ticket.roadmap import ITicketGroupStatsProvider, apply_ticket_permissions, get_ticket_stats
from trac.web.chrome import ITemplateProvider, web_context
from trac.util.datefmt import get_datetime_format_hint, parse_date, user_time, utc
from trac.util.translation import _
from trac.web.api import IRequestHandler, IRequestFilter
from trac.web.chrome import add_notice, add_script, add_script_data, add_stylesheet, \
    add_warning, Chrome, INavigationContributor

from simplemultiproject.admin_filter import SmpFilterDefaultVersionPanels
from simplemultiproject.api import IRoadmapDataProvider
from simplemultiproject.compat import JTransformer
from simplemultiproject.milestone import create_projects_table_j
from simplemultiproject.model import *
from simplemultiproject.session import get_filter_settings, get_list_from_req_or_session
from simplemultiproject.smp_model import SmpProject, SmpVersion
from simplemultiproject.permission import SmpPermissionPolicy


def get_tickets_for_any(env, any_name, any_value, field='component'):
    fields = TicketSystem(env).get_ticket_fields()
    if field in [f['name'] for f in fields if not f.get('custom')]:
        query = """
            SELECT id,status,%s FROM ticket WHERE %s=%%s ORDER BY %s
            """ % (field, any_name, field)
        args = (any_value,)
    else:
        query = """
            SELECT id,status,value FROM ticket
            LEFT OUTER JOIN ticket_custom ON (id=ticket AND name=%%s)
            WHERE %s=%%s ORDER BY value
            """ % any_name
        args = (field, any_value)
    tickets = []
    for tkt_id, status, fieldval in env.db_query(query, args):
        tickets.append({'id': tkt_id, 'status': status, field: fieldval})
    return tickets


def any_stats_data(env, req, stat, any_name, any_value, grouped_by='component',
                   group=None):
    has_query = env[QueryModule] is not None

    def query_href(extra_args):
        if not has_query:
            return None
        args = {any_name: any_value, grouped_by: group, 'group': 'status'}
        args.update(extra_args)
        return req.href.query(args)

    return {
        'stats': stat,
        'stats_href': query_href(stat.qry_args),
        'interval_hrefs': [query_href(interval['qry_args'])
                           for interval in stat.intervals]
    }


def writeResponse(req, data, httperror=200, content_type='text/plain'):
    data=data.encode('utf-8')
    req.send_response(httperror)
    req.send_header('Content-Type', '%s; charset=utf-8' % content_type)
    req.send_header('Content-Length', len(data))
    req.end_headers()
    req.write(data)


class SmpVersionModule(Component):
    """Create Project dependent versions from the roadmap page."""

    implements(INavigationContributor, IRequestFilter, IRequestHandler, ITemplateProvider)

    stats_provider = ExtensionOption(
        'roadmap', 'stats_provider',
        ITicketGroupStatsProvider, 'DefaultTicketGroupStatsProvider',
        """Name of the component implementing `ITicketGroupStatsProvider`,
        which is used to collect statistics on groups of tickets for display
        in the roadmap views.
        """)

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

    # Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
    # creation using trac.util.html.tag and friends
    pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')

    def __init__(self):
        self.__SmpModel = None  # SmpModel(self.env)
        self.smp_model = SmpVersion(self.env)
        self.smp_project = SmpProject(self.env)  # For project select on edit page

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'roadmap'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/version(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['id'] = match.group(1)
            return True

    def process_request(self, req):
        version_id = req.args.get('id')

        action = req.args.get('action', 'view')
        try:
            version = Version(self.env, version_id)
        except:
            version = Version(self.env)
            version.name = version_id
            action = 'edit'  # rather than 'new' so that it works for POST/save

        if req.method == 'POST':
            if 'cancel' in req.args:
                if version.exists:
                    req.redirect(req.href.version(version.name))
                else:
                    req.redirect(req.href.roadmap())
            elif action == 'edit':
                return self._do_save(req, version)
            elif action == 'delete':
                self._do_delete(req, version)
        elif action in ('new', 'edit'):
            return self._render_editor(req, version)
        elif action == 'delete':
            return self._render_confirm(req, version)

        if not version.name:
            req.redirect(req.href.roadmap())

        return self._render_view(req, version)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        # Prevent opening of restricted versions
        if data and 'is_SMP' in data and \
                req.path_info.startswith('/version'):  # #12371
            version = data['version']
            if version and type(version) is Version:
                # This includes released projects
                all_prjs = SmpPermissionPolicy.apply_user_permissions(Project.select(self.env), req.perm)
                all_prjs = [p.id for p in all_prjs]
                ver_prjs = self.smp_model.get_project_ids_for_version(version.name)

                if ver_prjs and not (set(all_prjs) & set(ver_prjs)):
                    raise PermissionError()

        if data and template in ('version_edit.html', 'version_edit_jinja.html'):
            input_type = 'radio' if self.single_project else "checkbox"
            # Insert project selection control
            # xpath: //form[@id="edit"]//div[@class="field"][1]
            xform = JTransformer('form#edit div.field:nth-of-type(1)')
            version = data['version']
            filter_list = [xform.after(create_projects_table_j(self, req,
                                                                input_type=input_type, item_name=version.name))]
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")
            add_script_data(req, {'smp_filter': filter_list})
            add_script(req, 'simplemultiproject/js/jtransform.js')
        return template, data, content_type

    # Internal methods

    def _do_delete(self, req, version):
        req.perm.require('MILESTONE_DELETE')
        version_name = version.name
        version.delete()

        self.smp_model.delete(version_name)

        add_notice(req, _('The version "%(name)s" has been deleted.',
                          name=version_name))
        req.redirect(req.href.roadmap())

    def _do_save(self, req, version):
        version_name = req.args.get('name')
        version_project = req.args.getlist('sel')  # this is a list of ids
        old_version_project = self.smp_model.get_project_ids_for_version(version.name)  # this is a list

        if version.exists:
            req.perm.require('MILESTONE_MODIFY')
        else:
            req.perm.require('MILESTONE_CREATE')

        old_name = version.name
        new_name = version_name

        version.description = req.args.get('description', '')

        time = req.args.get('time', '')
        if time:
            version.time = user_time(req, parse_date, time, hint='datetime')
        else:
            version.time = None

        # Instead of raising one single error, check all the constraints and
        # let the user fix them by going back to edit mode showing the warnings
        warnings = []

        def warn(msg):
            add_warning(req, msg)
            warnings.append(msg)

        # -- check the name
        # If the name has changed, check that the version doesn't already
        # exist
        # FIXME: the whole .exists business needs to be clarified
        #        (#4130) and should behave like a WikiPage does in
        #        this respect.
        try:
            new_version = Version(self.env, new_name)
            if new_version.name == old_name:
                pass  # Creation or no name change
            elif new_version.name:
                warn(_('Version "%(name)s" already exists, please '
                       'choose another name.', name=new_version.name))
            else:
                warn(_('You must provide a name for the version.'))
        except:
            version.name = new_name

        if warnings:
            return self._render_editor(req, version)

        # -- actually save changes

        if version.exists:
            version.update()

            if old_name != version.name:
                self.smp_model.delete(old_name)
                self.smp_model.add(version.name, version_project)

            if not version_project:
                self.smp_model.delete(version.name)
            elif not old_version_project:
                self.smp_model.add(version.name, version_project)
            else:
                self.smp_model.add_after_delete(req.args.get('name'), version_project)
        else:
            version.insert()
            if version_project:
                self.smp_model.add(version.name, version_project)

        add_notice(req, _('Your changes have been saved.'))
        req.redirect(req.href.version(version.name))

    def _render_confirm(self, req, version):
        req.perm.require('MILESTONE_DELETE')

        data = {
            'version': version
        }
        add_stylesheet(req, 'common/css/roadmap.css')
        if self.pre_1_3:
            return 'version_delete.html', data, None
        else:
            return 'version_delete_jinja.html', data, {}

    def _render_editor(self, req, version):
        """Render the version edit page.
        :param req: Request object
        :param version: a Trac Version object
        """
        # Suggest a default due time of 18:00 in the user's timezone
        default_time = datetime.now(req.tz).replace(hour=18, minute=0, second=0,
                                                    microsecond=0)
        if default_time <= datetime.now(utc):
            default_time += timedelta(days=1)

        data = {
            'version': version,
            'datetime_hint': get_datetime_format_hint(),
            'default_time': default_time
        }

        if version.exists:
            req.perm.require('MILESTONE_MODIFY')
        else:
            req.perm.require('MILESTONE_CREATE')

        chrome = Chrome(self.env)
        chrome.add_jquery_ui(req)
        chrome.add_wiki_toolbars(req)

        add_stylesheet(req, 'common/css/roadmap.css')
        if self.pre_1_3:
            return 'version_edit.html', data, None
        else:
            return 'version_edit_jinja.html', data, {}

    def _render_view(self, req, version):
        version_groups = []
        available_groups = []
        component_group_available = False
        ticket_fields = TicketSystem(self.env).get_ticket_fields()

        # collect fields that can be used for grouping
        for field in ticket_fields:
            if field['type'] == 'select' and field['name'] != 'version' \
                    or field['name'] in ('owner', 'reporter'):
                available_groups.append({'name': field['name'],
                                         'label': field['label']})
                if field['name'] == 'component':
                    component_group_available = True

        # determine the field currently used for grouping
        by = None
        if component_group_available:
            by = 'component'
        elif available_groups:
            by = available_groups[0]['name']
        by = req.args.get('by', by)

        tickets = get_tickets_for_any(self.env, 'version', version.name, by)
        tickets = apply_ticket_permissions(self.env, req, tickets)
        stat = get_ticket_stats(self.stats_provider, tickets)

        context = web_context(req)

        infodivclass = 'info trac-progress'

        data = {
            'context': context,
            'version': version,
            'attachments': AttachmentModule(self.env).attachment_data(context),
            'available_groups': available_groups,
            'grouped_by': by,
            'groups': version_groups,
            'infodivclass': infodivclass,
            'is_SMP': True  # See #12371
        }
        data.update(any_stats_data(self.env, req, stat, 'version', version.name))

        if by:
            groups = []
            for field in ticket_fields:
                if field['name'] == by:
                    if 'options' in field:
                        groups = field['options']
                        if field.get('optional'):
                            groups.insert(0, '')
                    else:
                        groups = [row[0] for row in self.env.db_query("""
                                SELECT DISTINCT COALESCE(%s,'') FROM ticket
                                ORDER BY COALESCE(%s,'')
                                """, [by, by])]

            max_count = 0
            group_stats = []

            for group in groups:
                values = group and (group,) or (None, group)
                group_tickets = [t for t in tickets if t[by] in values]
                if not group_tickets:
                    continue

                gstat = get_ticket_stats(self.stats_provider, group_tickets)
                if gstat.count > max_count:
                    max_count = gstat.count

                group_stats.append(gstat)

                gs_dict = {'name': group}
                gs_dict.update(any_stats_data(self.env, req, gstat,
                                              'version', version.name, by, group))
                version_groups.append(gs_dict)

            for idx, gstat in enumerate(group_stats):
                gs_dict = version_groups[idx]
                percent = 1.0
                if max_count:
                    percent = float(gstat.count) / float(max_count) * 100
                gs_dict['percent_of_max_total'] = percent

        add_stylesheet(req, 'common/css/roadmap.css')
        add_script(req, 'common/js/folding.js')
        if self.pre_1_3:
            return 'version_view.html', data, None
        else:
            return 'version_view_jinja.html', data, {}

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('simplemultiproject', resource_filename(__name__, 'htdocs'))]


class SmpVersionRoadmap(Component):
    """Add version information to the roadmap page."""

    implements(IRequestFilter, IRequestHandler, IRoadmapDataProvider, ITemplateProvider)

    stats_provider = ExtensionOption(
        'roadmap', 'stats_provider',
        ITicketGroupStatsProvider, 'DefaultTicketGroupStatsProvider',
        """Name of the component implementing `ITicketGroupStatsProvider`,
        which is used to collect statistics on groups of tickets for display
        in the roadmap views.
        """)

    # Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
    # creation using trac.util.html.tag and friends
    pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')
    version_tmpl = None

    def __init__(self):
        self.smp_version = SmpVersion(self.env)
        # CSS class for milestones and versions
        self.infodivclass = 'info trac-progress'

    def _load_template(self):
        chrome = Chrome(self.env)
        if self.pre_1_3:
            self.version_tmpl = chrome.load_template("roadmap_versions.html", None)
        else:
            self.version_tmpl = chrome.load_template("roadmap_versions_jinja.html", False)

    def create_show_completed_label(self):
        show_completed_label = u"""<label for="showcompleted">{label}</label>"""
        return show_completed_label.format(label=_(u"Show completed milestones and versions"))

    def create_hide_version_item(self, req):
        prefs = """
        <div>
              <input type="hidden" name="smp_update" id="smp_update_version" value="1" />
              <input type="checkbox" id="hideversions" name="smp_hideversions" value="1"
                     {hideverchk} />
              <label for="hideversions">{hideverlabel}</label>
        </div>"""
        hideverchk = ' checked="checked"' if get_filter_settings(req, 'roadmap', 'smp_hideversions') else '',
        return prefs.format(hideverlabel=_('Hide versions'), hideverchk=hideverchk)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):

        if data:
            path_elms = req.path_info.split('/')
            if len(path_elms) > 1 and path_elms[1] == 'roadmap':
                # Add versions to page.
                # Only when not grouped. When grouped the version information is added in SmpRoadmapModule
                if not get_filter_settings(req, 'roadmap', 'smp_group'):
                    # The query string holds the preference settings. We need this so the script
                    # may get the correct data for display, e.g. completed versions
                    add_script_data(req, {'smp_query_string': req.query_string})
                    add_script(req, 'simplemultiproject/js/add_version_roadmap.js')

                # Add the "create new version" button
                if 'MILESTONE_CREATE' in req.perm:
                    add_script_data(req, {'smp_add_version': self.create_version_button(req)})
                    add_script(req, 'simplemultiproject/js/smp_add_version_button.js')

                filter_list = []
                # Change label to include versions
                # xpath: //label[@for="showcompleted"]
                xform = JTransformer('label[for=showcompleted]')
                filter_list.append(xform.replace(self.create_show_completed_label()))

                # Add preference checkbox
                xform = JTransformer('#prefs div.buttons')
                filter_list.append(xform.before(self.create_hide_version_item(req)))

                add_script_data(req, {'smp_ver_filter': filter_list})

        return template, data, content_type

    # IRequestHandler methods

    def match_request(self, req):
        if req.path_info == '/smpversionroadmap':
            return True

    def process_request(self, req):
        # Add versions to page
        # Roadmap group plugin is grouping by project
        if not get_filter_settings(req, 'roadmap', 'smp_group'):
            if not self.version_tmpl:
                self._load_template()

            chrome = Chrome(self.env)
            data = {'infodivclass': self.infodivclass,
                    'smp_add_version_data': True,  # Mark for add_data()
                    'smp_render': 'versions'}
            # Specify part of template to be rendered
            data = chrome.populate_data(req, data)
            # Add version data
            self.add_data(req, data)
            if self.pre_1_3:
                html = self.version_tmpl.generate(**data).render('html')
            else:
                html = chrome.render_template_string(self.version_tmpl, data)

            writeResponse(req, html, 200, 'text/html')

            return

    # IRoadmapDataProvider

    def add_project_info_to_versions(self, data):
        data['version_without_prj'] = False
        if data.get('versions'):
            for item in data.get('versions'):
                ids_for_ver = self.smp_version.get_project_ids_for_resource_item('version', item.name)
                if not ids_for_ver:
                    # Used in smp_roadmap.html to check if there is a version - proj link
                    item.id_project = []  # Versions without a project are for all
                    data['version_without_prj'] = True
                else:
                    item.id_project = ids_for_ver

    def add_data(self, req, data):

        # When not grouped the version information is added in process_request().
        # We must still make sure the data is added when grouped but called as part of IRoadmapDataProvider.
        #
        # To decide the var smp_add_version_data is used, which is added in process_request().
        # This way in case of grouping we don't process this method twice.
        if not get_filter_settings(req, 'roadmap', 'smp_group') and not data.get('smp_add_version_data'):
           return data

        hide = []
        if get_filter_settings(req, 'roadmap', 'smp_hideversions'):
            hide.append('versions')

        if data and (not hide or 'versions' not in hide):  # TODO: This clause must be revised
            projects = list(Project.select(self.env))  # select() is a generator
            versions, version_stats = \
                self._versions_and_stats(req, [prj.id for prj in SmpPermissionPolicy.apply_user_permissions(projects, req.perm)])
            data['versions'] = versions
            data['version_stats'] = version_stats
            self.add_project_info_to_versions(data)

        return data

    def filter_data(self, req, data):
        return data

    @staticmethod
    def _version_time(version):
        if version.time:
            return version.time.replace(tzinfo=None).strftime('%Y%m%d%H%M%S')
        else:
            return datetime(9999, 12, 31).strftime('%Y%m%d%H%M%S') + version.name

    def _versions_and_stats(self, req, user_projects):
        """

        :param req: Request object
        :param user_projects: list of allowed project ids for this user
        :return:
        """
        req.perm.require('MILESTONE_VIEW')

        versions = Version.select(self.env)

        filtered_versions = []
        stats = []

        show = get_list_from_req_or_session(req, 'roadmap', 'show', [])

        for version in sorted(versions, key=lambda v: self._version_time(v)):
            project_ids = self.smp_version.get_project_ids_for_version(version.name)
            version.due = None
            version.completed = None
            if not project_ids or (set(project_ids) & set(user_projects)):
                if not version.time or version.time.replace(tzinfo=None) >= datetime.now() or 'completed' in show:
                    if version.time:
                        if version.time.replace(tzinfo=None) >= datetime.now():
                            version.due = version.time
                        else:
                            version.completed = version.time

                    filtered_versions.append(version)
                    tickets = get_tickets_for_any(self.env, 'version',
                                                  version.name, 'owner')
                    tickets = apply_ticket_permissions(self.env, req, tickets)
                    stat = get_ticket_stats(self.stats_provider, tickets)
                    stats.append(any_stats_data(self.env, req, stat,
                                                'version', version.name))
        return filtered_versions, stats

    def create_version_button(self, req):
        add_version_button = u"""\
        <form id="add-version" method="get" action="{action_url}">
          <div>
            <input type="hidden" name="action" value="new" />
            <input type="submit" value="{label}" />
          </div>
        </form>
        """
        return add_version_button.format(label=_(u"Add new version"), action_url=req.href.version())

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('simplemultiproject', resource_filename(__name__, 'htdocs'))]


class SmpVersionPageObserver(Component):
    """Module to keep version information for projects up to date when
    SmpFilterDefaultVersionPanel is deactivated.
    """
    implements(IRequestFilter)

    def __init__(self):
        self.smp_model = SmpVersion(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if self._is_valid_request(req) and req.method == "POST":
            # Try to delete only if version page filter is disabled.
            # Deleting is usually done there.
            if not self.env.enabled[SmpFilterDefaultVersionPanels]:
                if 'remove' in req.args:
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
