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

import hashlib
import os.path
import time
import urlparse

from trac.core           import Component, TracError
from tracsecdl.config    import SecDlConfig
from tracsecdl.model     import SecDlDownload

class SecDlRedirect (Component):

    """Class to generate the actual download URLs."""

    def subdir (self, id, name):
        """Returns the relative path of file 'name' with ID 'id'.

        The uploaded files are stored in a special directory structure to avoid
        name clashes, currently, for a download with '<ID>' and file '<name>'
        this is '<environment directory>/<last two digits of ID>/<ID>/<name>'.
        Given an ID and a file name this method returns this path, relative to
        the upload directory (ie. no leading slash).
        """
        env = os.path.basename (self.env.path.strip ('/'))
        return '%s/%s/%s/%s' % (env, ('%02i' % int (id)) [-2:], int (id), name)

    def redirect (self, req, url):
        """Send the actual redirect to the client.

        The parameters are a request instance and the URL to redirect the
        client to. This function does basically the same as req.redirect(), but
        supports absolute URLs with schemes other than http and https. The
        redirect will always be a 302 redirect. This method will raise the
        RequestDone exception after the headers are set, and will not return
        any specific value.
        """
        u = urlparse.urlparse (url)
        if not u.scheme or u.scheme == 'http' or u.scheme == 'https':
            req.redirect (url, permanent = False)
        else:
            req.send_response (302)
            req.send_header ('Location', url)
            req.send_header ('Content-Type', 'text/plain;charset=utf-8')
            req.send_header ('Content-Length', len (url) + 13)
            req.send_header ('Pragma', 'no-cache')
            req.send_header ('Cache-Control', 'no-cache')
            req.send_header ('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
            req.end_headers ()
            req.write ('Redirect to: %s' % url)
            raise RequestDone

    def redirect_url (self, req, id):

        """Returns the final download URL.

        This method will return the a (type, url_or_path) tuple. The 'type' is
        one 'secdl', 'regular', 'trac' or 'url'. For 'secdl' and 'regular',
        'url_or_path' will be the relative path to get the requested download
        from the webserver. For 'trac' the 'url_or_path' will be the absolute
        path to the requested file in the local file system, and for 'url' it
        will be the URL to redirect the client to.

        The parameters are a request object and the ID of the requested
        download. If the data can not be retrieved from the database (eg.
        invalid or non-existent ID), this method will return (None, None).
        Insufficient permissions will cause an exception to be raised.
        """

        req.perm.require ('SECDL_VIEW')

        data = self.env [SecDlDownload].redirect_data (id)

        if not data:
            return (None, None)

        if data ['hidden']:
            req.perm.require ('SECDL_HIDDEN')

        # An existing URL in the database means no local download:
        if data ['url']:
            return ('url', data ['url'])

        # Relative path to the upload directory:
        path = self.subdir (id, data ['name'])

        # Config settings:
        secret = self.env [SecDlConfig] ['lighty_secret']
        prefix = self.env [SecDlConfig] ['lighty_prefix']
        reg_dl = self.env [SecDlConfig] ['regular_downloads']
        cgi_dl = self.env [SecDlConfig] ['trac_downloads']
        ul_dir = self.env [SecDlConfig] ['upload_dir']

        # If the prefix does not start with a '/' we create an URL relative to
        # the project environment, everything else we be the same:
        if prefix [0] != '/':
            prefix = req.href (prefix)

        if prefix [-1] != '/':
            prefix += '/'

        if secret:
            # Calculate the mod_secdownload path and return it (note that
            # 'path' itself does not start with a '/'):
            tm = '%08x' % time.time ()
            cs = hashlib.md5 (secret + '/' + path + tm).hexdigest ()
            return ('secdl', '%s%s/%s/%s' % (prefix, cs, tm, path))

        if reg_dl:
            # Regular downloads will simply be prefix + path:
            return ('regular', prefix + path)

        if cgi_dl:
            # And the full (local) file path for Trac downloads:
            return ('trac', '%s/%s' % (ul_dir, path))

        # At this point none of the available download methods did work, so we
        # raise an exception:
        raise TracError ('Downloads are currently not available.')

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: