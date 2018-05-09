# -*- coding: utf-8 -*-

from trac.config import ListOption
from trac.core import Component, TracError, implements
from trac.perm import IPermissionPolicy, IPermissionRequestor
from trac.wiki.model import WikiPage


class PrivateWikiPolicy(Component):
    """Central tasks for the PrivateWiki plugin."""

    implements(IPermissionRequestor, IPermissionPolicy)

    wikis = ListOption('privatewikis', 'private_wikis', default='Private',
                       doc='Wikis to protect.')

    # IPermissionPolicy methods

    def check_permission(self, action, username, resource, perm):
        if resource is not None and \
                resource.realm == 'wiki'and \
                resource.id is not None and \
                action in ('WIKI_VIEW', 'WIKI_MODIFY', 'WIKI_CREATE'):
            wiki = WikiPage(self.env, resource.id)
            return self.check_wiki_access(perm, resource, action, wiki.name)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        view_actions = ['PRIVATE_VIEW_' + a for a in self.wikis]
        edit_actions = ['PRIVATE_EDIT_' + a for a in self.wikis]
        return view_actions + edit_actions + \
            [('PRIVATE_VIEW_ALL', view_actions),
             ('PRIVATE_EDIT_ALL', edit_actions + view_actions)]

    def _prep_page(self, page):
        return page.upper().replace('/', '_')

    def _protected_page(self, page):
        page = self._prep_page(page)
        member_of = []
        for base_page in self.wikis:
            if page.startswith(base_page + '_') or page == base_page:
                member_of.append(base_page)
        return member_of

    # Public methods

    def check_wiki_access(self, perm, res, action, page):
        """Return if this req is permitted access/modify/create a given
        wiki page.
        """
        try:
            page = self._prep_page(page)
            member_of = self._protected_page(page)
            if not member_of:
                return
            for p in member_of:
                view_perm = 'PRIVATE_VIEW_%s' % p
                edit_perm = 'PRIVATE_EDIT_%s' % p
                if action == 'WIKI_VIEW':
                    if perm and ('PRIVATE_ALL_VIEW' in perm(res) or
                                 view_perm in perm(res) or
                                 edit_perm in perm(res)):
                        return True

                elif action in ('WIKI_MODIFY', 'WIKI_CREATE'):
                    if perm and ('PRIVATE_ALL_EDIT' in perm(res) or
                                 edit_perm in perm(res)):
                        return True
        except TracError:
            return

        return False
