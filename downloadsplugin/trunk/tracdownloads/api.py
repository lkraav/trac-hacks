# -*- coding: utf-8 -*-

import datetime
import os
import shutil
import unicodedata

from trac.config import BoolOption, IntOption, ListOption, Option, PathOption
from trac.core import Component, ExtensionPoint, Interface, TracError
from trac.resource import Resource
from trac.mimeview import Mimeview
from trac.web.chrome import add_script, add_stylesheet
from trac.util.datefmt import format_datetime, to_timestamp, utc
from trac.util.text import to_unicode


class IDownloadChangeListener(Interface):
    """Extension point interface for components that require notification
    when downloads are created, modified, or deleted.
    """

    def download_created(context, download):
        """Called when a download is created. Only argument `download` is
        a dictionary with download field values.
        """

    def download_changed(context, download, old_download):
        """Called when a download is modified.
        `old_download` is a dictionary containing the previous values of the
        fields and `download` is a dictionary with new values.
        """

    def download_deleted(context, download):
        """Called when a download is deleted. `download` argument is
        a dictionary with values of fields of just deleted download.
        """


class DownloadsApi(Component):

    change_listeners = ExtensionPoint(IDownloadChangeListener)

    path = PathOption('downloads', 'path', '../downloads',
        doc="Path where to store uploaded downloads.")

    ext = ListOption('downloads', 'ext', 'zip,gz,bz2,rar',
        doc="""List of file extensions allowed to upload. Set to 'all'
            to specify that any file extensions is allowed.
            """)

    max_size = IntOption('downloads', 'max_size', 268697600,
        """Maximum allowed file size (in bytes) for downloads. Default
        is 256 MB.
        """)

    visible_fields = ListOption('downloads', 'visible_fields',
        'id,file,description,size,time,count,author,tags,component,version,'
        'architecture,platform,type',
        doc="""List of downloads table fields that should be visible to
            users on Downloads section.
            """)

    download_sort = Option('downloads', 'download_sort', 'time',
        """Column by which downloads list will be sorted. Possible values
        are: id, file, description, size, time, count, author, tags,
        component, version, architecture, platform, type.
        """)

    download_sort_direction = Option('downloads', 'download_sort_direction',
        'desc',
        """Direction of downloads list sorting. Possible values are: asc,
        desc.
        """)

    architecture_sort = Option('downloads', 'architecture_sort', 'name',
        """Column by which architectures list will be sorted. Possible
        values are: id, name, description.
        """)

    architecture_sort_direction = Option('downloads',
        'architecture_sort_direction', 'asc',
        """Direction of architectures list sorting. Possible values are:
        asc, desc.
        """)

    platform_sort = Option('downloads', 'platform_sort', 'name',
        """Column by which platforms list will be sorted. Possible values
        are: id, name, description.
        """)

    platform_sort_direction = Option('downloads', 'platform_sort_direction',
        'asc',
        """Direction of platforms list sorting. Possible values are:
        asc, desc.
        """)

    type_sort = Option('downloads', 'type_sort', 'name',
        """Column by which types list will be sorted. Possible values are:
        id, name, description.
        """)

    type_sort_direction = Option('downloads', 'type_sort_direction', 'asc',
        """Direction of types list sorting. Possible values are: asc,
        desc.
        """)

    unique_filename = BoolOption('downloads', 'unique_filename', False,
        doc="If enabled checks if uploaded file has unique name.")

    def _get_items(self, table, columns, where='', values=(), order_by='',
                   desc=False):
        if where:
            where = 'WHERE %s' % where
        desc = 'DESC' if desc else 'ASC'
        items = []
        with self.env.db_query as db:
            if order_by:
                order_by = " ORDER BY %s %s" % (db.quote(order_by), desc)
            for row in db("""
                    SELECT %s FROM %s %s %s
                    """ % (','.join(db.quote(col) for col in columns),
                           db.quote(table), where, order_by),
                          values):
                row = dict(zip(columns, row))
                items.append(row)
        return items

    def get_versions(self, order_by='name', desc=False):
        versions = self._get_items('version', ('name', 'description'),
                                   order_by=order_by, desc=desc)

        # Add IDs to versions according to selected sorting.
        id = 0
        for version in versions:
            id += 1
            version['id'] = id
        return versions

    def get_components(self, order_by='', desc=False):
        components = self._get_items('component',
                                     ('name', 'description'),
                                     order_by=order_by, desc=desc)

        # Add IDs to versions according to selected sorting.
        id = 0
        for component in components:
            id += 1
            component['id'] = id
        return components

    def get_downloads(self, order_by='id', desc=False):
        downloads = self._get_items('download',
                                    ('id', 'file', 'description', 'size',
                                     'time', 'count', 'author', 'tags',
                                     'component', 'version', 'architecture',
                                     'platform', 'type'),
                                    order_by=order_by, desc=desc)

        # Replace field IDs with appropriate objects.
        for download in downloads:
            download['architecture'] = self.get_architecture(
                download['architecture'])
            download['platform'] = self.get_platform(download['platform'])
            download['type'] = self.get_type(download['type'])
        return downloads

    def get_new_downloads(self, start, stop, order_by='time', desc=False):
        return self._get_items('download',
                               ('id', 'file', 'description', 'size',
                                'time', 'count', 'author', 'tags',
                                'component', 'version', 'architecture',
                                'platform', 'type'),
                               'time BETWEEN %s AND'
                               ' %s', (start, stop), order_by=order_by,
                               desc=desc)

    def get_architectures(self, order_by='id', desc=False):
        return self._get_items('architecture',
                               ('id', 'name', 'description'),
                               order_by=order_by, desc=desc)

    def get_platforms(self, order_by='id', desc=False):
        return self._get_items('platform',
                               ('id', 'name', 'description'),
                               order_by=order_by, desc=desc)

    def get_types(self, order_by='id', desc=False):
        return self._get_items('download_type',
                               ('id', 'name', 'description'),
                               order_by=order_by, desc=desc)

    # Get one item functions.

    def _get_item(self, table, columns, where='', values=()):
        if where:
            where = 'WHERE %s' % where
        with self.env.db_query as db:
            for row in db("""
                    SELECT %s FROM %s %s
                    """ % (','.join(db.quote(col) for col in columns),
                           db.quote(table), where),
                          values):
                row = dict(zip(columns, row))
                return row
        return None

    def get_download(self, id):
        return self._get_item('download',
                              ('id', 'file', 'description', 'size', 'time',
                               'count', 'author', 'tags', 'component',
                               'version', 'architecture', 'platform', 'type'),
                              'id = %s', (id,))

    def get_download_by_time(self, time):
        return self._get_item('download',
                              ('id', 'file', 'description', 'size', 'time',
                               'count', 'author', 'tags', 'component',
                               'version', 'architecture', 'platform', 'type'),
                              'time = %s', (time,))

    def get_download_by_file(self, file):
        return self._get_item('download',
                              ('id', 'file', 'description', 'size', 'time',
                               'count', 'author', 'tags', 'component',
                               'version', 'architecture', 'platform', 'type'),
                              'file = %s', (file,))

    def get_architecture(self, id):
        architecture = self._get_item('architecture',
                                      ('id', 'name', 'description'),
                                      'id = %s', (id,))
        if not architecture:
            architecture = {'id': 0, 'name': '', 'description': ''}
        return architecture

    def get_architecture_by_name(self, name):
        architecture = self._get_item('architecture',
                                      ('id', 'name', 'description'),
                                      'name = %s', (name,))
        if not architecture:
            architecture = {'id': 0, 'name': '', 'description': ''}
        return architecture

    def get_platform(self, id):
        platform = self._get_item('platform',
                                  ('id', 'name', 'description'), 'id = %s',
                                  (id,))
        if not platform:
            platform = {'id': 0, 'name': '', 'description': ''}
        return platform

    def get_platform_by_name(self, name):
        platform = self._get_item('platform',
                                  ('id', 'name', 'description'), 'name = %s',
                                  (name,))
        if not platform:
            platform = {'id': 0, 'name': '', 'description': ''}
        return platform

    def get_type(self, id):
        type = self._get_item('download_type',
                              ('id', 'name', 'description'), 'id = %s',
                              (id,))
        if not type:
            type = {'id': 0, 'name': '', 'description': ''}
        return type

    def get_type_by_name(self, name):
        type = self._get_item('download_type',
                              ('id', 'name', 'description'), 'name = %s',
                              (name,))
        if not type:
            type = {'id': 0, 'name': '', 'description': ''}
        return type

    def get_description(self):
        for value, in self.env.db_query("""
                SELECT value FROM system WHERE name = 'downloads_description'
                """):
            return value

    # Add item functions.

    def _add_item(self, table, item):
        fields = item.keys()
        values = item.values()
        with self.env.db_transaction as db:
            db("""INSERT INTO %s (%s) VALUES (%s)
                """ % (db.quote(table),
                       ','.join(db.quote(f) for f in fields),
                       ','.join(['%s'] * len(fields))),
               tuple(values))

    def add_download(self, download):
        self._add_item('download', download)

    def add_architecture(self, architecture):
        self._add_item('architecture', architecture)

    def add_platform(self, platform):
        self._add_item('platform', platform)

    def add_type(self, type):
        self._add_item('download_type', type)

    # Edit item functions.

    def _edit_item(self, table, id, item):
        fields = item.keys()
        values = item.values()
        with self.env.db_transaction as db:
            db("""
                UPDATE %s SET %s WHERE id=%%s
                """ % (db.quote(table),
                       ','.join('%s=%%s' % db.quote(f) for f in fields)),
               tuple(values + [id]))

    def edit_download(self, id, download):
        self._edit_item('download', id, download)

    def edit_architecture(self, id, architecture):
        self._edit_item('architecture', id, architecture)

    def edit_platform(self, id, platform):
        self._edit_item('platform', id, platform)

    def edit_type(self, id, type):
        self._edit_item('download_type', id, type)

    def edit_description(self, description):
        self.env.db_transaction("""
                UPDATE system SET value = %s
                WHERE name = 'downloads_description'
                """, (description,))

    # Delete item functions.

    def _delete_item(self, table, id):
        with self.env.db_transaction as db:
            db("DELETE FROM %s WHERE id = %%s" % db.quote(table), (id,))

    def _delete_item_ref(self, table, column, id):
        with self.env.db_transaction as db:
            db("UPDATE %s SET %s=NULL WHERE %s=%%s"
               % (db.quote(table), db.quote(column), db.quote(column)),
               (id,))

    def delete_download(self, id):
        self._delete_item('download', id)

    def delete_architecture(self, id):
        self._delete_item('architecture', id)
        self._delete_item_ref('download', 'architecture', id)

    def delete_platform(self, id):
        self._delete_item('platform', id)
        self._delete_item_ref('download', 'platform', id)

    def delete_type(self, id):
        self._delete_item('download_type', id)
        self._delete_item_ref('download', 'type', id)

    # Misc database access functions.

    def _get_attribute(self, table, column, where='', values=()):
        if where:
            where = "WHERE %s" % where
        with self.env.db_query as db:
            for row in db("""
                    SELECT %s FROM %s %s
                    """ % (db.quote(column), db.quote(table), where), values):
                return row[0]
        return None

    def get_download_id_from_file(self, file):
        return self._get_attribute('download', 'file', 'id = %s', (file,))

    def get_number_of_downloads(self, download_ids=None):
        where = "WHERE id IN (%s)" \
                % ','.join(to_unicode(did) for did in download_ids) \
                if download_ids else ''
        for row in self.env.db_query("""
                SELECT SUM(count) FROM download %s
                """ % (where,)):
            return row[0]
        return None

    # Process request methods

    def process_downloads(self, context):
        data = {}
        modes = self._get_modes(context)
        self._do_actions(context, modes, data)

        data['authname'] = context.req.authname
        data['time'] = format_datetime(datetime.datetime.now(utc))
        data['realm'] = context.resource.realm

        add_stylesheet(context.req, 'common/css/wiki.css')
        add_stylesheet(context.req, 'downloads/css/downloads.css')
        add_stylesheet(context.req, 'downloads/css/admin.css')
        add_script(context.req, 'common/js/wikitoolbar.js')

        return modes[-1] + '.html', {'downloads': data}

    # Internal functions.

    def _get_modes(self, context):
        # Get request arguments.
        page = context.req.args.get('page')
        action = context.req.args.get('action')

        # Determine mode.
        if context.resource.realm == 'downloads-admin':
            if page == 'downloads':
                if action == 'post-add':
                    return ['downloads-post-add', 'admin-downloads-list']
                elif action == 'post-edit':
                    return ['downloads-post-edit', 'admin-downloads-list']
                elif action == 'delete':
                    return ['downloads-delete', 'admin-downloads-list']
                else:
                    return ['admin-downloads-list']
            elif page == 'architectures':
                if action == 'post-add':
                    return ['architectures-post-add',
                            'admin-architectures-list']
                elif action == 'post-edit':
                    return ['architectures-post-edit',
                            'admin-architectures-list']
                elif action == 'delete':
                    return ['architectures-delete',
                            'admin-architectures-list']
                else:
                    return ['admin-architectures-list']
            elif page == 'platforms':
                if action == 'post-add':
                    return ['platforms-post-add', 'admin-platforms-list']
                elif action == 'post-edit':
                    return ['platforms-post-edit', 'admin-platforms-list']
                elif action == 'delete':
                    return ['platforms-delete', 'admin-platforms-list']
                else:
                    return ['admin-platforms-list']
            elif page == 'types':
                if action == 'post-add':
                    return ['types-post-add', 'admin-types-list']
                elif action == 'post-edit':
                    return ['types-post-edit', 'admin-types-list']
                elif action == 'delete':
                    return ['types-delete', 'admin-types-list']
                else:
                    return ['admin-types-list']
        elif context.resource.realm == 'downloads-core':
            if action == 'get-file':
                return ['get-file']
            elif action == 'post-add':
                return ['downloads-post-add', 'downloads-list']
            elif action == 'edit':
                return ['description-edit', 'downloads-list']
            elif action == 'post-edit':
                return ['description-post-edit', 'downloads-list']
            else:
                return ['downloads-list']
        else:
            pass

    def _do_actions(self, context, actions, data):
        has_tags = self.env.is_component_enabled('tractags.api.TagEngine')

        for action in actions:
            if action == 'get-file':
                context.req.perm.require('DOWNLOADS_VIEW')

                # Get request arguments.
                download_id = context.req.args.get('id') or 0
                download_file = context.req.args.get('file')

                # Get download.
                if download_id:
                    download = self.get_download(download_id)
                else:
                    download = self.get_download_by_file(download_file)

                # Check if requested download exists.
                if not download:
                    raise TracError("File not found.")

                # Check resource based permission.
                context.req.perm.require('DOWNLOADS_VIEW',
                                         Resource('downloads',
                                                  download['id']))

                # Get download file path.
                filename = os.path.basename(download['file'])
                filepath = os.path.join(self.path,
                                        to_unicode(download['id']),
                                        filename)
                filepath = os.path.normpath(filepath)

                # Increase downloads count.
                new_download = {'count': download['count'] + 1}

                # Edit download.
                self.edit_download(download['id'], new_download)

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.download_changed(context, new_download, download)

                # Guess mime type.
                with open(filepath.encode('utf-8'), 'r') as fileobj:
                    file_data = fileobj.read(1000)
                mimeview = Mimeview(self.env)
                mime_type = mimeview.get_mimetype(filepath, file_data)
                if not mime_type:
                    mime_type = 'application/octet-stream'
                if 'charset=' not in mime_type:
                    charset = mimeview.get_charset(file_data, mime_type)
                    mime_type = mime_type + '; charset=' + charset

                # Return uploaded file to request.
                context.req.send_header('Content-Disposition',
                                        'attachment;filename="%s"'
                                        % os.path.normpath(download['file']))
                context.req.send_header('Content-Description',
                                        download['description'])
                context.req.send_file(filepath.encode('utf-8'), mime_type)

            elif action == 'downloads-list':
                context.req.perm.require('DOWNLOADS_VIEW')

                self.log.debug("visible_fields: %s", self.visible_fields)

                # Get form values.
                order = context.req.args.get('order') or self.download_sort
                if 'desc' in context.req.args:
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.download_sort_direction == 'desc'

                data['order'] = order
                data['desc'] = desc
                data['has_tags'] = has_tags
                data['description'] = self.get_description()
                data['downloads'] = self.get_downloads(order, desc)
                data['visible_fields'] = self.visible_fields

                # Component, versions, etc. are needed only for new
                # download add form.
                if 'DOWNLOADS_ADD' in context.req.perm:
                    data['components'] = self.get_components()
                    data['versions'] = self.get_versions()
                    data['architectures'] = self.get_architectures()
                    data['platforms'] = self.get_platforms()
                    data['types'] = self.get_types()

            elif action == 'admin-downloads-list':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values
                order = context.req.args.get('order') or self.download_sort
                if 'desc' in context.req.args:
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.download_sort_direction == 'desc'
                download_id = int(context.req.args.get('download') or 0)

                data['order'] = order
                data['desc'] = desc
                data['has_tags'] = has_tags
                data['download'] = self.get_download(download_id)
                data['downloads'] = self.get_downloads(order, desc)
                data['components'] = self.get_components()
                data['versions'] = self.get_versions()
                data['architectures'] = self.get_architectures()
                data['platforms'] = self.get_platforms()
                data['types'] = self.get_types()

            elif action == 'description-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

            elif action == 'description-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                description = context.req.args.get('description')

                # Set new description.
                self.edit_description(description)

            elif action == 'downloads-post-add':
                context.req.perm.require('DOWNLOADS_ADD')

                # Get form values.
                file, filename, file_size = self._get_file_from_req(context)
                download = {
                    'file': filename,
                    'description': context.req.args.get('description'),
                    'size': file_size,
                    'time': to_timestamp(datetime.datetime.now(utc)),
                    'count': 0,
                    'author': context.req.authname,
                    'tags': context.req.args.get('tags'),
                    'component': context.req.args.get('component'),
                    'version': context.req.args.get('version'),
                    'architecture': context.req.args.get('architecture'),
                    'platform': context.req.args.get('platform'),
                    'type': context.req.args.get('type')
                }

                # Upload file to DB and file storage.
                self._add_download(context, download, file)

                file.close()

            elif action == 'downloads-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                download_id = context.req.args.get('id')
                old_download = self.get_download(download_id)
                download = {
                    'description': context.req.args.get('description'),
                    'tags': context.req.args.get('tags'),
                    'component': context.req.args.get('component'),
                    'version': context.req.args.get('version'),
                    'architecture': context.req.args.get('architecture'),
                    'platform': context.req.args.get('platform'),
                    'type': context.req.args.get('type')
                }

                # Edit Download.
                self.edit_download(download_id, download)

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.download_changed(context, download, old_download)

            elif action == 'downloads-delete':
                context.req.perm.require('DOWNLOADS_ADMIN')

                selection = context.req.args.getlist('selection')
                if selection:
                    for download_id in selection:
                        download = self.get_download(download_id)
                        self.log.debug("download: %s", download)
                        self._delete_download(context, download)

            elif action == 'admin-architectures-list':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values
                order = context.req.args.get('order') or \
                        self.architecture_sort
                if 'desc' in context.req.args:
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.architecture_sort_direction == 'desc'
                architecture_id = \
                    int(context.req.args.get('architecture') or 0)

                # Display architectures.
                data['order'] = order
                data['desc'] = desc
                data['architecture'] = self.get_architecture(architecture_id)
                data['architectures'] = self.get_architectures(order, desc)

            elif action == 'architectures-post-add':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                architecture = {
                    'name': context.req.args.get('name'),
                    'description': context.req.args.get('description')
                }

                # Add architecture.
                self.add_architecture(architecture)

            elif action == 'architectures-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                architecture_id = context.req.args.get('id')
                architecture = {
                    'name': context.req.args.get('name'),
                    'description': context.req.args.get('description')
                }

                # Add architecture.
                self.edit_architecture(architecture_id, architecture)

            elif action == 'architectures-delete':
                context.req.perm.require('DOWNLOADS_ADMIN')

                selection = context.req.args.getlist('selection')
                if selection:
                    for architecture_id in selection:
                        self.delete_architecture(architecture_id)

            elif action == 'admin-platforms-list':
                context.req.perm.require('DOWNLOADS_ADMIN')

                order = context.req.args.get('order') or self.platform_sort
                if 'desc' in context.req.args:
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.platform_sort_direction == 'desc'
                platform_id = int(context.req.args.get('platform') or 0)

                data['order'] = order
                data['desc'] = desc
                data['platform'] = self.get_platform(platform_id)
                data['platforms'] = self.get_platforms(order, desc)

            elif action == 'platforms-post-add':
                context.req.perm.require('DOWNLOADS_ADMIN')

                platform = {
                    'name': context.req.args.get('name'),
                    'description': context.req.args.get('description')
                }
                self.add_platform(platform)

            elif action == 'platforms-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                platform_id = context.req.args.get('id')
                platform = {
                    'name': context.req.args.get('name'),
                    'description': context.req.args.get('description')
                }
                self.edit_platform(platform_id, platform)

            elif action == 'platforms-delete':
                context.req.perm.require('DOWNLOADS_ADMIN')

                selection = context.req.args.getlist('selection')
                if selection:
                    for platform_id in selection:
                        self.delete_platform(platform_id)

            elif action == 'admin-types-list':
                context.req.perm.require('DOWNLOADS_ADMIN')

                order = context.req.args.get('order') or self.type_sort
                if 'desc' in context.req.args:
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.type_sort_direction == 'desc'
                platform_id = int(context.req.args.get('type') or 0)

                data['order'] = order
                data['desc'] = desc
                data['type'] = self.get_type(platform_id)
                data['types'] = self.get_types(order, desc)

            elif action == 'types-post-add':
                context.req.perm.require('DOWNLOADS_ADMIN')

                type = {
                    'name': context.req.args.get('name'),
                    'description': context.req.args.get('description')
                }
                self.add_type(type)

            elif action == 'types-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                type_id = context.req.args.get('id')
                type = {
                    'name': context.req.args.get('name'),
                    'description': context.req.args.get('description')
                }
                self.edit_type(type_id, type)

            elif action == 'types-delete':
                context.req.perm.require('DOWNLOADS_ADMIN')

                selection = context.req.args.getlist('selection')
                if selection:
                    for type_id in selection:
                        self.delete_type(type_id)

    def _add_download(self, context, download, file):
        # Check for file name uniqueness.
        if self.unique_filename:
            if self.get_download_by_file(download['file']):
                raise TracError("File with same name is already uploaded "
                                "and unique file names are enabled.")

        # Check correct file type.
        name, ext = os.path.splitext(download['file'])
        if not (ext[1:].lower() in self.ext) and not ('all' in self.ext):
            raise TracError("Unsupported file type.")

        # Check for maximum file size.
        if 0 <= self.max_size < download['size']:
            raise TracError("Maximum file size: %s bytes" % self.max_size,
                            "Upload failed")

        # Add new download to DB.
        self.add_download(download)

        # Get inserted download by time to get its ID.
        download = self.get_download_by_time(download['time'])

        # Prepare file paths.
        path = os.path.normpath(os.path.join(self.path,
                                             to_unicode(download['id'])))
        filepath = os.path.normpath(os.path.join(path, download['file']))

        self.log.debug("path: %s", path)
        self.log.debug("filepath: %s", filepath)

        # Store uploaded image.
        try:
            os.mkdir(path.encode('utf-8'))
            with open(filepath.encode('utf-8'), 'wb+') as fileobj:
                file.seek(0)
                shutil.copyfileobj(file, fileobj)
        except Exception, error:
            self.delete_download(download['id'])
            self.log.debug(error)
            try:
                os.remove(filepath.encode('utf-8'))
            except:
                pass
            try:
                os.rmdir(path.encode('utf-8'))
            except:
                pass
            raise TracError("Error storing file %s. Does the directory "
                            "specified in path config option of [downloads] "
                            "section of trac.ini exist?" % download['file'])

        # Notify change listeners.
        for listener in self.change_listeners:
            listener.download_created(context, download)

    def _delete_download(self, context, download):
        try:
            self.delete_download(download['id'])
            path = os.path.join(self.path, to_unicode(download['id']))
            filepath = os.path.join(path, download['file'])
            path = os.path.normpath(path)
            filepath = os.path.normpath(filepath)
            os.remove(filepath)
            os.rmdir(path)

            # Notify change listeners.
            for listener in self.change_listeners:
                listener.download_deleted(context, download)
        except:
            pass

    def _get_file_from_req(self, context):
        file = context.req.args['file']

        # Test if file is uploaded.
        if not hasattr(file, 'filename') or not file.filename:
            raise TracError("No file uploaded.")

        # Get file size.
        if hasattr(file.file, 'fileno'):
            size = os.fstat(file.file.fileno())[6]
        else:
            # Seek to end of file to get its size.
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        if size == 0:
            raise TracError("Can't upload empty file.")

        # Try to normalize the filename to unicode NFC if we can.
        # Files uploaded from OS X might be in NFD.
        self.log.debug("input filename: %s", file.filename)
        filename = unicodedata.normalize('NFC',
                                         to_unicode(file.filename, 'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        self.log.debug("output filename: %s", filename)

        return file.file, filename, size
