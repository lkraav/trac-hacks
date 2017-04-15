# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from datetime import timedelta

from trac.perm import PermissionCache
from trac.resource import Resource
from trac.test import MockRequest
from trac.util.datefmt import to_datetime, utc
from trac.web.href import Href
from trac.web.chrome import web_context

from tracdiscussion.api import DiscussionApi
from tracdiscussion.tests.test import DiscussionBaseTestCase


class DiscussionApiTestCase(DiscussionBaseTestCase):
    def setUp(self):
        DiscussionBaseTestCase.setUp(self)

        self.req = MockRequest(self.env, authname='editor', method='GET')
        self.req.perm = PermissionCache(self.env, 'editor')

        self.actions = ('DISCUSSION_ADMIN', 'DISCUSSION_MODERATE',
                        'DISCUSSION_ATTACH', 'DISCUSSION_APPEND',
                        'DISCUSSION_VIEW')

        self.forum = Resource(self.realm, 'forum/1')
        self.topic = Resource(self.realm, 'topic/2')
        self.message = Resource(self.realm, 'message/3', None, self.topic)

        self.api = DiscussionApi(self.env)

    # Helpers

    def _prepare_context(self, req):
        context = web_context(req)
        return context

    # Tests

    def test_available_actions(self):
        for action in self.actions:
            self.assertFalse(action not in self.perms.get_actions())

    def test_meta_inherit_actions(self):
        user = 'anonymous'
        self.assertEqual(set(self.perms.get_user_permissions(user))
                         .intersection(self.actions), set())
        user = 'visitor'
        self.perms.grant_permission(user, 'DISCUSSION_VIEW')
        self.assertTrue(set(self.perms.get_user_permissions(user))
                        .issuperset(self.actions[4:]))
        self.assertEqual(set(self.perms.get_user_permissions(user))
                         .intersection(self.actions[:4]), set())
        user = 'msg+file-editor'
        self.perms.grant_permission(user, 'DISCUSSION_APPEND')
        self.assertTrue(set(self.perms.get_user_permissions(user))
                        .issuperset(self.actions[3:]))
        self.assertEqual(set(self.perms.get_user_permissions(user))
                         .intersection(self.actions[:3]), set())
        user = 'msg-only-editor'
        self.perms.grant_permission(user, 'DISCUSSION_ATTACH')
        self.assertTrue(set(self.perms.get_user_permissions(user))
                        .issuperset(self.actions[2:]))
        self.assertEqual(set(self.perms.get_user_permissions(user))
                         .intersection(self.actions[:2]), set())
        user = 'moderator'
        self.perms.grant_permission(user, 'DISCUSSION_MODERATE')
        self.assertTrue(set(self.perms.get_user_permissions(user))
                        .issuperset(self.actions[1:]))
        self.assertEqual(set(self.perms.get_user_permissions(user))
                         .intersection(self.actions[:1]), set())
        user = 'admin'
        self.perms.grant_permission(user, 'DISCUSSION_ADMIN')
        self.assertTrue(set(self.perms.get_user_permissions(user))
                        .issuperset(self.actions))

    def test_get_resource_realms(self):
        self.assertEqual(list(self.api.get_resource_realms()), [self.realm])

    def test_get_resource_description(self):
        desc = self.api.get_resource_description  # method shorthand
        self.assertEqual(desc(self.forum), 'Forum forum1')
        self.assertEqual(desc(self.forum, 'summary'),
                         'Forum forum1 - forum-subject1')
        self.assertEqual(desc(self.topic), 'Topic #2')
        self.assertEqual(desc(self.topic, 'summary'), 'Topic #2 (top2)')
        self.assertEqual(desc(self.message), 'Message #3')
        self.assertEqual(desc(self.message, 'summary'), 'Message #3')

    def test_get_resource_url(self):
        url = self.api.get_resource_url  # method shorthand
        self.assertEqual(url(self.forum, Href('/')), '/discussion/forum/1')
        self.assertEqual(url(self.topic, Href('/')), '/discussion/topic/2')
        self.assertEqual(url(self.message, Href('/')),
                         '/discussion/topic/2#message_3')

    def test_resource_exists(self):
        self.assertTrue(self.api.resource_exists(self.forum))
        self.assertFalse(self.api.resource_exists(self.forum(id='forum/3')))
        self.assertTrue(self.api.resource_exists(self.topic))
        self.assertFalse(self.api.resource_exists(self.forum(id='topic/4')))
        self.assertTrue(self.api.resource_exists(self.message))
        self.assertFalse(self.api.resource_exists(self.forum(id='message/6')))

    def test_get_group(self):
        self.assertEqual('forum_group1',
                         self.api.get_group(1)['name'])

    def test_get_forum(self):
        context = self._prepare_context(self.req)
        context.has_tags = False
        forum = self.api.get_forum(context, 1)
        self.assertEqual(
            set(['id', 'name', 'author', 'time', 'forum_group', 'subject',
                 'description', 'moderators', 'subscribers',
                 'unregistered_subscribers']),
            set(forum.keys())
        )
        self.assertEqual('forum1', forum['name'])

    def test_get_forums(self):
        context = self._prepare_context(self.req)
        context.has_tags = False
        context.users = ('user',)
        context.visited_forums = dict()
        context.visited_topics = dict()
        self.assertEqual(
            set(self.api.get_forums(context)[0].keys()),
            set(['id', 'name', 'author', 'time', 'forum_group', 'subject',
                 'description', 'moderators', 'subscribers',
                 'topics', 'replies', 'lasttopic', 'lastreply',
                 'new_replies', 'new_topics', 'unregistered_subscribers']))

    def test_get_changed_forums(self):
        start = to_datetime(None, tzinfo=utc)
        stop = start - timedelta(seconds=1)
        self.assertEqual(
            list(self.api.get_changed_forums(start, stop)), [])

    def test_get_topic(self):
        context = self._prepare_context(self.req)
        topic = self.api.get_topic(context, 1)
        self.assertEqual(
            set(['id', 'forum', 'author', 'time', 'status', 'subject', 'body',
                 'priority', 'subscribers', 'unregistered_subscribers']),
            set(topic.keys())
        )
        self.assertEqual('top1', topic['subject'])

    def test_get_forum_subject(self):
        self.assertEqual('forum-subject1',
                         self.api.get_forum_subject(1))

    def test_get_topic_subject(self):
        self.assertEqual('top2', self.api.get_topic_subject(2))

    def test_get_topics(self):
        context = self._prepare_context(self.req)
        context.has_tags = False
        context.users = ('user',)
        context.visited_forums = dict()
        context.visited_topics = dict()
        self.assertEqual(
            set(self.api.get_topics(1, context)[0].keys()),
            set(['id', 'forum', 'author', 'time', 'status', 'subject', 'body',
                 'priority', 'subscribers', 'replies', 'lastreply',
                 'new_replies', 'unregistered_subscribers']))

    def test_get_topics_count(self):
        self.assertEqual(self.api.get_topics_count(1), 2)

    def test_get_flat_messages(self):
        self.assertEqual(
            self.api.get_flat_messages(1), [{
                'id': 1, 'author': None, 'body': u'msg1', 'replyto': -1,
                'time': 1400361500}]
        )

    def test_get_flat_messages_by_forum(self):
        self.assertEqual(
            self.api.get_flat_messages_by_forum(2), [{
                'id': 5, 'topic': 3, 'author': None, 'body': u'msg5',
                'replyto': -1, 'time': 1400362600}]
        )

    def test_get_message(self):
        self.assertEqual(
            self.api.get_message(1), {
                'id': 1, 'forum': 1, 'topic': 1, 'author': None,
                'body': u'msg1',
                'replyto': -1, 'time': 1400361500}
        )

    def test_get_messages_count(self):
        self.assertEqual(self.api.get_messages_count(2), 3)

    def test_get_replies(self):
        self.assertEqual(
            self.api.get_replies(2), [{
                'id': 3, 'author': None, 'body': u'msg3', 'replyto': 2,
                'time': 1400362200}]
        )

    def test_modify_group(self):
        self.assertEqual('None', self.api.get_group(2)['name'])
        self.api.add_group(dict(name='newgroup', description='desc'))
        self.assertEqual('newgroup', self.api.get_group(2)['name'])
        self.api.edit_group(2, dict(description='changed'))
        self.assertEqual('changed',
                         self.api.get_group(2)['description'])
        self.api.delete_group(2)
        self.assertEqual('None', self.api.get_group(2)['name'])

    def test_modify_forum(self):
        context = self._prepare_context(self.req)
        context.has_tags = False
        self.assertEqual(None, self.api.get_forum(context, 3))
        self.api.add_forum(dict(name='newforum',
                                description='forum-desc3',
                                moderators='', subscribers=''))
        self.assertEqual('newforum', self.api.get_forum(context, 3)['name'])
        self.api.edit_forum(3, dict(description='changed'))
        self.assertEqual('changed',
                         self.api.get_forum(context, 3)['description'])
        self.assertEqual(None, self.api.get_forum(context, 3)['forum_group'])
        self.api.set_group(3, 1)
        self.assertEqual(1, self.api.get_forum(context, 3)['forum_group'])
        self.api.delete_forum(3)
        self.assertEqual(None, self.api.get_forum(context, 3))

    def test_modify_topic(self):
        context = self._prepare_context(self.req)
        self.assertEqual(None, self.api.get_topic(context, 4))
        self.api.add_topic(dict(subject='newtopic',
                                body='topic-desc4', forum=2,
                                status='locked', subscribers=''))
        self.assertEqual('newtopic',
                         self.api.get_topic(context, 4)['subject'])
        self.api.edit_topic(4, dict(body='changed'))
        self.assertEqual('changed', self.api.get_topic(context, 4)['body'])
        self.api.set_forum(4, 1)
        self.assertEqual(1, self.api.get_topic(context, 4)['forum'])
        self.api.delete_topic(4)
        self.assertEqual(None, self.api.get_topic(context, 4))

    def test_modify_message(self):
        self.assertEqual(None, self.api.get_message(6))
        self.api.add_message(dict(body='msg6', forum=1, topic=2,
                                  replyto=3))
        self.assertEqual('msg6', self.api.get_message(6)['body'])
        self.api.edit_message(6, dict(body='changed'))
        self.assertEqual('changed', self.api.get_message(6)['body'])
        # Check propagation of topic change into topic message.
        self.api.set_forum(2, 2)
        self.assertEqual(2, self.api.get_message(6)['forum'])
        self.api.delete_message(6)
        self.assertEqual(None, self.api.get_message(6))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionApiTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
