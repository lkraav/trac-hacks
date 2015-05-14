# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Giuseppe Ursino
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.


from trac.config import ListOption
from trac.core import *
from trac.perm import IPermissionPolicy, IPermissionRequestor, PermissionSystem
from trac.ticket.model import Ticket
from trac.util.compat import set
from trac.web.chrome import Chrome
from fnmatch import fnmatchcase


class RestrictAccessPolicy(Component):
    """Central tasks for the PrivateTickets plugin."""
    
    implements(IPermissionRequestor, IPermissionPolicy)
    
    # New permission actions
    actions = set(['TRAC_RESTRICT_ACCESS'])
    
    # IPermissionPolicy(Interface)
    def check_permission(self, action, username, resource, perm):
        self.env.log.debug('RA[check_permission]: action: %s, username: %s, ' \
                           'resource: %s, perm: %s' % 
                           (action, username, resource, perm))
        
        if username == 'anonymous' or \
           action == 'TRAC_ADMIN' or \
           action in self.actions or \
           'TRAC_ADMIN' in perm:
            # In these cases, checking makes no sense
            return None
                           
        if resource and perm.has_permission('TRAC_RESTRICT_ACCESS'): # restricted user
        
            self.log.debug('RA[check_permission]: restricted user to resource: %s' \
                           % (resource.id))

            # Check for wiki restrict
            if resource.realm == 'wiki': # wiki realm or resource
                if resource.id: # ... it's a resource
                    if fnmatchcase(resource.id, 'WikiStart') or \
                       fnmatchcase(resource.id, 'SharedPages/*'):
                        self.log.debug('RA[check_permission]: access agreed')
                        return None
                    else:
                        self.log.debug('RA[check_permission]: access denied')
                        return False
            
            # Look up the resource parentage for a ticket.
            while resource:
                if resource.realm == 'ticket':
                    break
                resource = resource.parent
            
            if resource and resource.realm == 'ticket' and resource.id:
                
                try:
                    tkt = Ticket(self.env, resource.id)
                except TracError:
                    return None  # Ticket doesn't exist
                    
                cc_list = Chrome(self.env).cc_list(tkt['cc'])
                
                if perm.username == tkt['reporter'] or \
                   perm.username == tkt['owner'] or \
                   perm.username in cc_list:
                    return None
                else:
                    return False
            
            # Else
            return None
            
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        self.log.debug('RA[get_permission_actions]: %s'% (self.actions))
        return self.actions

