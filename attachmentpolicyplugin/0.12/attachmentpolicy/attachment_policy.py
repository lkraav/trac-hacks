# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Gefasoft AG
# Copyright (C) 2011 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Component, implements
from trac.perm import IPermissionPolicy, IPermissionRequestor


class AttachmentDeletePolicy(Component):
    """Adds permission `TICKET_ATTACHMENT_DELETE` for exclusive right to
    delete and replace attachments, regardless who added / changed it.

    Everybody who has permission `TICKET_ATTACHMENT_DELETE` can delete /
    replace attachments, regardless who added / changed it.

    Once this plugin is enabled, you'll have to insert it at the appropriate
    place in your list of permission policies, e.g.
    {{{#!ini
    [trac]
    permission_policies = AttachmentDeletePolicy, DefaultPermissionPolicy, LegacyAttachmentPolicy
    }}}
    """
    implements(IPermissionPolicy, IPermissionRequestor)

    # IPermissionPolicy methods

    def check_permission(self, action, username, resource, perm):
        # Avoid recursion
        if action == 'TICKET_ATTACHMENT_DELETE':
            return

#        self.log.info( "action: %s, resource: %s" % (action, resource) )
        # Check whether we're dealing with a ticket resource
        if action == 'ATTACHMENT_DELETE' and \
                resource and \
                resource.realm == 'attachment' and \
                'TICKET_ATTACHMENT_DELETE' in perm:
            self.log.info("Granted permission for user %s to delete "
                          "attachment %s", username, resource)
            return True

    # IPermissionRequestor methods

    def get_permission_actions(self):
        yield 'TICKET_ATTACHMENT_DELETE'
