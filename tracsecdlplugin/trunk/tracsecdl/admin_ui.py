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
import os
import re
import shutil
import urlparse

from trac.admin          import IAdminPanelProvider
from trac.core           import Component, implements, TracError, \
                                ExtensionPoint
from trac.util.datefmt   import pretty_timedelta, to_datetime, format_datetime
from trac.util.text      import pretty_size
from trac.web.chrome     import add_script, add_stylesheet, add_warning
from tracsecdl.config    import SecDlConfig
from tracsecdl.extension import ISecDlDownload
from tracsecdl.model     import SecDlArch, SecDlPlatform, SecDlType, \
                                SecDlComponent, SecDlMilestone, SecDlVersion, \
                                SecDlDownload
from tracsecdl.redirect  import SecDlRedirect
from tracsecdl.upload    import SecDlUpload, ISecDlUpload
from tracsecdl.web_ui    import SecDlWebUI

class SecDlAdminPanel (Component):

    """Abstract class providing the extension methods for admin panels."""

    abstract = True

    implements (IAdminPanelProvider)

    # IAdminPanelProvider methods:

    def get_admin_panels (self, req):
        """Return (category, category_label, page, page_label) tuples.

        We use the category 'secdl' and the configured title. subpages are
        defined in the inheriting classes. 'SECDL_ADMIN' permission is required
        to access the admin interface.
        """
        if 'SECDL_ADMIN' in req.perm:
            title = self.env [SecDlConfig] ['title']
            yield ('secdl', title, self._page, self._page.capitalize ())

    def render_admin_panel (self, req, cat, page, path_info):
        """Return a (template, data) tuple for the admin pages.

        Actual implementation is provided by the _render_admin_panel() methods
        of the inheriting classes.
        """
        req.perm.require ('SECDL_ADMIN')
        add_stylesheet (req, 'secdl/css/secdl-admin.css')
        try:
            return self._render_admin_panel (req, cat, page, path_info)
        except AssertionError, e:
            raise TracError (e)

