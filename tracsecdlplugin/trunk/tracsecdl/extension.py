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

from trac.core import Interface

class ISecDlDownload (Interface):

    """Provides an extension point for plugins."""

    def created (id):
        """Called when a new download has been created.

        The only argument is the ID of the new download. The return value of
        this method is ignored.
        """
        # Called in  SecDlAdminPanelDownload._render_admin_panel() in
        # admin_ui.py.

    def removed ():
        """Called when a download has been removed.

        No parameters, return value is ignored. There is not much you can do in
        this method, since the download data has been deleted from the database
        already if there was a download to delete, for technical reasons, you
        can not be sure that this is the case (ie. trying to delete a
        non-existing download will also cause this method to be called). Note
        that if multiple downloads are deleted at once this method will be
        called only once after the downloads are removed.
        """
        # Called in  SecDlAdminPanelDownload._render_admin_panel() in
        # admin_ui.py.

    def requested (req, id):
        """Called when a download is requested.

        This method is called when a download is requested by a client, before
        the redirect is sent to the client. The parameters are a request
        instance and the ID of the requested download. The return value of this
        method is ignored.
        """
        # Called in SecDlWebUI.process_request() in web_ui.py.

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: