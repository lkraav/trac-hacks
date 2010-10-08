# -*- coding: utf-8 -*-

# Deprecated as for Python 2.6.
try:
    import sets
except:
    pass

from tracdownloads.api import *
from trac.core import *
from trac.resource import Resource
from trac.mimeview import Context

from tractags.api import DefaultTagProvider, TagSystem

class DownloadsTagProvider(DefaultTagProvider):
    """
      Tag provider for downloads.
    """
    realm = 'downloads'

    # Other methods.

    def check_permission(self, perm, operation):
        # Permission table for download tags.
        permissions = {'view' : 'DOWNLOADS_VIEW', 'modify' : 'DOWNLOADS_ADMIN'}

        # First check permissions in default provider then for downloads.
        return super(DownloadsTagProvider, self).check_permission(perm,
          operation) and permissions[operation] in perm

class DownloadsTags(Component):
    """
        The tags module implements plugin's ability to create tags related
        to downloads.
    """
    implements(IDownloadChangeListener)

    realm = 'downloads'

    # IDownloadChangeListener methods.

    def download_created(self, context, download):
        # Check proper permissions to modify tags.
        if not context.req.perm.has_permission('TAGS_MODIFY'):
            return

        # Create temporary resource.
        resource = Resource(self.realm, download['id'])

        # Delete tags of download with same ID for sure.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(context.req, resource)

        # Add tags of new download.
        new_tags = self._get_tags(download)
        self.log.debug('tags: %s' % (new_tags,))
        tag_system.add_tags(context.req, resource, new_tags)

    def download_changed(self, context, download, old_download):
        # Check proper permissions to modify tags.
        if not context.req.perm.has_permission('TAGS_MODIFY'):
            return

        # Check if tags has to be updated.
        if not self._has_tags_changed(download):
           return

        # Update old download with new values.
        old_download.update(download)

        # Create temporary resource.
        resource = Resource(self.realm, old_download['id'])

        # Delete old tags.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(context.req, resource)

        # Add new ones.
        new_tags = self._get_tags(old_download)
        tag_system.add_tags(context.req, resource, new_tags)

    def download_deleted(self, context, download):
        # Check proper permissions to modify tags.
        if not context.req.perm.has_permission('TAGS_MODIFY'):
            return

        # Create temporary resource.
        resource = Resource(self.realm, download['id'])

        # Delete tags of download.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(context.req, resource)

    # Private methods

    def _has_tags_changed(self, download):
        # Return True if there is any attribute that generate tags in download.
        return download.has_key('author') or download.has_key('component') or \
          download.has_key('version') or download.has_key('architecture') or \
          download.has_key('platform') or download.has_key('type') or \
          download.has_key('tags')

    def _get_tags(self, download):
        # Translate architecture, platform and type ID to its names.
        self._resolve_ids(download)

        # Prepare tag names.
        tags = [download['author']]
        if download['component']:
            tags += [download['component']]
        if download['version']:
            tags += [download['version']]
        if download['architecture']:
            tags += [download['architecture']]
        if download['platform']:
            tags += [download['platform']]
        if download['type']:
            tags += [download['type']]
        if download['tags']:
            tags += download['tags'].split()
        return sorted(tags)

    def _get_stored_tags(self, context, download_id):
        tag_system = TagSystem(self.env)
        resource = Resource(self.realm, download_id)
        tags = tag_system.get_tags(context.req, resource)
        return sorted(tags)

    def _resolve_ids(self, download):
        # Create context.
        context = Context('downloads-core')
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Resolve architecture platform and type names.
        api = self.env[DownloadsApi]
        architecture = api.get_architecture(context, download['architecture'])
        platform = api.get_platform(context, download['platform'])
        type = api.get_type(context, download['type'])
        download['architecture'] = architecture['name']
        download['platform'] = platform['name']
        download['type'] = type['name']
