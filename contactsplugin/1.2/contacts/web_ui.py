# -*- coding: utf-8 -*-

import re
from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.util.html import tag
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider, add_script, add_stylesheet)

from model import Contact, ContactIterator


class ContactsAdminPanel(Component):
    """Pages for adding/editing contacts."""

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler,
               ITemplateProvider)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'contacts'

    def get_navigation_items(self, req):
        if 'CONTACTS_VIEW' in req.perm('contacts'):
            yield ('mainnav', 'contacts', tag.a(_('Contacts'),
                   href=req.href.contacts()))

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('contacts', resource_filename('contacts', 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename('contacts', 'templates')]

    # IRequestHandler methods

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        if re.match(r'^/contact', req.path_info):
            return True

    def process_request(self, req):
        req.perm('contacts').require('CONTACTS_VIEW')

        add_stylesheet(req, 'common/css/admin.css')
        if re.match(r'^/contacts$', req.path_info):
            return ('contacts.html', {
                'contacts': ContactIterator(self.env),
                'can_edit': 'CONTACTS_ADMIN' in req.perm('contacts')
            }, None)

        req.perm('contacts').require('CONTACTS_ADMIN')

        params = req.path_info.split('/')
        contact_id = None
        if len(params) > 2 and params[2].isdigit():
            contact_id = params[2]
        contact = Contact(self.env, contact_id)

        if req.method == 'POST' and 'addcontact' in req.args:
            contact.update_from_req(req)
            contact.save()
            if 'redirect' in req.args:
                req.redirect(req.href.contacts(contact.id))
            else:
                req.redirect(req.href.contacts())

        template = {'contact': contact}
        if len(params) > 2 and params[2].isdigit():
            add_script(req, 'contacts/edit_contact.js')
            add_stylesheet(req, 'contacts/edit_contact.css')
            template['title'] = 'Edit %s' % contact.last_first()
            template['edit'] = True
        else:
            template['title'] = 'Add Contact'
            template['edit'] = False
        if 'redirect' in req.args:
            template['redirect'] = req.args.get('redirect')
        else:
            template['redirect'] = None

        return 'contact.html', template, None

    # IPermissionRequest methods

    def get_permission_actions(self):
        return ['CONTACTS_VIEW', ('CONTACTS_ADMIN', ['CONTACTS_VIEW'])]
