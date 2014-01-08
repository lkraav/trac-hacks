# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Michael Renzmann <mrenzmann@otaku42.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag

from trac.config import ListOption
from trac.core import Component, ExtensionPoint, implements
from trac.web.chrome import INavigationContributor


class NavAdd(Component):
    """ Allows to add items to main and meta navigation bar"""
    implements(INavigationContributor)

    nav_items = ListOption('navadd', 'add_items',
                           doc="Items that will be added to the navigation")

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return ''

    def get_navigation_items(self, req):
        items = []
        for name in self.nav_items:
            title = self.env.config.get('navadd', '%s.title' % name)
            href = self.env.config.get('navadd', '%s.url' % name)
            perm = self.env.config.get('navadd', '%s.perm' % name)
            target = self.env.config.get('navadd', '%s.target' % name)

            if perm and not req.perm.has_permission(perm):
                continue

            if target not in ('mainnav', 'metanav'):
                target = 'mainnav'

            if not href.startswith(('http://', 'https://', '/')):
                href = req.href + href
            items.append((target, name, tag.a(title, href=href)))

        return items
