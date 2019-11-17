# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2014-2019 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.attachment import Attachment
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
            parent = resource.parent
            if resource.realm == 'wiki' and \
                    action == 'WIKI_DELETE' and \
                    WikiPage(self.env, resource, 1).author == username:
                return True
            if resource.realm == 'attachment' and \
                    action == 'ATTACHMENT_DELETE' and \
                    Attachment(self.env, parent.realm, parent.id,
                               resource.id).author == username:
                return True
