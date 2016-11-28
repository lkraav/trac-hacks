# -*- coding: utf-8 -*-

import datetime
import os.path
import unicodedata

from trac.admin import AdminCommandError, IAdminCommandProvider
from trac.config import Option
from trac.core import Component, ExtensionPoint, TracError, implements
from trac.mimeview import Context
from trac.perm import PermissionCache
from trac.util import as_int
from trac.util.datefmt import format_datetime, to_timestamp, utc
from trac.util.text import pretty_size, print_table, to_unicode
from trac.util.translation import _

from tracdownloads.api import DownloadsApi, IDownloadChangeListener


class FakeRequest(object):
    def __init__(self, env, authname):
        self.perm = PermissionCache(env, authname)


class DownloadsConsoleAdmin(Component):
    """
        The consoleadmin module implements downloads plugin administration
        via trac-admin command.
    """
    implements(IAdminCommandProvider)

    change_listeners = ExtensionPoint(IDownloadChangeListener)

    consoleadmin_user = Option('downloads', 'consoleadmin_user', 'anonymous',
        doc="""User who's permissions will be used to upload download.
               He/she should have TAGS_MODIFY permissions.""")

    # IAdminCommandProvider

    def get_admin_commands(self):
        yield ('download list', '', "Show uploaded downloads", None,
               self._do_list)
        yield ('download add',
               "<file> [description=<description>]\n"
               "                    [author=<author>]\n"
               "                    [tags='<tag1> <tag2> ...']\n"
               "                    [component=<component>]\n"
               "                    [version=<version>]\n"
               "                    [architecture=<architecture>]\n"
               "                    [platform=<platform>]\n"
               "                    [type=<type>]\n",
               'Add new download', None, self._do_add)
        yield ('download remove', '<filename> | <download_id>',
               "Remove uploaded download", None, self._do_remove)

    # Internal methods.

    def _do_list(self):
        # Get downloads API component.
        api = self.env[DownloadsApi]

        # Print uploaded download
        downloads = api.get_downloads()
        print_table([
            (download['id'],
             download['file'],
             pretty_size(download['size']),
             format_datetime(download['time']),
             download['component'],
             download['version'],
             download['architecture']['name'],
             download['platform']['name'],
             download['type']['name'])
            for download in downloads], [
            'ID', 'Filename', 'Size', 'Uploaded', 'Component',
            'Version',
            'Architecture', 'Platform', 'Type'
        ])

    def _do_add(self, filename, *arguments):
        # Get downloads API component.
        api = self.env[DownloadsApi]

        # Create context.
        context = Context('downloads-consoleadmin')
        context.req = FakeRequest(self.env, self.consoleadmin_user)

        # Open file object.
        fileobj, filename, file_size = self._get_file(filename)

        # Create download dictionary from arbitrary attributes.
        download = {
            'file': filename,
            'size': file_size,
            'time': to_timestamp(datetime.datetime.now(utc)),
            'count': 0
        }

        # Read optional attributes from arguments.
        for argument in arguments:
            # Check correct format.
            argument = argument.split("=")
            if len(argument) != 2:
                AdminCommandError(_("Invalid format of download attribute: "
                                    "%(value)s", value=argument))
            name, value = argument

            # Check known arguments.
            if name not in ('description', 'author', 'tags', 'component',
                            'version', 'architecture', 'platform', 'type'):
                raise AdminCommandError(_("Invalid download attribute: "
                                          "%(value)s", value=name))

            # Transform architecture, platform and type name to ID.
            if name == 'architecture':
                value = api.get_architecture_by_name(value)['id']
            elif name == 'platform':
                value = api.get_platform_by_name(value)['id']
            elif name == 'type':
                value = api.get_type_by_name(value)['id']

            # Add attribute to download.
            download[name] = value

        self.log.debug(download)

        # Upload file to DB and file storage.
        api._add_download(context, download, fileobj)

        fileobj.close()

    def _do_remove(self, identifier):
        api = self.env[DownloadsApi]

        # Create context.
        context = Context('downloads-consoleadmin')
        context.req = FakeRequest(self.env, self.consoleadmin_user)

        # Get download by ID or filename.
        download_id = as_int(identifier, None)
        if download_id is not None:
            download = api.get_download(download_id)
        else:
            download = api.get_download_by_file(identifier)

        # Check if download exists.
        if not download:
            raise AdminCommandError(_("Invalid download identifier: "
                                      "%(value)s", value=identifier))

        # Delete download by ID.
        api.delete_download(download_id)

    @staticmethod
    def _get_file(filename):
        # Open file and get its size
        fileobj = open(filename, 'rb')
        size = os.fstat(fileobj.fileno())[6]

        # Check non-empty file.
        if size == 0:
            raise TracError("Can't upload empty file.")

        # Try to normalize the filename to unicode NFC if we can.
        # Files uploaded from OS X might be in NFD.
        filename = unicodedata.normalize('NFC', to_unicode(filename, 'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)

        return fileobj, filename, size
