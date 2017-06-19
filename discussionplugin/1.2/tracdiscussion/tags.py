# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import implements
from trac.resource import Resource, get_resource_description, resource_exists
from trac.config import ListOption

from tractags.api import DefaultTagProvider, TagSystem

from tracdiscussion.api import IForumChangeListener, ITopicChangeListener


class DiscussionTagProvider(DefaultTagProvider):
    """Tag provider for discussion forums and topics.

    The module implements plugin's ability to create tags related
    to discussion forums and topics.
    """

    implements(IForumChangeListener, ITopicChangeListener)

    realm = 'discussion'

    automatic_forum_tags = ListOption('discussion', 'automatic_forum_tags',
        'name,author', doc="""Tags that will be created automatically from
        discussion forums fields. Possible values are: name, author.
        """)

    automatic_topic_tags = ListOption('discussion', 'automatic_topic_tags',
        'author,status', doc="""Tags that will be created automatically
        from discussion topics fields. Possible values are: author, status.
        """)

    # IForumChangeListener methods

    def forum_created(self, context, forum):
        # Create temporary resource to update tags.
        resource = Resource(self.realm, 'forum/%s' % forum['id'])
        new_tags = self._get_forum_tags(forum)
        self._update_tags(context.req, resource, new_tags)

    def forum_changed(self, context, forum, old_forum):
        resource = Resource(self.realm, 'forum/%s' % old_forum['id'])
        # ToDo: Delete tags for old_forum.
        new_tags = self._get_forum_tags(forum)
        self._update_tags(context.req, resource, new_tags)

    def forum_deleted(self, context, forum_id):
        resource = Resource(self.realm, 'forum/%s' % forum_id)
        TagSystem(self.env).delete_tags(context.req, resource)

    # ITopicChangeListener methods

    def topic_created(self, context, topic):
        resource = Resource(self.realm, 'topic/%s' % topic['id'])
        new_tags = self._get_topic_tags(topic)
        self._update_tags(context.req, resource, new_tags)

    def topic_changed(self, context, topic, old_topic):
        resource = Resource(self.realm, 'topic/%s' % old_topic['id'])
        # ToDo: Delete tags for old_topic.
        new_tags = self._get_topic_tags(topic)
        self._update_tags(context.req, resource, new_tags)

    def topic_deleted(self, context, topic):
        resource = Resource(self.realm, 'topic/%s' % topic['id'])
        TagSystem(self.env).delete_tags(context.req, resource)

    # ITagProvider methods

    def check_permission(self, perm, action):
        map_ = {'view': 'DISCUSSION_VIEW', 'modify': 'DISCUSSION_APPEND'}
        # Check tag permissions (in default provider), then for discussion.
        return super(DiscussionTagProvider, self) \
                   .check_permission(perm, action) and map_[action] in perm

    def describe_tagged_resource(self, req, resource):
        if not self.check_permission(req.perm(resource), 'view'):
            return ''
        if resource_exists(self.env, resource):
            return get_resource_description(self.env, resource, 'compact')

    # Internal methods

    def _update_tags(self, req, resource, new_tags):
        tag_system = TagSystem(self.env)
        # Get recorded tags associated to the discussion resource.
        old_tags = tag_system.get_tags(req, resource)
        # Replace with new tags, if different.
        if old_tags != new_tags:
            tag_system.set_tags(req, resource, new_tags)
            self.log.debug("Setting discussion tags: %s", new_tags)
            return True
        return False

    def _get_forum_tags(self, forum):
        tags = []
        if 'tags' in forum:
            tags += forum['tags']
        if 'name' in self.automatic_forum_tags and forum['name']:
            if not forum['name'] in tags:
                tags.append(forum['name'])
        if 'author' in self.automatic_forum_tags and forum['author']:
            if forum['author'] not in tags:
                tags.append(forum['author'])
        return set(tags)

    def _get_topic_tags(self, topic):
        tags = []
        if 'tags' in topic:
            tags += topic['tags']
        if 'author' in self.automatic_topic_tags and topic['author']:
            if topic['author'] not in tags:
                tags.append(topic['author'])
        if 'status' in self.automatic_topic_tags and len(topic['status']):
            for status in topic['status']:
                if status not in tags:
                    tags.append(status)
        return set(tags)