class SecDlAdminPanelDownload (SecDlAdminPanel):

    """Implements the downloads section of the admin interface."""

    implements (ISecDlUpload)

    _exts = ExtensionPoint (ISecDlDownload)
    _page = 'downloads'
    _md5  = None
    _sha  = None
    _size = None

    # ISecDlUpload methods:

    def pre_write (self, req, file, name, tempdir):

        """Check the uploaded file before it is saved temporarily.

        This method performs some basic file checks and raises a TracError if
        some check fails and the upload should be discarded. If the upload
        looks fine it returns True and processing continues.
        """

        # Check the file size. The following stuff has to be checked:
        #   * the file size must not exceed 'max_size' bytes
        #   * the file must not be empty
        #   * the size of all uploaded files must not exceed 'max_total' bytes

        if hasattr (file.file, 'fileno'):
            self._size = os.fstat (file.file.fileno ()) [6]
        else:
            file.file.seek (0, 2)
            self._size = file.file.tell ()
            file.file.seek (0)

        # Check for empty file:
        if self._size == 0:
            raise TracError ("Can't upload an empty file.")

        # Check 'max_size' option:
        max_size = self.env [SecDlConfig] ['max_size']
        if max_size > 0 and self._size > max_size:
            raise TracError ('Maximum file size: %s bytes.' % max_size)

        # Check the 'max_total' option:
        (cur_total, max_total, reached) = self._max_total_reached ()
        if max_total > 0:
            if cur_total + self._size > max_total:
                raise TracError ('Maximum size of all uploads exceeded.')

        return True

    def process (self, chunk):
        """Called during the saving to a temporary file.

        This method will feed the provided chunk of the file to the checksum
        instances. It must return None (else it would alter the file content).
        """
        self._md5.update (chunk)
        self._sha.update (chunk)
        return None

    def post_write (self, handle, name):
        """Called after the temporary file has been written to disk."""
        pass

    # SecDlAdminPanel methods:

    def _render_admin_panel (self, req, cat, page, path_info):

        """Returns the (template, data) tuple for the downloads admin page."""

        data   = {}
        dl     = self.env [SecDlDownload]
        new_id = None

        if path_info is None:

            # Main page with the downloads index table. This page will also be
            # rendered when the form to create a new download is submitted.

            if req.method == 'POST' and req.args.get ('createlocal'):

                # Create a new download entry from an uploaded file.

                # Check 'max_files' before doing anything else:
                (cur_files, max_files, reached) = self._max_files_reached ()
                if reached:
                    raise TracError ('Maximum number of uploads reached.')

                tempdir  = self.env [SecDlConfig] ['temp_dir']
                if not tempdir:
                    env = os.path.basename (self.env.path.strip ('/'))
                    dir = self.env [SecDlConfig] ['upload_dir']
                    tempdir = '%s/%s' % (dir, env)

                upld = self.env [SecDlUpload]
                file = upld.set_file (req, 'file', tempdir)

                # Clean up the file name:
                file = re.sub (r'[^a-zA-Z0-9_.-]', '_', file.strip ('.'))

                # Check for an empty file name:
                if not file:
                    raise TracError ('No file uploaded or invalid file name.')

                # File name must not start with a dash:
                if file [0] == '-':
                    raise TracError ('Invalid file name.')

                # Check for duplicate files if required:
                if self.env [SecDlConfig] ['duplicate'] == 'deny':
                    if dl.local_file_exists (file):
                        raise TracError ('This file already exists.')

                # Check allowed file extensions if required:
                (base, ext) = os.path.splitext (file)
                if base == '' and ext != '':
                    # Fix for Python < 2.6 behaviour:
                    (base, ext) = (ext, base)
                ext = ext.lstrip ('.')
                # Check 'no_extension' option:
                if not ext and not self.env [SecDlConfig] ['no_extension']:
                    raise TracError ('File name extension is empty.')
                # Check 'extensions' option:
                elif ext:
                    allowed = self.env [SecDlConfig] ['extensions']
                    if allowed and ext not in allowed:
                        raise TracError ('This file type is not allowed.')

                # Create the md5 and sha512 instances. They will get their data
                # during the writing of the temporary file, see the process()
                # method for details.
                self._md5 = hashlib.md5 ()
                self._sha = hashlib.sha512 ()

                # Try to write the uploaded file to a temporary file:
                tempfile = upld.process ()
                if not tempfile:
                    raise TracError ('Upload not successful.')

                # If that succeeded, try to add the download data to the
                # database:
                id = dl.add (
                        name         = file,
                        url          = None,
                        size         = self._size,
                        description  = req.args.get ('descr'),
                        component    = req.args.get ('component'),
                        milestone    = req.args.get ('milestone'),
                        version      = req.args.get ('version'),
                        architecture = req.args.get ('arch'),
                        platform     = req.args.get ('platform'),
                        type         = req.args.get ('type'),
                        hidden       = req.args.get ('hidden'),
                        checksum_md5 = self._md5.hexdigest (),
                        checksum_sha = self._sha.hexdigest (),
                        author       = req.authname,
                        ip           = req.remote_addr,
                    )

                # In case of an error delete the temporary file and raise an
                # error:
                if not id:
                    upld.delete ()
                    raise TracError ('Could not add download to the database.')

                # Once we got the ID of the download we can move the temporary
                # file to the final location. The actual path relative to the
                # upload directory is provided by SecDlRedirect.subdir(), see
                # there for details:
                rel = self.env [SecDlRedirect].subdir (id, file)
                tgt = '%s/%s' % (self.env [SecDlConfig] ['upload_dir'], rel)

                # Move the temporary file and raise an exception if it fails:
                if not upld.move (tgt, 0644):
                    upld.delete ()
                    raise TracError ('Could not move file to final loactaion.')

                # Save the ID for later...
                new_id = id

                # Finally run any extensions:
                for ext in self._exts:
                    ext.created (id)

            elif req.method == 'POST' and req.args.get ('createremote'):

                # Remote downloads are a lot easier, we only need to add the
                # data to the database, after performing some checks:
                (name, url, size, md5, sha) = self._check_remote (
                        req.args.get ('name'),
                        req.args.get ('url'),
                        req.args.get ('size'),
                        req.args.get ('md5'),
                        req.args.get ('sha'),
                    )

                # Everything else should be fine if the form on the admin page
                # was used, if some value is invalid the add() method will
                # raise an exception anyway.
                id = dl.add (
                        name         = name,
                        url          = url,
                        size         = size,
                        checksum_md5 = md5,
                        checksum_sha = sha,
                        author       = req.authname,
                        ip           = req.remote_addr,
                        description  = req.args.get ('descr'),
                        component    = req.args.get ('component'),
                        milestone    = req.args.get ('milestone'),
                        version      = req.args.get ('version'),
                        architecture = req.args.get ('arch'),
                        platform     = req.args.get ('platform'),
                        type         = req.args.get ('type'),
                        hidden       = req.args.get ('hidden'),
                    )

                if not id:
                    raise TracError ('Could not add download to the database.')

                new_id = id

                for ext in self._exts:
                    ext.created (id)

            elif req.method == 'POST' and req.args.get ('removeall'):

                # Request to remove all downloads. We will first delete all
                # remote downloads, and then process the list of local
                # downloads, trying to remove the local file and if that
                # succeeds remove the entry from the database, if not the entry
                # will not be deleted.

                dl.delete_remote ()

                local = dl.get_local_files ()
                for id, name in local:
                    root = self.env [SecDlConfig] ['upload_dir']
                    envd = os.path.basename (self.env.path.strip ('/'))
                    subd = ('%02i' % int (id)) [-2:]
                    try:
                        shutil.rmtree ('%s/%s/%s' % (root, envd, subd))
                    except:
                        raise TracError ('Could not delete the %s.' % name)
                    dl.delete (id)

                for ext in self._exts:
                    ext.removed ()

            elif req.method == 'POST' and req.args.get ('remove'):

                # Remove a selected set of downloads. Basically the same as
                # above, but iterating over the list of selected downloads.

                sel = req.args.get ('sel')

                if sel:
                    if type (sel) is not list:
                        sel = [sel]
                    root = self.env [SecDlConfig] ['upload_dir']
                    for id in sel:
                        name = dl.get_local_file (id)
                        if name:
                            subd = ('%02i' % int (id)) [-2:]
                            envd = os.path.basename (self.env.path.strip ('/'))
                            try:
                                shutil.rmtree ('%s/%s/%s' % (root, envd, subd))
                            except Exception, e:
                                raise TracError ('Could not delete %s.' % name)
                            dl.delete (id)
                        else:
                            dl.delete (id)

                for ext in self._exts:
                    ext.removed ()

            # Now get the current list of downloads, including all available
            # information:

            data = self.env [SecDlWebUI].table_data (
                    req,
                    fields = self.env [SecDlDownload].columns (),
                    order  = req.args.get ('order')
                )

            data ['page_url'] = 'admin/secdl/downloads'
            data ['admin']    = True
            data ['new_id']   = new_id

            # table_data() doesn't actually know about the admin specific
            # columns, we need to add 4 to the column number:
            data ['cols'] += 4

            # Check if uploads (ie. for local downloads) are still possible:
            data ['uploads'] = True

            # If maximum number of files is not reached yet:
            (cur, max_f, lim)  = self._max_files_reached ()
            data ['max_files'] = max_f
            data ['cur_files'] = cur
            if max_f:
                data ['files_pct'] = min (int (round (cur * 100 / max_f)), 100)
                # Don't show link to create local download if limit is reached:
                if lim:
                    data ['files_cls'] = {'class': 'reached'}
                    data ['uploads']   = False

            # And the maximum size of all files is not reached yet:
            (cur, max_t, lim)  = self._max_total_reached ()
            data ['max_total'] = max_t
            data ['cur_total'] = cur
            # Pretty size is only required if there are more than 512 bytes:
            if max_t >= 512:
                data ['max_total_p'] = pretty_size (max_t)
            if cur >= 512:
                data ['cur_total_p'] = pretty_size (cur)
            if max_t:
                data ['total_pct'] = min (int (round (cur * 100 / max_t)), 100)
                # Don't show link to create local download if limit is reached:
                if lim:
                    data ['total_cls'] = {'class': 'reached'}
                    data ['uploads']   = False

            # That's all there is to do for the main admin page!

        elif path_info == 'local' or path_info == 'remote':

            # The form to create either a new local or a new remote download.
            # Currently errors will cause an exception to be raised, submitting
            # the form will display the main page again.

            add_script (req, 'common/js/wikitoolbar.js')

            # Some basic info required for both types:
            data ['view'] = path_info
            data ['arch'] = self.env [SecDlArch     ].get_all ()
            data ['pfrm'] = self.env [SecDlPlatform ].get_all ()
            data ['typ_'] = self.env [SecDlType     ].get_all ()
            data ['comp'] = self.env [SecDlComponent].get_all ()
            data ['mlst'] = self.env [SecDlMilestone].get_all ()
            data ['vers'] = self.env [SecDlVersion  ].get_all ()

            # Remote download specific data:
            if path_info == 'remote':

                # Display the scheme restrictions to the user:
                data ['schemes'] = self.env [SecDlConfig] ['schemes']

            # Local download specific data:
            if path_info == 'local':

                # Check the limits and raise an error in case a limit is
                # reached and the upload would fail anyway:
                (cur, max_f, lim) = self._max_files_reached ()
                if lim:
                    raise TracError ('Maximum number of uploads reached.')
                (cur, max_t, lim) = self._max_total_reached ()
                if lim:
                    raise TracError ('Maximum total upload size reached.')

                # Get the current file size limit. It is either the 'max_size'
                # option (if enabled) or the 'max_total' option minus the size
                # of the files already uploaded (if 'max_total' is enabled).
                max_size = int (self.env [SecDlConfig] ['max_size'] or 0)
                data ['size'] = 0
                if max_t:
                    data ['size'] = min (max (max_t - cur, 0), max_size)
                elif max_size:
                    data ['size'] = max_size
                data ['size_p'] = pretty_size (data ['size'])

                # File name extension restrictions:
                data ['no_ext'] = self.env [SecDlConfig] ['no_extension']
                data ['exts']   = self.env [SecDlConfig] ['extensions']

        elif path_info == 'description':

            # Display the form to change the main download description.
            # Submitting the form will lead to this page again.

            if req.method == 'POST' and req.args.get ('savedescr'):

                # Modify the main download description. Not much to do here,
                # basically all values are accepted.

                dl.edit_description (req.args.get ('description'))

            add_script (req, 'common/js/wikitoolbar.js')

            data ['view'] = 'description'
            data ['desc'] = dl.get_description ()

        elif path_info.isdigit ():

            # Display the form to modify an existing download. Submitting this
            # form will show this page again. Local and remote downloads
            # require different forms, and different handling when modifying
            # the data in the database:

            if req.method == 'POST' and req.args.get ('changelocal'):

                # First check if it's really an existing local download:
                rd = dl.redirect_data (int (path_info))
                if not rd or rd ['url']:
                    raise TracError ('Not a local download: %s' % path_info)

                # Simply try to update the data for local downloads. All the
                # fields will be checked (if required) by the edit() method, so
                # it is safe to not perform any checks here.
                dl.edit (
                        int (path_info),
                        description  = req.args.get ('descr'),
                        component    = req.args.get ('component'),
                        milestone    = req.args.get ('milestone'),
                        version      = req.args.get ('version'),
                        architecture = req.args.get ('arch'),
                        platform     = req.args.get ('platform'),
                        type         = req.args.get ('type'),
                        hidden       = req.args.get ('hidden'),
                    )

            elif req.method == 'POST' and req.args.get ('changeremote'):

                # First check if it's really an existing remote download:
                rd = dl.redirect_data (int (path_info))
                if not rd or not rd ['url']:
                    raise TracError ('Not a remote download: %s' % path_info)

                # For remote downloads some checks are performed first. These
                # are checked again by the edit method, but since the user may
                # enter invalid values here we perform the checks before and
                # display a specific error message if something is wrong.
                (name, url, size, md5, sha) = self._check_remote (
                        req.args.get ('name'),
                        req.args.get ('url'),
                        req.args.get ('size'),
                        req.args.get ('md5'),
                        req.args.get ('sha'),
                    )

                dl.edit (
                        int (path_info),
                        name         = name,
                        url          = url,
                        size         = size,
                        checksum_md5 = md5,
                        checksum_sha = sha,
                        description  = req.args.get ('descr'),
                        component    = req.args.get ('component'),
                        milestone    = req.args.get ('milestone'),
                        version      = req.args.get ('version'),
                        architecture = req.args.get ('arch'),
                        platform     = req.args.get ('platform'),
                        type         = req.args.get ('type'),
                        hidden       = req.args.get ('hidden'),
                    )

            # Get the download data. If the download does not exist raise an
            # exception:
            d = dl.get (int (path_info))
            if not d:
                raise TracError ('No download exists with that ID.')

            add_script (req, 'common/js/wikitoolbar.js')

            data ['view'] = 'detail'
            data ['url']  = self.env [SecDlConfig] ['url']

            if d ['url']:
                data ['typ']     = 'remote'
                data ['schemes'] = self.env [SecDlConfig] ['schemes']
            else:
                data ['typ']     = 'local'

            # Data required for the form:
            data ['arch'] = self.env [SecDlArch     ].get_all ()
            data ['pfrm'] = self.env [SecDlPlatform ].get_all ()
            data ['typ_'] = self.env [SecDlType     ].get_all ()
            data ['comp'] = self.env [SecDlComponent].get_all ()
            data ['mlst'] = self.env [SecDlMilestone].get_all ()
            data ['vers'] = self.env [SecDlVersion  ].get_all ()

            d ['p_time_d'] = pretty_timedelta (d ['time'])
            d ['p_size']   = pretty_size (d ['size'] or 0)
            d ['p_time']   = format_datetime (to_datetime (d ['time']))

            if d ['last_request']:
                d ['p_last_request_d'] = pretty_timedelta (d ['last_request'])
                d ['p_last_request']   = format_datetime (
                        to_datetime (d ['last_request'])
                    )

            data ['dl'] = d

        else:

            # Every path_info value not covered above is invalid:
            raise TracError ('Invalid ID: %s' % path_info)

        # That's it. Return the template and the data:
        return 'secdl-admin-dl.html', data

    def _max_total_reached (self):
        """Check if the total file size limit is reached.

        This method checks if the total size of all local uploads is greater or
        equal to the configured 'max_total' limit. The return value will be a
        tuple containing the values (current_value, max_total, limit_reached).
        The first two values are the values checked, the third value will be
        either True or False, depending on the outcome of the check. If the
        'max_total' option is disabled it will always be False, else it will be
        False if the limit is not yet reached.
        """
        max_total = int (self.env [SecDlConfig] ['max_total'] or 0)
        cur_total = self.env [SecDlDownload].get_local_size ()
        total_lim = max_total > 0 and cur_total >= max_total
        return (cur_total, max_total, total_lim)

    def _max_files_reached (self):
        """Check if the total number of local downloads is reached.

        This method checks if the total number of local uploads is greater or
        equal to the configured 'max_files' limit. The return value will be a
        tuple containing the values (current_files, max_files, limit_reached).
        The first two values are the values checked, the third value will be
        either True or False, depending on the outcome of the check. If the
        'max_files' option is disabled it will always be False, else it will be
        False if the limit is not yet reached.
        """
        max_files = int (self.env [SecDlConfig] ['max_files'] or 0)
        cur_files = self.env [SecDlDownload].get_local_number ()
        files_lim = max_files > 0 and cur_files >= max_files
        return (cur_files, max_files, files_lim)

    def _check_remote (self, name, url, size, md5, sha):

        """Performs some validity checks for remote download data.

        The parameters are the file name, the url, the file size, the MD5
        checksum and the SHA512 checksum, in that order. This method will run a
        few checks on these values and return a list like the parameters that
        should be used as parameters for the actual download add/modify method.
        """

        # First required field is the file name, check and clean it up:
        name = name.strip ()
        name = re.sub (r'[^a-zA-Z0-9_.-]', '_', name.strip ('.'))
        if not name:
            raise TracError ('No name specified.')

        # Second required field is the URL, check for a valid scheme:
        url = url.strip ()
        parts = urlparse.urlparse (url)
        if not parts.scheme:
            raise TracError ('URLs must include the scheme.')
        allowed = self.env [SecDlConfig] ['schemes']
        if allowed and parts.scheme not in allowed:
            raise TracError ('Specified URL scheme is not allowed.')
        # Check that there are at least a few characters in the URL:
        if len (''.join (parts [1:])) < 4:
            raise TracError ('Invalid URL specified.')

        # If a size is specified it has to be numeric:
        if size:
            if not size.isdigit ():
                raise TracError ('Invalid file size specified.')
        else:
            size = None

        # And check the validity of the checksums:
        md5 = md5.lower ()
        sha = sha.lower ()
        if md5 and not re.match (r'^[a-f0-9]{32}$', md5):
            raise TracError ('Invalid MD5 checksum.')
        if sha and not re.match (r'^[a-f0-9]{128}$', sha):
            raise TracError ('Invalid SHA512 checksum.')

        return (name, url, size, md5, sha)

