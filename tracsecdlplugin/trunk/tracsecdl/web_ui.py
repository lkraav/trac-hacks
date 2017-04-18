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

import os.path
import re
import sys

from genshi.builder      import tag
from pkg_resources       import resource_filename
from trac.core           import Component, implements, ExtensionPoint
from trac.mimeview       import Context
from trac.util.datefmt   import pretty_timedelta
from trac.util.text      import pretty_size
from trac.web.chrome     import INavigationContributor, ITemplateProvider, \
                                add_script, add_stylesheet
from trac.web.main       import IRequestHandler, RequestDone
from trac.wiki.formatter import format_to
from tracsecdl.config    import SecDlConfig
from tracsecdl.extension import ISecDlDownload
from tracsecdl.model     import SecDlDownload
from tracsecdl.redirect  import SecDlRedirect

class SecDlWebUI (Component):

    """Implements the user interface for the downloads index page.

    User interface implementation (except the admin interface). This includes
    the required stuff to provide the templates and static files to Trac (this
    includes the templates and static files used in the admin interface).
    """

    implements (INavigationContributor, IRequestHandler, ITemplateProvider)

    _extensions = ExtensionPoint (ISecDlDownload)

    # ITemplateProvider methods:

    def get_htdocs_dirs (self):
        """Make the static files available.

        The files in the 'htdocs' directory will be available under the
        '/chrome/secdl/' path, relative to the environment root. Example usage
        later on: add_stylesheet (req, 'secdl/css/example.css')
        """
        return [('secdl', resource_filename (__name__, 'htdocs'))]

    def get_templates_dirs (self):
        """Make the templates available."""
        return [resource_filename (__name__, 'templates')]

    # INavigationContributor methods:

    def get_active_navigation_item (self, req):
        """Return the name of the active navigation item."""
        return 'secdl'

    def get_navigation_items (self, req):
        """Return a list of additional navigation items.

        The list must contain (category, name, text) tuples. 'text' must be an
        anchor tag if required, 'name' must match the name used in the
        get_active_navigation_item() method, see above.

        We only add one new item to the main navigation, and only if the user
        has at least the 'SECDL_VIEW' permission. Both the title and the
        relative path can be configured ('title' and 'url' config options).
        """
        if 'SECDL_VIEW' in req.perm:
            t = self.env [SecDlConfig] ['title']
            u = self.env [SecDlConfig] ['url']
            yield 'mainnav', 'secdl', tag.a (t, href = req.href (u))

    # IRequestHandler methods:

    def match_request (self, req):
        """Return True if this plugin handles the requested URI.

        The following (relative) URLs are currently processed by this plugin
        (<url> is the configured relative path of the download index page
        (configuration option 'url'), <id> is the all-numeric ID of a specific
        download):

         * /<url>               download index page
         * /<url>/<id>          download the specified file (via redirect)
         * /<url>/<id>/md5      checksum of download <id> in md5sum format
         * /<url>/<id>/sha      checksum of download <id> in sha512sum format

        Additionally, all of the paths above are matched if they include a
        trailing slash.
        """
        path  = self.env [SecDlConfig] ['url']
        match = re.match (
                r'^/%s(?:/(?:\d+(?:/(?:md5/?|sha/?)?)?)?)?$' % path,
                req.path_info
            )
        if match:
            return True
        else:
            return False

    def process_request (self, req):

        """Process the request.

        See match_request() for a list of URLs that are eventually processed by
        this method.

        The checksum download (*/md5 or */sha) is usually sent as text/plain to
        be displayed by the browser. To force a 'Save as...' dialog the GET
        parameter 'dl' may be specified (eg. */md5?dl).
        """

        req.perm.require ('SECDL_VIEW')

        path = self.env [SecDlConfig] ['url']

        # Send the checksum of a file in standard GNU md5sum or sha512sum
        # format to the client. If the download ID dows not exist return a 404
        # error, if there is no checksum stored in the database an empty file
        # will be sent:

        match = re.match (r'^/%s/(\d+)/(md5|sha)/?$' % path, req.path_info)
        if match:
            id = int (match.group (1))
            cs = match.group (2)
            rs = self.env [SecDlDownload].checksum (id, cs)
            if rs and rs ['hidden']:
                req.perm.require ('SECDL_HIDDEN')
            if rs and rs ['checksum']:
                req.send_response (200)
                req.send_header ('Content-Type', 'text/plain')
                if req.method == 'GET' and req.args.has_key ('dl'):
                    if cs == 'md5':
                        ex = 'md5sum'
                    else:
                        ex = 'sha512sum'
                    req.send_header (
                            'Content-Disposition',
                            'attachment;filename=%s.%s' % (rs ['name'], ex)
                        )
                req.end_headers ()
                req.write ('%s  %s\n' % (rs ['checksum'], rs ['name']))
            elif rs:
                req.send_response (200)
                req.end_headers ()
            else:
                self._404 (req)

        # Send a redirect to the client if a download is requested. Again, if
        # there is no download with the requested ID, send a 404 error:

        match = re.match (r'^/%s/(\d+)/?$' % path, req.path_info)
        if match:
            id = int (match.group (1))
            # Run extensions first:
            for ext in self._extensions:
                ext.requested (req, id)
            # redirect_url() will check the SECDL_HIDDEN permission.
            (typ, rd) = self.env [SecDlRedirect].redirect_url (req, id)
            if typ and rd:
                self.env [SecDlDownload].count (id)
                if typ != 'trac':
                    self.env [SecDlRedirect].redirect (req, rd)
                else:
                    file = os.path.basename (rd)
                    req.send_header (
                            'Content-Disposition',
                            'attachment;filename=%s' % file
                        )
                    req.send_file (rd)
            else:
                self._404 (req)

        # Main downloads index page. Return a (template, data, content_type)
        # tuple:

        match = re.match (r'^/%s/?$' % path, req.path_info)
        if match:
            data = self.table_data (req, order = req.args.get ('order'))
            return ('secdl.html', data, 'text/html')

    def _404 (self, req):
        """Sends a 404 response to the client. Returns nothing."""
        data = {
                'title'  : 'Not Found',
                'type'   : 'TracError',
                'message': 'Requested document not found.',
            }
        req.send_error (None, status = 404, env = self.env, data = data)

    def table_data (self, req, fields = None, order = None):

        """Return the data for the download index table.

        This method will return the data that is required for the
        secdl-table.html template (as a dictionary). The parameters are a
        request instance, a list containing the fields (columns) to be included
        in the output, and a list used to sort the data (for details on these
        lists please take a look at the SecDlDownload.get_all() method). The
        method will automatically add the required static ressources to the
        request. The SECDL_HIDDEN permission is checked and hidden downloads
        are automatically excluded if required.
        """

        add_stylesheet (req, 'secdl/css/secdl.css')
        add_script     (req, 'secdl/js/secdl.js')

        data = {
                'title'      : self.env [SecDlConfig] ['title'],
                'url'        : self.env [SecDlConfig] ['url'],
                'page_url'   : self.env [SecDlConfig] ['url'],
                'fields'     : self.env [SecDlConfig] ['show_fields'],
                'order'      : self.env [SecDlConfig] ['order'],
                'p_size'     : pretty_size,
                'p_time'     : pretty_timedelta,
                'extended'   : False,
                'cols'       : 0,
                'description': self.env [SecDlDownload].get_description (),
            }

        if fields is not None:
            data ['fields'] = fields
        if 'id' not in data ['fields']:
            data ['fields'].append ('id')

        if order is not None:
            if isinstance (order, list):
                data ['order'] = order
            else:
                data ['order'] = [order]

        # Note: If fields or order contain invalid values (or if any of these
        # is empty) the get_all() method will automatically raise an exception.

        data ['downloads']= self.env [SecDlDownload].get_all (
                fields = data ['fields'],
                order  = data ['order'],
                hidden = 'SECDL_HIDDEN' in req.perm
            )

        # The following columns are additional information that is not
        # displayed by default:

        extended = [
                'description',
                'url',
                'last_request',
                'ip',
                'checksum_md5',
                'checksum_sha'
            ]

        # Check if we need to include the extended info row:
        for field in data ['fields']:
            if field in extended:
                if not data ['extended']:
                    data ['cols'] += 1
                data ['extended'] = True
            elif field not in ['id', 'hidden']:
                if field == 'size':
                    data ['cols'] += 2
                else:
                    data ['cols'] += 1

        # Descriptions (main and per download) are wiki-formatted, create HTML:
        context = Context.from_request (req) ('secdl')
        data ['description_html'] = ''
        if data ['description']:
            data ['description_html'] = format_to (
                    self.env, None, context, data ['description']
                )
        for dl in data ['downloads']:
            # Per-download extended info flag:
            dl ['extended'] = False
            for field in extended:
                if dl.has_key (field) and dl [field]:
                    dl ['extended'] = True
                    break
            if dl.has_key ('description') and dl ['description']:
                dl ['description_html'] = format_to (
                        self.env, None, context, dl ['description']
                    )

        return data

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: