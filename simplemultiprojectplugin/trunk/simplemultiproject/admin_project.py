# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 Cinc
#
# License: 3-clause BSD
#

from pkg_resources import resource_filename, get_distribution, parse_version
from simplemultiproject.smp_model import PERM_TEMPLATE, SmpProject
from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.resource import IResourceManager, Resource, ResourceNotFound
from trac.ticket.model import TicketSystem
from trac.util.datefmt import datetime_now, get_datetime_format_hint, parse_date,\
    to_utimestamp, user_time, utc
from trac.util.translation import _
from trac.web.chrome import add_notice, add_script, add_warning, Chrome, ITemplateProvider

class SmpProjectAdmin(Component):
    """Manage projects and configure global settings.


    """

    implements(IAdminPanelProvider, IResourceManager, ITemplateProvider)

    # Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
    # creation using trac.util.html.tag and friends
    pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')

    def __init__(self):
        self.smp_project = SmpProject(self.env)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'PROJECT_SETTINGS_VIEW' in req.perm('projects'):
            yield ('smproject', _('Manage Projects'),
                   'projects', _("Projects"))
            excl_mark = '' if self.ticket_custom_field_exists() else ' (!)'
            yield ('smproject', _('Manage Projects'),
                   'basics', _("Basic Settings") + excl_mark)

    def check_project_name(self, req, projects):
        name = req.args.get('name', None)
        if name:
            for project in projects:
                if name == project.name:
                    add_warning(req, _('Project name "%s" already exists.') % project.name)
                    return False
        else:
            add_warning(req, _("You need to provide a project name."))
            return False
        return True

    def ticket_custom_field_exists(self):
        """Check if the ticket custom field 'project' is configured.

        :returns None if not configured, otherwise the field type

        Note that we have to check the config here. 'TicketSystem(self.env).fields' does not hold
        the custom field until 'project.options' has some value.

        We don't check for proper custom field type here.
        """
        return self.config.get('ticket-custom', 'project', None)

    def render_basics_panel(self, req, cat, page, path_info):
        policies = self.config.get('trac', 'permission_policies')
        data = {'custom_field': self.ticket_custom_field_exists(),
                'allow_no_prj_ms': self.config.getbool('simple-multi-project', 'milestone_without_project', False),
                'single_prj_ms': self.config.getbool('simple-multi-project', 'single_project_milestones', False),
                'allow_no_prj_ver': self.config.getbool('simple-multi-project', 'version_without_project', False),
                'single_prj_ver': self.config.getbool('simple-multi-project', 'single_project_versions', False),
                'permission_policy': 'SmpPermissionPolicy' in policies,
                'permission_list': policies,
                }

        # data.update({})

        if req.method == 'POST':
            req.perm.require("PROJECT_ADMIN")

            if req.args.get('create-ticket-custom'):
                self.config.set('ticket-custom', 'project', 'select')
                self.config.set('ticket-custom', 'project.label', _('Project'))
                self.config.set('ticket-custom', 'project.value', None)
                self.config.set('ticket-custom', 'project.options', None)
                self.config.save()
                add_notice(req, "The ticket custom field 'project' was added to the configuration.")
            elif req.args.get('save-ms'):
                if req.args.get('cb-single-prj-ms'):
                    self.config.set('simple-multi-project', 'single_project_milestones', 'enabled')
                else:
                    self.config.set('simple-multi-project', 'single_project_milestones', 'disabled')
                if req.args.get('cb-allow-no-prj-ms'):
                    self.config.set('simple-multi-project', 'milestone_without_project', 'enabled')
                else:
                    self.config.set('simple-multi-project', 'milestone_without_project', 'disabled')
                self.config.save()
                add_notice(req, "The configuration for milestones was saved.")
            elif req.args.get('save-ver'):
                if req.args.get('cb-single-prj-ver'):
                    self.config.set('simple-multi-project', 'single_project_versions', 'enabled')
                else:
                    self.config.set('simple-multi-project', 'single_project_versions', 'disabled')
                if req.args.get('cb-allow-no-prj-ver'):
                    self.config.set('simple-multi-project', 'version_without_project', 'enabled')
                else:
                    self.config.set('simple-multi-project', 'version_without_project', 'disabled')
                self.config.save()
                add_notice(req, "The configuration for versions was saved.")
            elif req.args.get('save-permission-policy'):
                pols = req.args.get('permission-policies')
                self.config.set('trac', 'permission_policies', pols)
                self.config.save()
                add_notice(req, "The following permission policies were saved: %s", pols)
            req.redirect(req.href.admin(cat, page))

        if self.pre_1_3:
            return 'admin_smp_basics.html', data
        else:
            return 'admin_smp_basics_jinja.html', data

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('PROJECT_SETTINGS_VIEW')

        if page == 'basics':
            return self.render_basics_panel(req, cat, page, path_info)

        name = req.args.get('name', None)
        summary = req.args.get('summary', None)
        description = req.args.get('description', None)
        restricted = req.args.get('restricted', None)
        sel = req.args.getlist('sel')
        projects = self.smp_project.get_all_projects()

        def add_project_warning_and_redirect():
            add_warning(req, _("Project '%s' does not exist or you don't have the necessary permission "
                               "to access it."), path_info)
            req.redirect(req.href.admin(cat, page))

        # Prevent users from directly accessing projects or guessing project names
        if path_info:
            for project in projects:
                if path_info == project.name:
                    if project.restricted and not req.perm.has_permission(PERM_TEMPLATE % project.id):
                        add_project_warning_and_redirect()
                    break
            else:
                add_project_warning_and_redirect()

        if req.method == 'POST':
            req.perm.require("PROJECT_ADMIN")

            def redirect_with_parms():
                req.redirect(req.href.admin(cat, page, name=name, summary=summary,
                                            description=description, restricted=restricted))
            if req.args.get('add'):
                # Check name
                if not self.check_project_name(req, projects):
                    redirect_with_parms()

                # Add new project
                self.smp_project.add(name, summary, description, None, 'YES' if restricted else None)
                # update internal caches
                self.smp_project.get_all_projects()
                self.config.save()  # See #12524
                add_notice(req, _('The project "%s" has been added.') % name)
                self.log.info('SMP - The project "%s" has been added.' % name)
            elif req.args.get('remove'):
                self.smp_project.delete(sel)
                self.smp_project.get_all_projects()
                self.config.save()  # See #12524
                add_notice(req, _('The selected projects have been removed.'))
                self.log.info("SMP - The project(s) %s have been removed" % sel)
            elif req.args.get('save'):
                # TODO: we lose all changes with this redirect
                old_name = req.args.get('old_name')
                project_id = req.args.get('project_id', 0)
                if name != old_name and not self.check_project_name(req, projects):
                    req.redirect(req.href.admin(cat, page, path_info))

                if 'completed' in req.args:
                    completed = req.args.get('completeddate', '')
                    completed = user_time(req, parse_date, completed,
                                          hint='datetime') if completed else None
                    if completed and completed > datetime_now(utc):
                        add_warning(req, _('Completion date may not be in the future'))
                else:
                    completed = None
                # to_utimestamp(None) gives 0 which is a valid time. For not completed
                # projects we want to have None in the database instead. So we convert to utimestamp only
                # when there is a real completeddate.
                if completed:
                    completed = to_utimestamp(completed)
                self.smp_project.update(project_id, name, summary, description,
                                        completed, 'YES' if restricted else None)

                self.smp_project.get_all_projects()
                self.config.save()  # See #12524
            req.redirect(req.href.admin(cat, page))

        # GET, show admin page
        user_projects = self.smp_project.apply_user_restrictions(projects, req.authname)
        data = {'all_projects': user_projects}
        if not path_info:
            # The main pages
            data.update({'view': 'list',
                         'name': name,
                         'summary': summary,
                         'description': description,
                         'restricted': restricted,
                         'custom_field': self.ticket_custom_field_exists()
                         })
        else:
            for project in user_projects:
                if project.name == path_info:
                    data.update({'project': project,
                                 'view': 'detail',
                                 'datetime_hint': get_datetime_format_hint(req.lc_time)
                                 })
                    break
            Chrome(self.env).add_wiki_toolbars(req)

        add_script(req, 'common/js/resizer.js')
        if self.pre_1_3:
            return 'admin_project.html', data
        else:
            return 'admin_project_jinja.html', data

    # IResourceManager methods

    def get_resource_url(self, resource, href, **kwargs):
        """Return the canonical URL for displaying the given resource.

        :param resource: a `Resource`
        :param href: an `Href` used for creating the URL

        Note that if there's no special rule associated to this realm for
        creating URLs (i.e. the standard convention of using realm/id applies),
        then it's OK to not define this method.
        """

    def get_resource_realms(self):
        yield 'project'

    def get_resource_description(self, resource, format=None, context=None,
                                 **kwargs):
        desc = unicode(resource.id)
        if resource.realm == 'project':
            if format == 'compact':
                return 'project:%s' % resource.id
            else:
                return 'Project %s' % resource.id
        return ""

    def resource_exists(self, resource):
        db = self.env.get_read_db()
        cursor = db.cursor()
        if resource.realm == 'project':
            # TODO: use method in SmpProject here
            cursor.execute("SELECT * FROM peerreview WHERE project_id = %s", (resource.id,))
            if cursor.fetchone():
                return True
            else:
                return False

        raise ResourceNotFound('Resource %s not found.' % resource.realm)

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('simplemultiproject', resource_filename(__name__, 'htdocs'))]
