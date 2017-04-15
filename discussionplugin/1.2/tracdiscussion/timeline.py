# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Component, implements
from trac.resource import Resource, get_resource_url
from trac.timeline import ITimelineEventProvider
from trac.util.html import html as tag
from trac.web.chrome import add_stylesheet, web_context
from trac.wiki.formatter import format_to_oneliner
from trac.util.datefmt import to_datetime, utc

from tracdiscussion.api import DiscussionApi


class DiscussionTimeline(Component):
    """[opt] Provides timeline events for forum, topic and message changes.
    """

    implements(ITimelineEventProvider)

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if 'DISCUSSION_VIEW' in req.perm:
            yield ('discussion',
                   self.config.get('discussion', 'title') + ' changes')

    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("Discussion timeline events start: %s, "
                       "stop: %s, filters: %s", start, stop, filters)

        if 'discussion' in filters and 'DISCUSSION_VIEW' in req.perm:
            api = DiscussionApi(self.env)

            context = web_context(req)
            context.realm = 'discussion-core'

            add_stylesheet(req, 'discussion/css/discussion.css')

            # Get forum events.
            for forum in api.get_changed_forums(start, stop):
                # Return event.
                title = 'New forum %s created' % forum['name']
                description = tag(
                    format_to_oneliner(self.env, context, forum['subject']),
                    ' - ',
                    format_to_oneliner(self.env, context,
                                       forum['description']))
                yield ('discussion unsolved',
                       to_datetime(forum['time'], utc), forum['author'],
                       (Resource('discussion', 'forum/%s' % forum['id']),
                        title, description), self)

            # Get topic events.
            for topic in api.get_changed_topics(start, stop):
                title = 'New topic on %s created' % topic['forum_name']
                description = format_to_oneliner(self.env, context,
                                                 topic['subject'])
                yield ('discussion solved'
                       if 'solved' in topic['status']
                       else 'discussion unsolved',
                       to_datetime(topic['time'], utc), topic['author'],
                       (Resource('discussion', 'topic/%s' % topic['id']),
                        title, description), self)

            # Get message events.
            for message in api.get_changed_messages(start, stop):
                title = 'New reply on %s created' % message['forum_name']
                description = format_to_oneliner(self.env, context,
                                                 message['topic_subject'])
                yield ('discussion unsolved',
                       to_datetime(message['time'], utc), message['author'],
                       (Resource('discussion', 'message/%s' % message['id'],
                                 None,  # Discussion messages are unversioned.
                                 Resource('discussion', 'topic/%s'
                                          % message['topic'])),
                        title, description), self)

    def render_timeline_event(self, context, field, event):
        env = self.env
        # Decompose event data.
        resource, title, description = event[3]

        if 'description' == field:
            return tag(description)
        elif 'title' == field:
            return tag(title)
        elif 'url' == field:
            return get_resource_url(env, resource, context.href)
