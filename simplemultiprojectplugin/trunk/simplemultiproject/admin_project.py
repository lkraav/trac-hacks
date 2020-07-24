# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#

from pkg_resources import resource_filename, get_distribution, parse_version
from simplemultiproject.smp_model import SmpProject
from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.resource import IResourceManager, Resource, ResourceNotFound
from trac.util.translation import _
from trac.web.chrome import add_script, ITemplateProvider

class SmpProjectAdmin(Component):

    implements(IAdminPanelProvider, IResourceManager, ITemplateProvider)

    # Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
    # creation using trac.util.html.tag and friends
    pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')


    def __init__(self):
        self.smp_project = SmpProject(self.env)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'PROJECT_SETTINGS_VIEW_TEST' in req.perm('projects'):
            yield ('projects', _('Manage Projects'),
                   'projects', _("Projects_"))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('PROJECT_SETTINGS_VIEW')

        if req.method == 'POST':
            if req.args.get('add'):
                pass
                #self.config.set(section, key, val)
                #self.config.save()
            elif req.args.get('remove'):
                pass
                #self.config.remove(workflow, key)
                #self.config.save()
            elif req.args.get('save'):
                pass
                #self.config.save()
            req.redirect(req.href.admin(cat, page))

        # GET, show admin page
        data = {'all_projects': self.smp_project.get_all_projects()}
        if not path_info:
            data.update({'view': 'list', 'name': 'default'})
        else:
            data.update({'view': 'detail',
                         'name': path_info,
                         })

        add_script(req, 'common/js/resizer.js')
        if self.pre_1_3:
            return 'admin_project.html', data
        else:
            return 'admin_project_j.html', data, {}

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
