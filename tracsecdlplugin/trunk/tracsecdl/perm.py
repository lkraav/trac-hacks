# Copyright 2010-2011, 2014 Stefan Goebel - <tracsecdl -at- subtype -dot- de>
#
# This file is part of TracSecDl.
#
# TracSecDl is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# TracSecDl is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# TracSecDl. If not, see <http://www.gnu.org/licenses/>.

from trac.core import Component, implements
from trac.perm import IPermissionRequestor

class SecDlPerm (Component):

    """Basic permission stuff for TracSecDl."""

    implements (IPermissionRequestor)

    # IPermissionRequestor methods:

    def get_permission_actions (self):

        """Provides additional permissions for TracSecDl.

        Implemented are three permissions, basic permission is SECDL_VIEW to
        allow access to the downloads. SECDL_HIDDEN allows access to downloads
        that are marked hidden, and SECDL_ADMIN allows access to the
        administration interface. All permissions include the previous ones,
        ie. SECDL_HIDDEN includes SECDL_VIEW permissions and SECDL_ADMIN
        includes all permissions.
        """

        # Basic permission SECDL_VIEW:
        yield 'SECDL_VIEW'

        # All other permissions include the previous ones:
        yield ('SECDL_HIDDEN', ['SECDL_VIEW'  ])
        yield ('SECDL_ADMIN',  ['SECDL_HIDDEN'])

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: