# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.perm import IPermissionPolicy, IPermissionRequestor
from trac.ticket.model import Ticket
from trac.wiki.model import WikiPage


class SelfDeletePolicy(Component):
    """Permissions policy that allows users to delete wiki pages and
    attachments that they created.
    """

    implements(IPermissionPolicy, IPermissionRequestor)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        yield 'WIKI_DELETE_SELF'
        yield 'TICKET_DELETE_SELF'

    # IPermissionPolicy methods

    def check_permission(self, action, username, resource, perm):
        if action in self.get_permission_actions():
            return
        if resource:
            if resource.realm == 'wiki' and \
                    action == 'WIKI_DELETE':
                return WikiPage(self.env, resource, 1).author == username
            if resource.realm == 'attachment' and \
                    resource.parent.realm == 'ticket' and \
                    action == 'ATTACHMENT_DELETE':
                ticket = Ticket(self.env, resource.parent.id)
                return ticket['reporter'] == username