class SecDlAdminPanelEnum (SecDlAdminPanel):

    """Abstract base class for the architecture, platform and type panels.

    Inheriting classes only need to set their _model and _page member variables
    to their specific values, everything else will be done by this class.
    """

    abstract = True

    def _render_admin_panel (self, req, cat, page, path_info):

        """Returns the (template, data) tuple for the requested admin page."""

        # Some basic data required on all pages:
        model = self.env [self._model]
        data  = {
                'title' : self._page.capitalize () [:-1],
                'titles': self._page.capitalize (),
                'name'  : self._page [:-1],
                'names' : self._page,
                'attrs' : {},
                'view'  : 'list',
            }

        if path_info is None:

            # Main page. Display a list with all available stuff, and handle
            # the creation and removal of whatever we're currently responsible
            # for.

            if req.method == 'POST' and req.args.get ('add'):
                names = req.args.get ('name')
                if names:
                    if type (names) is not list:
                        names = [names]
                    for name in names:
                        if not name:
                            continue
                        try:
                            id = model.add (name)
                            data ['attrs'] [id] = {'class': 'created'}
                        except:
                            add_warning (req, "Could not add '%s'." % name)

            elif req.method == 'POST' and req.args.get ('remove'):
                sel = req.args.get ('sel')
                if sel:
                    if type (sel) is not list:
                        sel = [sel]
                    for id in sel:
                        model.delete (id)

            elif req.method == 'POST' and req.args.get ('removeall'):
                model.delete_all ()

            add_script (req, 'secdl/js/secdl.js')
            data ['enums'] = model.get_all ()

        elif path_info.isdigit ():

            # Show the form to modify an existing entry. Submitting this form
            # will show the same page again.

            if req.method == 'POST' and req.args.get ('save'):
                name = req.args.get ('name')
                if name:
                    descr = req.args.get ('description')
                    id    = int (path_info)
                    model.edit (id, name, descr)

            data ['enum'] = model.get (int (path_info))
            if data ['enum']:
                add_script (req, 'common/js/wikitoolbar.js')
                data ['view'] = 'detail'
            else:
                raise TracError ('ID %s does not exist.' % path_info)

        else:

            # Every other path_info is an error:
            raise TracError ('Invalid ID: %s.' % path_info)

        # Done. Return the template and the data:
        return 'secdl-admin-enum.html', data

class SecDlAdminPanelArch (SecDlAdminPanelEnum):
    """Implements the architectures admin panel."""
    _page  = 'architectures'
    _model = SecDlArch


class SecDlAdminPanelPlatform (SecDlAdminPanelEnum):
    """Implements the platforms admin panel."""
    _page  = 'platforms'
    _model = SecDlPlatform


class SecDlAdminPanelType (SecDlAdminPanelEnum):
    """Implements the types admin panel."""
    _page  = 'types'
    _model = SecDlType

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: