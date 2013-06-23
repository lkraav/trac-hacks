# -*- coding: utf-8 -*-

# Standard imports.

# Deprecated as for Python 2.6.
try:
    import sets
except:
    pass


# Trac imports.
from trac.core import *
from trac.resource import *
from trac.config import ListOption

# TracTags imports.
from tractags.api import DefaultTagProvider, TagSystem

# Local imports.
from tracscreenshots.api import *

class ScreenshotsTagProvider(DefaultTagProvider):
    """
      Tag provider for screenshots.
    """
    realm = 'screenshots'

    def check_permission(self, perm, action):
        # Permission mapping for screenshot tagging operations.
        perm_map = {'create': 'SCREENSHOTS_ADD', 'modify': 'SCREENSHOTS_EDIT',
                    'view': 'SCREENSHOTS_VIEW'}
        # First check default provider permissions (TAGS_*), then
        # specifically for screenshot resources.
        # Hint: We do not care for fine-grained per-resource restrictions yet.
        realm_perm = perm('screenshots') 
        return super(ScreenshotsTagProvider,
                     self).check_permission(realm_perm, action) and \
            (perm_map[action] in realm_perm or
             action == 'modify' and perm_map['create'] in realm_perm)

class ScreenshotsTags(Component):
    """
        The tags module implements plugin's ability to create tags related
        to screenshots.
    """
    implements(IScreenshotChangeListener)

    # Configuration options.
    additional_tags = ListOption('screenshots', 'additional_tags',
      'author,components,versions,name', doc = 'Additional tags that will be '
      'created for submitted screenshots. Possible values are: author, '
      'components, versions, name, description.')

    # IScreenshotChangeListener methods.

    def screenshot_created(self, req, screenshot):
        # Create temporary resource.
        resource = Resource('screenshots', to_unicode(screenshot['id']))

        # Delete tags of screenshot with same ID for sure.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(req, resource)

        # Add tags of new screenshot.
        new_tags = self._get_tags(screenshot)
        tag_system.add_tags(req, resource, new_tags)

    def screenshot_changed(self, req, screenshot, old_screenshot):
        # Update old screenshot with new values.
        old_screenshot.update(screenshot)

        # Create temporary resource.
        resource = Resource('screenshots', to_unicode(old_screenshot['id']))

        # Delete old tags.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(req, resource)

        # Add new ones.
        new_tags = self._get_tags(old_screenshot)
        tag_system.add_tags(req, resource, new_tags)

    def screenshot_deleted(self, req, screenshot):
        # Create temporary resource.
        resource = Resource('screenshots', to_unicode(screenshot['id']))

        # Delete tags of screenshot.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(req, resource)

    def _get_tags(self, screenshot):
        # Prepare tag names.
        self.log.debug("additional_tags: %s" % (self.additional_tags,))
        tags = []
        if 'author' in self.additional_tags:
           tags = [screenshot['author']]
        if 'components' in self.additional_tags and screenshot['components']:
            tags += [component for component in screenshot['components']]
        if 'versions' in self.additional_tags and screenshot['versions']:
            tags += [version for version in screenshot['versions']]
        if 'name' in self.additional_tags and screenshot['name']:
            tags += [screenshot['name']]
        if 'description' in self.additional_tags and screenshot['description']:
            tags += [screenshot['description']]
        if screenshot['tags']:
            tags += screenshot['tags'].split()
        return sorted(tags)

    def _get_stored_tags(self, req, screenshot_id):
        tag_system = TagSystem(self.env)
        resource = Resource('screenshots', to_unicode(screenshot_id))
        tags = tag_system.get_tags(req, resource)
        return sorted(tags)
