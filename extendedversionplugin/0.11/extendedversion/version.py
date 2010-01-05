"""
ExtendedVersionTracPlugin:
Extend versions in trac
Plugin for trac:  http://trac.edgewall.org
See also:  http://trac-hacks.org
"""

import pkg_resources
import re

from genshi.builder import tag

from trac.attachment import AttachmentModule
from trac.core import *
from trac.mimeview.api import Context
from trac.resource import Resource, ResourceNotFound
from trac.ticket import Milestone, Version
from trac.util.datefmt import get_datetime_format_hint, parse_date
from trac.util.translation import _
from trac.web.chrome import add_link, add_notice, add_stylesheet, add_warning

### interfaces:  
from trac.attachment import ILegacyAttachmentPolicyDelegate
from trac.perm import IPermissionPolicy, IPermissionRequestor
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.wiki.api import IWikiSyntaxProvider


class VisibleVersion(Component):
    implements(ILegacyAttachmentPolicyDelegate, INavigationContributor, IPermissionRequestor,
            IRequestHandler, ITemplateProvider, IWikiSyntaxProvider)

    # ILegacyAttachmentPolicyDelegate methods

    def check_attachment_permission(self, action, username, resource, perm):
        if resource.parent.realm != 'version':
            print "declined"
            return

        if action == 'ATTACHMENT_CREATE':
            action = 'VERSION_MODIFY'
        elif action == 'ATTACHMENT_VIEW':
            action = 'VERSION_VIEW'
        elif action == 'ATTACHMENT_DELETE':
            action = 'VERSION_DELETE'

        decision = action in perm(resource.parent)
        if not decision:
            self.env.log.debug('ExtendedVersionTracPlugin denied %s '
                               'access to %s. User needs %s' %
                              (username, resource, legacy_action))
        return decision

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'roadmap'

    def get_navigation_items(self, req):
        return []

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['VERSION_CREATE', 'VERSION_DELETE', 'VERSION_MODIFY',
                   'VERSION_VIEW']
        return actions + [('VERSION_ADMIN', actions)]

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
       return []

    def get_templates_dirs(self):
       return [pkg_resources.resource_filename('extendedversion', 'templates')]

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/version(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['id'] = match.group(1)
            return True

    def process_request(self, req):
        version_id = req.args.get('id')
        req.perm('version', version_id).require('VERSION_VIEW')
        
        #add_link(req, 'up', req.href.roadmap(), _('Roadmap'))

        db = self.env.get_db_cnx() # TODO: db can be removed
        version = Version(self.env, version_id, db)
        action = req.args.get('action', 'view')

        if req.method == 'POST':
            if req.args.has_key('cancel'):
                if version.exists:
                    req.redirect(req.href.version(version.name))
                else:
                    req.redirect(req.href.roadmap())
            elif action == 'edit':
                return self._do_save(req, db, version)
            elif action == 'delete':
                self._do_delete(req, db, version)
        elif action in ('new', 'edit'):
            return self._render_editor(req, db, version)
        elif action == 'delete':
            return self._render_confirm(req, db, version)

        if not version.name:
            req.redirect(req.href.roadmap())

        return self._render_view(req, db, version)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('version', self._format_link)

    # Internal methods

    def _do_delete(self, req, db, version):
        name = version.name
        resource = Resource('version', version.name)
        req.perm(resource).require('VERSION_DELETE')

        version.delete(db=db)
        db.commit()
        add_notice(req, _('The version "%(name)s" has been deleted.',
                          name=name))
        req.redirect(req.href.roadmap())

    def _do_save(self, req, db, version):
        resource = Resource('version', version.name)
        if version.exists:
            req.perm(resource).require('VERSION_MODIFY')
        else:
            req.perm(resource).require('VERSION_CREATE')

        old_name = version.name
        new_name = req.args.get('name')
        
        version.name = new_name
        version.description = req.args.get('description', '')

        time = req.args.get('time', '')

        # Instead of raising one single error, check all the constraints and
        # let the user fix them by going back to edit mode showing the warnings
        warnings = []
        def warn(msg):
            add_warning(req, msg)
            warnings.append(msg)

        # -- check the name
        if new_name:
            if new_name != old_name:
                # check that the version doesn't already exists
                # FIXME: the whole .exists business needs to be clarified
                #        (#4130) and should behave like a WikiPage does in
                #        this respect.
                try:
                    other_version = Version(self.env, new_name, db)
                    warn(_('Version "%(name)s" already exists, please '
                           'choose another name', name=new_name))
                except ResourceNotFound:
                    pass
        else:
            warn(_('You must provide a name for the version.'))

        # -- check completed date
        if 'time' in req.args:
            time = time and parse_date(time, req.tz) or None
        else:
            time = None
        version.time = time

        if warnings:
            return self._render_editor(req, db, version)
        
        # -- actually save changes
        if version.exists:
            version.update()
        else:
            version.insert()
        db.commit()

        req.redirect(req.href.version(version.name))

    def _format_link(self, formatter, ns, name, label):
        name, query, fragment = formatter.split_link(name)
        return self._render_link(formatter.context, name, label,
                                 query + fragment)

    def _render_confirm(self, req, db, version):
        resource = Resource('version', version.name)
        req.perm(resource).require('VERSION_DELETE')

        data = {
            'version': version,
        }
        return 'version_delete.html', data, None

    def _render_editor(self, req, db, version):
        resource = Resource('version', version.name)
        data = {
            'version': version,
            'resource': resource,
            'versions': [ver.name for ver in Version.select(self.env)],
            'datetime_hint': get_datetime_format_hint(),
            'version_groups': [],
        }

        if version.exists:
            req.perm(resource).require('VERSION_MODIFY')
            #versions = [m for m in Version.select(self.env, db=db)
            #              if m.name != version.name
            #              and 'VERSION_VIEW' in req.perm(m.resource)]
        else:
            req.perm(resource).require('VERSION_CREATE')

        return 'version_edit.html', data, None

    def _render_link(self, context, name, label, extra=''):
        try:
            version = Version(self.env, name)
        except TracError:
            version = None
        # Note: the above should really not be needed, `Milestone.exists`
        # should simply be false if the milestone doesn't exist in the db
        # (related to #4130)
        href = context.href.version(name)
        if version and version.exists:
            resource = Resource('version', name)
            if 'VERSION_VIEW' in context.perm(resource):
                return tag.a(label, class_='version', href=href + extra)
        elif 'VERSION_CREATE' in context.perm('version', name):
            return tag.a(label, class_='missing version', href=href + extra,
                         rel='nofollow')
        return tag.a(label, class_='missing version')
        
    def _render_view(self, req, db, version):

        db = self.env.get_db_cnx()
        sql = "SELECT name,due,completed,description FROM milestone " \
              "INNER JOIN milestone_version ON (name = milestone) " \
              "WHERE version = %s " \
              "ORDER BY name "
        cursor = db.cursor()
        cursor.execute(sql, (version.name,))
        milestones = []
        for row in cursor:
            milestone = Milestone(self.env)
            milestone._from_database(row)
            milestones.append(milestone)

        resource = Resource('version', version.name)
        context = Context.from_request(req, resource)
        data = {
            'context': context,
            'resource': resource,
            'version': version,
            'milestones': milestones,
            'attachments': AttachmentModule(self.env).attachment_data(context),
            }

        return 'version_view.html', data, None

