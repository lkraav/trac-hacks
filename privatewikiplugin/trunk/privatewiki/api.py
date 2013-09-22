# -*- coding: utf-8 -*-

from trac.config import IntOption, ListOption
from trac.core import *
from trac.perm import IPermissionRequestor, IPermissionGroupProvider, \
                      IPermissionPolicy, PermissionSystem
from trac.util.compat import set
from trac.wiki.model import WikiPage

__all__ = ['PrivateWikiSystem']


class PrivateWikiSystem(Component):
    """Central tasks for the PrivateWiki plugin."""

    implements(IPermissionRequestor, IPermissionPolicy)

    group_providers = ExtensionPoint(IPermissionGroupProvider)

    wikis = ListOption('privatewikis', 'private_wikis', default='Private',
                       doc='Wikis to protect.')

    # IPermissionPolicy(Interface)
    def check_permission(self, action, username, resource, perm):
        log_msg = 'Checking permission called with: action(%s), \
                   username(%s), resource(%s), perm(%s)'
        log_msg_vars = (str(action), str(username), str(resource), str(perm))
        self.env.log.debug(log_msg % log_msg_vars)
        
        if resource is None or resource.id is None:
            return None

        if username == 'anonymous' and resource.realm == 'wiki':
            wiki = WikiPage(self.env, resource.id)
            page = self._prep_page(wiki.name)
            if self._protected_page(page):
                return False

        if (resource.realm == 'wiki' 
            and action in ('WIKI_VIEW', 
                           'WIKI_MODIFY', 
                           'WIKI_CREATE')):
            wiki = WikiPage(self.env, resource.id)
            return self.check_wiki_access(perm, resource, action, wiki.name)
        return None

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
        self.env.log.debug('Checking privacy of page %s' % (page))
        page = self._prep_page(page)
        member_of = []
        for base_page in self.wikis:
            if page.startswith(base_page + '_') or page == base_page:
                member_of.append(base_page)

        self.env.log.debug('Privacy check results %s' % str(member_of))
        return member_of

    # Public methods
    def check_wiki_access(self, perm, res, action, page):
        """Return if this req is permitted access/modify/create a given wiki page."""

        try:
            page = self._prep_page(page)
            self.env.log.debug('Now checking for %s on %s' % (action, page))
            member_of = self._protected_page(page)
            if not member_of:
                self.env.log.debug('%s is not a private page' % page)
                return None
            for p in member_of:
                self.env.log.debug('Checking protected area: %s' % p)
                view_perm = 'PRIVATE_VIEW_%s' % p;
                edit_perm = 'PRIVATE_EDIT_%s' % p;

                self.env.log.debug('Attempting to protect against %s' % action)
                
                if action == 'WIKI_VIEW':
                    if ('PRIVATE_ALL_VIEW' in perm(res)
                        or view_perm in perm(res)
                        or edit_perm in perm(res)):

                        self.env.log.debug('--Can VIEW')
                        return True

                elif action in ('WIKI_MODIFY', 'WIKI_CREATE'):
                    if ('PRIVATE_ALL_EDIT' in perm(res)
                        or edit_perm in perm(res)):

                        self.env.log.debug('--Can MODIFY or CREATE')
                        return True

        except TracError:
            return None

        return False

