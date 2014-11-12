# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Dirk Stöcker <trac@stoecker.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs.

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements

from traclate.web import _

class TraclateAdmin(Component):
    """Web administration for translation infrastructure"""

    implements(IAdminPanelProvider)

    # IAdminPanelProvider

    def get_admin_panels(self, req):
        if req.perm.has_permission('TRANS_CONFIG'):
            yield ('traclate', _("Translation"), 'config', 
                   _("Configuration"))

    def render_admin_panel(self, req, cat, page, path_info):
        raise Exception("Not implemented")
