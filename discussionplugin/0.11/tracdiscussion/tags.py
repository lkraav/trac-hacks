# -*- coding: utf-8 -*-

# Genshi imports.
from genshi.builder import tag
from genshi.filters.transform import Transformer

# Trac imports.
from trac.core import implements
from trac.resource import Resource
from trac.config import ListOption

# TracTags imports.
from tractags.api import DefaultTagProvider, TagSystem

# Local interfaces.
from tracdiscussion.api import DiscussionApi, IForumChangeListener
from tracdiscussion.api import ITopicChangeListener


class DiscussionTagProvider(DefaultTagProvider):
    """Tag provider for discussion forums and topics.

    The module implements plugin's ability to create tags related
    to discussion forums and topics.
    """

    implements(IForumChangeListener, ITopicChangeListener)

    realm = 'discussion'

    # Configuration options
    automatic_forum_tags = ListOption('discussion', 'automatic_forum_tags',
      'name,author', doc = "Tags that will be created automatically from "
      "discussion forums fields. Possible values are: name, author.")
    automatic_topic_tags = ListOption('discussion', 'automatic_topic_tags',
      'author,status', doc = "Tags that will be created automatically from "
      "discussion topics fields. Possible values are: author, status.")

    # ITagProvider method overwrite
    def check_permission(self, perm, operation):
        permissions = {'view': 'DISCUSSION_VIEW',
                       'modify': 'DISCUSSION_MODIFY'}

        # Check tag permissions (in default provider), then for discussion.
        return super(DiscussionTagProvider, self)
                     .check_permission(perm, operation) and \
                     permissions[operation] in perm

    # IForumChangeListener methods

    def forum_created(self, context, forum):
        # Create temporary resource to update tags.
        resource = Resource(self.realm, 'forum/%s' % forum['id'])
        new_tags = self._get_forum_tags(forum)
        self._update_tags(context.req, resource, new_tags)

    def forum_changed(self, context, forum, old_forum):
        resource = Resource(self.realm, 'forum/%s' % forum['id'])
        new_tags = self._get_forum_tags(forum)
        self._update_tags(context.req, resource, new_tags)

    def forum_deleted(self, context, forum_id):
        resource = Resource(self.realm, 'forum/%s' % forum_id)
        self._delete_tags(context.req, resource)

    # ITopicChangeListener methods

    def topic_created(self, context, topic):
        resource = Resource(self.realm, 'topic/%s' % topic['id'])
        new_tags = self._get_topic_tags(topic)
        self._update_tags(context.req, resource, new_tags)

    def topic_changed(self, context, topic, old_topic):
        resource = Resource(self.realm, 'topic/%s' % topic['id'])
        new_tags = self._get_topic_tags(topic)
        self._update_tags(context.req, resource, new_tags)

    def topic_deleted(self, context, topic):
        resource = Resource(self.realm, 'topic/%s' % topic['id'])
        self._delete_tags(context.req, resource)

    # Internal methods

    def _update_tags(self, req, resource, new_tags):
        # Get recorded tags for the discussion resource.
        tag_system = TagSystem(self.env)
        old_tags = self._get_stored_tags(req, resource)

        self.log.debug("Setting discussion tags: %s" % new_tags)

        # Replace with new tags, if different.
        if old_tags != new_tags:
            tag_system.set_tags(req, resource, new_tags)
            return True
        return False

    def _delete_tags(self, req, resource):
        # Delete tags of the resource.
        tag_system = TagSystem(self.env)
        tag_system.delete_tags(req, resource)

    def _get_stored_tags(self, req, resource):
        # Return tags associated to resource.
        tag_system = TagSystem(self.env)
        tags = tag_system.get_tags(req, resource)
        return sorted(tags)

    def _get_forum_tags(self, forum):
        tags = []
        if forum.has_key('tags'):
            tags += forum['tags']
        if 'name' in self.automatic_forum_tags and forum['name']:
            if not forum['name'] in tags:
                tags.append(forum['name'])
        if 'author' in self.automatic_forum_tags and forum['author']:
            if forum['author'] not in tags:
                tags.append(forum['author'])
        return sorted(tags)

    def _get_topic_tags(self, topic):
        tags = []
        if topic.has_key('tags'):
            tags += topic['tags']
        if 'author' in self.automatic_topic_tags and topic['author']:
            if not topic['author'] in tags:
                tags.append(topic['author'])
        if 'status' in self.automatic_topic_tags and len(topic['status']):
            for status in topic['status']:
                if not status in tags:
                    tags.append(status)
        return sorted(tags)
