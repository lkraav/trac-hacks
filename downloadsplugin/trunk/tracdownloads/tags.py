# -*- coding: utf-8 -*-

from trac.config import ListOption
from trac.core import Component, implements
from trac.resource import Resource
from tractags.api import DefaultTagProvider, TagSystem

from tracdownloads.api import DownloadsApi, IDownloadChangeListener


class DownloadsTagProvider(DefaultTagProvider):
    """
      Tag provider for downloads.
    """
    realm = 'downloads'

    def check_permission(self, perm, operation):
        # Permission table for download tags.
        permissions = {'view': 'DOWNLOADS_VIEW', 'modify': 'DOWNLOADS_ADD'}

        # First check permissions in default provider then for downloads.
        return super(DownloadsTagProvider, self)\
                   .check_permission(perm, operation) and \
               permissions[operation] in perm


class DownloadsTags(Component):
    """
        The tags module implements plugin's ability to create tags related
        to downloads.
    """
    implements(IDownloadChangeListener)

    realm = 'downloads'

    additional_tags = ListOption('downloads', 'additional_tags',
        'author,component,version,architecture,platform,type', doc="""
        Additional tags that will be created for submitted downloads.
        Possible values are: author, component, version, architecture,
        platform, type.
        """)

    # IDownloadChangeListener methods

    def download_created(self, context, download):
        # Check proper permissions to modify tags.
        if 'TAGS_MODIFY' not in context.req.perm:
            return

        # Create temporary resource.
        resource = Resource(self.realm, download['id'])

        # Delete tags of download with same ID for sure.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(context.req, resource)

        # Add tags of new download.
        new_tags = self._get_tags(download)
        self.log.debug("tags: %s", new_tags)
        tag_system.add_tags(context.req, resource, new_tags)

    def download_changed(self, context, download, old_download):
        # Check proper permissions to modify tags.
        if 'TAGS_MODIFY' not in context.req.perm:
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
        if 'TAGS_MODIFY' not in context.req.perm:
            return

        # Create temporary resource.
        resource = Resource(self.realm, download['id'])

        # Delete tags of download.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(context.req, resource)

    # Private methods

    def _has_tags_changed(self, download):
        # Return True for any attribute that generate tags in download.
        return 'author' in download or 'component' in download or \
               'version' in download or 'architecture' in download or \
               'platform' in download or 'type' in download or \
               'tags' in download

    def _get_tags(self, download):
        # Translate architecture, platform and type ID to its names.
        self._resolve_ids(download)

        # Prepare tag names.
        self.log.debug("additional_tags: %s", self.additional_tags)
        tags = []
        if 'author' in self.additional_tags and \
                download['author']:
            tags += [download['author']]
        if 'component' in self.additional_tags and \
                download['component']:
            tags += [download['component']]
        if 'version' in self.additional_tags and \
                download['version']:
            tags += [download['version']]
        if 'architecture' in self.additional_tags and \
                download['architecture']:
            tags += [download['architecture']]
        if 'platform' in self.additional_tags and \
                download['platform']:
            tags += [download['platform']]
        if 'type' in self.additional_tags and \
                download['type']:
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
        # Resolve architecture platform and type names.
        api = self.env[DownloadsApi]
        architecture = api.get_architecture(download['architecture'])
        platform = api.get_platform(download['platform'])
        type = api.get_type(download['type'])
        download['architecture'] = architecture['name']
        download['platform'] = platform['name']
        download['type'] = type['name']
