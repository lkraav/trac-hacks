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

from genshi.builder   import tag
from trac.core        import Component, implements
from trac.web.chrome  import add_stylesheet
from trac.wiki        import IWikiSyntaxProvider
from tracsecdl.config import SecDlConfig
from tracsecdl.model  import SecDlDownload

class SecDownloadWiki (Component):

    """Extend the wiki syntax with download specific stuff."""

    implements (IWikiSyntaxProvider)

    def get_link_resolvers (self):
        """Provides additional wiki syntax for the downloads.

        All prefixes must be defined in the configuration file (option
        'wiki_prefix'), the default is 'download,secdownload', ie. the two
        prefixes 'download' and 'secdownload' can be used to link to the
        files.

        Usage: '[download:123 label]' or simply 'download:123' (instead of
        'download' every configured prefix can be used). To link to the
        downloads index page use either the usual '[/downloads]' (if this is
        the configured download url, see the 'url' config option) or
        'download:index'.

        This method must return a list of (prefix, function) tuples.
        """
        for prefix in self.env [SecDlConfig] ['wiki_prefix']:
            yield prefix, self._download_link

    def get_wiki_syntax (self):
        """No more wiki syntax is provided by get_wiki_syntax."""
        return []

    def _download_link (self, formatter, namespace, target, label):
        """Return the HTML for the download link on wiki pages.

        If the target is index, a link to the download index page will be
        rendered, if the target is a string containing only digits, the ID is
        checked for existence (and sufficient permissions), invalid IDs and
        insufficient permissions will result in an error message being shown.
        """

        add_stylesheet (formatter.req, 'secdl/css/secdl.css')

        if 'SECDL_VIEW' in formatter.req.perm:

            url = self.env [SecDlConfig] ['url']

            # prefix:index is allowed to link to the downloads index page:
            if target == 'index':
                return tag.a (label, href = formatter.href (url))

            # Everything else not completely made out of digits is invalid:
            if not target.isdigit ():
                return self._error ('%s is no valid download ID.' % target)

            # Use the redirect_data() method to get the download info:
            dl = self.env [SecDlDownload].redirect_data (int (target))

            if not dl:
                return self._error ('Download #%s does not exist.' % target)

            if dl ['hidden'] and 'SECDL_HIDDEN' not in formatter.req.perm:
                return self._error ()

            if label.isdigit ():
                label = dl ['name']

            # Download exists and permissions are ok:
            return tag.a (label, href = formatter.href (url, target))

        else:
            return self._error ()

    def _error (self, msg = 'No permission to download this file.'):
        """Returns an error message with the specified message 'msg'."""
        return tag.span ('[ERROR: %s]' % msg, class_ = 'secdlerror')

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: