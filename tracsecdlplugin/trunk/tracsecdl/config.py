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

from trac.core   import Component
from trac.config import Option, BoolOption, ListOption, IntOption, \
                        ConfigurationError

class SecDlConfig (Component):

    """Provides access to the configuration options.

    Access to the configuration is possible using either 'config.get(key)' or
    'config[key]' (with 'config' being an instance of this class and 'key' the
    string specifying the configuration option), both methods are not exactly
    the same, see '__getitem__()' and 'get()' for details.

    Assignment (ie. changing configuration options) is not yet supported.
    """

    _section   = 'secdl'
    _separator = ','
    _lists     = [
            'extensions', 'order', 'schemes', 'show_fields', 'wiki_prefix'
        ]

    Option (
            section = _section,
            name    = 'duplicate',
            default = 'deny',
            doc     = """Specify what to do if a file is uploaded with an
                      already existing file name. To deny the upload, set it
                      to 'deny' (default), set it to 'allow' to allow two files
                      with the same name. Note that this applies only to local
                      downloads, remote downloads are not restricted."""
        )

    ListOption (
            section = _section,
            name    = 'extensions',
            default = 'zip,gz,bz2,rar',
            sep     = _separator,
            doc     = """Comma separated list of allowed file extensions
                      (without leading dot). Leave this empty to not restrict
                      the file types. The default is 'zip,gz,bz2,rar'. See also
                      the 'no_extension' option."""
        )

    Option (
            section = _section,
            name    = 'lighty_prefix',
            default = '/download/',
            doc     = """Must be set to the Lighttpd 'secdownload-uri-prefix'
                      configuration value if mod_secdownload is used. The final
                      download URL will be constructed using this value as the
                      first part after the root path, followed by the protected
                      part of the URL. If regular downloads are enabled, the
                      URL will be the same but without the protected part. Note
                      that if you do not start the value for this option with a
                      '/', an URL relative to the Trac environment root will be
                      created. This is in most cases not what you want!"""
        )

    Option (
            section = _section,
            name    = 'lighty_secret',
            default = '',
            doc     = """The secret key to protect the downloads (Lighttpd
                      'secdownload.secret' configuration value). The downloads
                      using mod_secdownload are disabled if this is left
                      empty (default)."""
        )

    IntOption (
            section = _section,
            name    = 'max_files',
            default = 0,
            doc     = """Maximum number of uploaded files. If this limit is
                      reached, no more uploads are allowed. Set this to '0' to
                      allow an unlimited number of uploads (default). Note that
                      this applies to local files only."""
        )

    IntOption (
            section = _section,
            name    = 'max_size',
            default = 524288,
            doc     = """Maximum allowed file size for uploaded files in
                      bytes. Note that a file has to be uploaded completely
                      before this can be checked. Set 'max_size' to '0' to not
                      restrict the file size. The default value is '524288'
                      (512 KiB). See also the 'max_total' configuration option.
                      Note that this applies to local files only."""
        )

    IntOption (
            section = _section,
            name    = 'max_total',
            default = 0,
            doc     = """Maximum total size of uploaded files in bytes. If a
                      new file upload would exceed this limit it will be
                      denied. Note that a file has to be uploaded completely
                      before this can be checked (unless the limit is already
                      reached). Set this to '0' to disable this feature
                      (default). This applies to local files only."""
        )

    BoolOption (
            section = _section,
            name    = 'no_extension',
            default = False,
            doc     = """In addition to the allowed file extensions specified
                      by the 'extensions' option, allow files with no extension
                      to be uploaded if this option is set to True. The default
                      value is False."""
        )

    ListOption (
            section = _section,
            name    = 'order',
            default = '!time',
            doc     = """Default order of the downloads table, specified as
                      comma separated list of field names. See 'show_fields'
                      for a list of allowed field names. You may prepend a '!'
                      to change the sort order of a given field (eg. use
                      '!name' to sort by file name in a descending order). Note
                      that the fields used here have to be included in the
                      'show_fields' list, too. The default value is '!time', so
                      latest downloads will be shown at the top of the
                      table."""
        )

    BoolOption (
            section = _section,
            name    = 'regular_downloads',
            default = False,
            doc     = """Enable regular downloads not using mod_secdownload.
                      Note that the webserver has to be configured to serve
                      the files in 'upload_dir'. This option will be ignored
                      unless 'lighty_secret' is empty. Regular downloads may
                      be used on other servers than Lighttpd, too, but keep in
                      mind that there are no further restrictions to access
                      these files."""
        )

    ListOption (
            section = _section,
            name    = 'schemes',
            default = 'http,https',
            doc     = """Comma separated list of allowed schemes for the remote
                      downloads. A remote download with another scheme can not
                      be created. To not restrict the remote URLs leave this
                      option empty. Note that URLs without a scheme are always
                      denied. The default is 'http,https'."""
        )

    ListOption (
            section = _section,
            name    = 'show_fields',
            default = 'name,size,description,url,time,checksum_md5,' \
                      'checksum_sha',
            sep     = _separator,
            doc     = """Comma separated list of fields to show on the
                      downloads index page. Valid options are: 'id', 'name',
                      'url', 'description', 'size', 'time', 'last_request',
                      'count', 'author', 'ip', 'component', 'version',
                      'milestone', 'platform', 'architecture', 'type',
                      'hidden', 'checksum_md5', 'checksum_sha'. Note that some
                      options are not displayed in a separate column but will
                      force a new table row, and some options are not displayed
                      at all (though they are valid). The order does not
                      matter."""
        )

    Option (
            section = _section,
            name    = 'temp_dir',
            default = '',
            doc     = """Temporary directory for uploaded files. If this is
                      empty (default) 'upload_dir' will be used. Note that it
                      is highly recommended to use a directory on the same
                      physical partition as 'upload_dir'. The directory must
                      exist and the user running Trac must have write access to
                      this directory."""
        )

    Option (
            section = _section,
            name    = 'title',
            default = 'Downloads',
            doc     = """Main navigation link title, and title of the downloads
                      index page. Defaults to 'Downloads'."""
        )

    BoolOption (
            section = _section,
            name    = 'trac_downloads',
            default = False,
            doc     = """If 'lighty_secret' is not set and 'regular_downloads'
                      is disabled, too, this option can be enabled to allow
                      downloads to be handled by Trac itself. This is disabled
                      by default."""
        )

    Option (
            section = _section,
            name    = 'upload_dir',
            default = '/var/lib/trac/files',
            doc     = """Directory to store uploaded files. The directory must
                      exist and the user running Trac must have write access
                      to this directory. The user running Lighttpd (or any
                      other webserver if regular downloads are used) must have
                      read permissions. The default value is
                      '/var/lib/trac/files'. Note that you can safely use the
                      same upload directory for multiple environments, the
                      uploaded files are automatically stored in subdirectories
                      for each environment."""
        )

    Option (
            section = _section,
            name    = 'url',
            default = 'download',
            doc     = """URL of the downloads page relative to the Trac
                      environment root (one word, no slashes). Defaults to
                      'download'."""
        )

    ListOption (
            section = _section,
            name    = 'wiki_prefix',
            default = 'download,secdownload',
            sep     = _separator,
            doc     = """Comma separated list of prefixes used in the wiki to
                      link to the downloads. The default value is
                      'download,secdownload'."""
        )

    def __getitem__ (self, key):
        """Convenient dictionary-like access to configuration options.

        Provides dictionary-like access in the form 'config [option]', but
        restricted to read-only access. List options are split automatically
        and the list is returned (an empty list if the field was empty). If
        the option does not exist a 'ConfigurationError' is raised.
        """
        value = self.get (key)
        if key in self._lists:
            if value:
                return value.split (self._separator)
            else:
                return []
        return value

    def get (self, key):
        """Provides access to configuration options.

        Returns the value of the option specified by 'key'. If the option does
        not exist a 'ConfigurationError' is raised. Note that this function
        will not automatically split list options, use the dictionary-like
        access if this is required.
        """
        if self.config.has_option (self._section, key):
            return self.config.get (self._section, key)
        else:
            raise ConfigurationError ('Option %s does not exist.' % key)

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: