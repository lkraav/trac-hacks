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

import os
import os.path
import shutil
import tempfile
import unicodedata

from trac.core import Component, Interface, ExtensionPoint, TracError

class ISecDlUpload (Interface):

    """Provides an extension point for plugins."""

    def pre_write (req, file, name, tempdir):
        """Called before the file is temporarily saved.

        The arguments are the request object, the FieldStore file object, the
        normalized filename and the temporary directory the file will be saved
        in.

        Return False to discard the file upload, or True if the processing
        should continue. Note that the first time a False value is returned no
        further 'pre_write' implementations are executed and the upload will be
        discarded. (Note that it is also possible to raise an error from within
        this method, in fact, this is the only way to display meaningful
        messages to the user if more than one reason for discarding the upload
        exists.)
        """

    def process (chunk):
        """Called during the saving of the temporary file.

        One parameter, containing the current part of the file that is to be
        written to disk. The return value should be None, otherwise it must be
        a string. In this case the string will be written to disk instead of
        the actual uploaded content.
        """

    def post_write (handle, name):
        """Called after the temporary file has been written to disk.

        The handle is a file handle as returned by 'tempfile.mkstemp', the
        position in the file will be set to the beginning. The file name of the
        temporary file will be the second parameter (full path). The return
        value of this method is ignored.
        """

class SecDlUploadError (TracError):
    """Raised when there is something wrong with the upload."""

class SecDlUploadFileError (TracError):
    """Raised when there is an error in a file operation."""

class SecDlUpload (Component):

    """General class for file uploads.

    This class provides a general interface for the file upload, including
    sanitizing the file name, saving the uploaded data to a temporary file and
    moving (or copying) it to the final destination (or deleting it if
    required). The class provides three extension points, see 'ISecDlUpload'
    for details.
    """

    _extensions = ExtensionPoint (ISecDlUpload)

    _bufsize   = 4096
    _file      = None
    _name      = None
    _req       = None
    _tmp_dir   = None
    _tmp_file  = None

    def set_file (self, req, field, tempdir, bufsize = 4096):

        """Initialize a new file upload.

        The parameters are: the request object, the name of the HTML input
        field of the file upload, the full path to the temporary directory and
        the buffer size used when writing the temporary file (this is the only
        optional parameter, it defaults to 4096). This method will return the
        normalized file name of the uploaded file, if no error occured. If no
        file was uploaded False will be returned. If the file upload was not
        complete an error will be raised, an error will also be raised if the
        file name (after sanitizing) is empty.
        """

        self.reset ()

        file = req.args.get (field)
        if file is None or not hasattr (file, 'filename') or not file.filename:
            raise SecDlUploadError ('No file uploaded.')

        if not hasattr (file, 'done') or file.done == -1:
            raise SecDlUploadError ('File upload not completed.')

        name = unicodedata.normalize ('NFC', unicode (file.filename, 'utf-8'))
        name = os.path.basename (name.replace ('\\', '/').replace (':', '/'))
        if not name:
            raise SecDlUploadError ('Invalid file name.')

        self._bufsize = bufsize
        self._file    = file
        self._name    = name
        self._req     = req
        self._tmp_dir = tempdir

        return name

    def process (self):

        """Saves the uploaded file to a temporary file.

        This method will save the uploaded file to a temporary file in the
        directory specified with the 'set_file' call. This method will also run
        the extension point methods. On success, the full path to the temporary
        file will be returned, if an extension discards the file, None will be
        returned. In case of an error, an exception will be raised.
        """

        for extension in self._extensions:
            if not extension.pre_write (
                    self._req, self._file, self._name, self._tmp_dir
                ):
                return False

        try:
            (tmp, tmp_file) = tempfile.mkstemp (dir = self._tmp_dir)
        except Exception, e:
            raise SecDlUploadFileError ('Could not create temporary file. %s' % e)

        try:
            chunk = self._file.file.read (self._bufsize)
            while chunk != '':
                for extension in self._extensions:
                    modified = extension.process (chunk)
                    if modified is not None:
                        chunk = modified
                if os.write (tmp, chunk) != len (chunk):
                    raise SecDlUploadFileError (
                            'Error writing temporary file.'
                        )
                chunk = self._file.file.read (self._bufsize)
        except:
            raise SecDlUploadFileError ('Could not save temporary file.')

        for extension in self._extensions:
            try:
                os.lseek (tmp, 0, 0)
            except:
                raise SecDlUploadFileError ('Could not seek temporary file.')
            extension.post_write (tmp, tmp_file)

        try:
            os.close (tmp)
        except:
            SecDlUploadFileError ('Could not close temporary file.')

        self._tmp_file = tmp_file

        return tmp_file

    def _move_or_copy (self, operation, target, mode = None):

        """Performs the copy or move operation of the temporary file.

        Two parameters, the first one must be a function that copies or moves
        the file, taking two parameters itself: source path and destination
        path (for move os.rename is recommended, for copy shutil.copy2 is
        recommended). The second parameter must be the full destination path.
        Intermediate directories are created automatically. The third parameter
        specifies the mode the target file will be chmoded to, if it is not
        specified it defaults to None, meaning that no chmod is performed. This
        method does not reset the member variables.

        In case of an error an exception is raised, else True is returned if
        the temporary file did exist or False if not.
        """

        if self._tmp_file is None or not os.path.isfile (self._tmp_file):
            return False

        path = os.path.dirname (target)
        if not path:
            raise SecDlUploadFileError ('Invalid target path.')
        if not os.path.isdir (path):
            try:
                os.makedirs (path)
            except:
                raise SecDlUploadFileError ('Could not create target path.')

        try:
            operation (self._tmp_file, target)
        except:
            raise SecDlUploadFileError ('Could not copy uploaded file.')

        if mode:
            try:
                os.chmod (target, mode)
            except:
                raise SecDlUploadFileError ('Could not chmod target file.')

        return True

    def move (self, target, mode = None):

        """Moves the temporary file to the final location.

        Same as 'copy', but instead of copying the temporary file it will be
        moved to the destination. Unlike 'copy' this method resets all member
        variables, unless an exception is raised when trying to move the file.
        """

        result = self._move_or_copy (os.rename, target, mode)
        return self.reset () and result

    def copy (self, target, mode = None):

        """Copies the temporary file to the final location.

        The target parameter specifies the location the temporary file should
        be copied to. It has to be the full path, if the target file already
        exists it will be overridden. Intermediate directories will be created
        automatically. An optional third parameter 'mode' can be specified to
        chmod the target file, it defaults to None (ie. no chmod is done). If
        the temporary file does not exist, False will be returned, if the copy
        operation succeeds True will be returned. If there is an error an
        exception will be raised.
        """

        return self._move_or_copy (shutil.copy2, target, mode)

    def delete ():

        """Deletes the temporary file.

        Returns True if the file could be deleted, False if there is no file
        with the temporary name. In case of an error an exception is raised.
        This method resets all member variables, unless the file does exist but
        could not be deleted.
        """

        if self._tmp_file is not None and os.path.isfile (self._tmp_file):
            try:
                os.unlink (self._tmp_file)
            except:
                raise SecDlUploadTemp ('Could not remove temporary file.')
            return self.reset ()
        return not self.reset ()

    def reset (self):

        """Resets all variables.

        This method should be called to reset all member variables if required.
        It is automatically called when a new upload is prepared by the
        'set_file' method, and after a temporary file is removed by the 'move'
        and 'delete' methods. It will always return True.
        """

        self._bufsize  = 4096
        self._file     = None
        self._name     = None
        self._req      = None
        self._tmp_dir  = None
        self._tmp_file = None

        return True

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: