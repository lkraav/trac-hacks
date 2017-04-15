# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2012-2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import hashlib

from trac.core import *
from trac.config import ListOption
from trac.web.chrome import Chrome
from trac.notification import NotifyEmail

from tracdiscussion.api import *


class DiscussionNotifyEmail(NotifyEmail):
    template_name = 'topic-notify-body.txt'
    forum = None
    topic = None
    message = None
    from_email = 'trac+discussion@localhost'
    to_recipients = []
    cc_recipients = []
    COLS = 75

    def __init__(self, env):
        NotifyEmail.__init__(self, env)
        self.prev_cc = []

    def notify(self, context, forum=None, topic=None, message=None):
        req = context.req
        # Store link to currently notifying forum, topic and message.
        self.forum = forum
        self.topic = topic
        self.message = message

        # Initialize template data.
        data = {
            'forum': self.forum,
            'topic': self.topic,
            'message': self.message,
            'prefix': self.config.get('notification',
                                      'smtp_subject_prefix')
        }
        if data['prefix'] == '__default__':
            data['prefix'] = self.env.project_name
        self.data.update({'discussion': data})

        # Which item notify about?
        if self.message:
            self.message['link'] = \
                self.env.abs_href.discussion('message', self.message['id'])
            self.template_name = 'message-notify-body.txt'
        elif self.topic:
            self.topic['link'] = \
                self.env.abs_href.discussion('topic', self.topic['id'])
            self.template_name = 'topic-notify-body.txt'

        # Send e-mail to all subscribers.
        self.cc_recipients = forum['subscribers'] + topic['subscribers'] + \
                             self.config.getlist('discussion',
                                                 'smtp_always_cc')

        # Render subject template and send notification.
        message = 'message-notify-subject.txt' if self.message \
                                               else 'topic-notify-subject.txt'
        template = Chrome(self.env).render_template(req, message, self.data,
                                                    'text/plain')
        subject = (to_unicode(template)).strip()
        NotifyEmail.notify(self, id, subject)

    def invite(self, forum=None, topic=None, recipients=None):
        # Store link to currently notifying forum.
        recipients = recipients or []
        self.forum = forum
        self.topic = topic

        # Initialize template data.
        data = {
            'forum': self.forum,
            'topic': self.topic,
            'prefix': self.config.get('notification', 'smtp_subject_prefix')
        }
        if data['prefix'] == '__default__':
            data['prefix'] = self.env.project_name
        self.data.update({'discussion': data})

        # Which item notify about?
        if self.topic:
            self.topic['link'] = \
                self.env.abs_href.discussion('topic', self.topic['id'])
            self.template_name = 'topic-invite-body.txt'
        elif self.forum:
            self.forum['link'] = \
                self.env.abs_href.discussion('forum', self.forum['id'])
            self.template_name = 'forum-invite-body.txt'

        # Send e-mail to all subscribers.
        self.cc_recipients = recipients + \
                             self.config.getlist('discussion',
                                                 'smtp_always_cc')

        # Render subject template and send notification.
        topic = 'topic-invite-subject.txt' if self.topic \
                                           else 'forum-invite-subject.txt'
        template = Chrome(self.env).render_template(topic, self.data,
                                                    'text/plain')
        subject = (to_unicode(template)).strip()
        NotifyEmail.notify(self, id, subject)

    def send(self, to_recipients, cc_recipients):
        header = {}

        # Add item specific e-mail header fields.
        if self.message:
            # ID of the message.
            header['Message-ID'] = self.get_message_email_id(
                self.message['id'])
            header['X-Trac-Message-ID'] = to_unicode(self.message['id'])
            header['X-Trac-Discussion-URL'] = self.message['link']

            # ID of replied message.
            if self.message['replyto'] != -1:
                reply_id = self.get_message_email_id(self.message['replyto'])
            else:
                reply_id = self.get_topic_email_id(self.message['topic'])
            header['In-Reply-To'] = reply_id
            header['References'] = reply_id
        elif self.topic:
            # ID of the message.
            header['Message-ID'] = self.get_topic_email_id(self.topic['id'])
            header['X-Trac-Topic-ID'] = to_unicode(self.topic['id'])
            header['X-Trac-Discussion-URL'] = self.topic['link']
        elif self.forum:
            # ID of the message.
            header['Message-ID'] = self.get_forum_email_id(self.forum['id'])
            header['X-Trac-Forum-ID'] = to_unicode(self.forum['id'])
            header['X-Trac-Discussion-URL'] = self.forum['link']
        else:
            # Should not happen.
            raise TracError('DiscussionPlugin internal error.')

        # Send e-mail.
        self.template = Chrome(self.env).load_template(self.template_name,
                                                       method='text')
        self.env.log.debug('to_recipients: %s cc_recipients: %s',
                           to_recipients, cc_recipients)
        NotifyEmail.send(self, to_recipients, cc_recipients, header)

    def get_recipients(self, item_id):
        return self.to_recipients, self.cc_recipients

    def get_message_email_id(self, message_id):
        # Generate a predictable, but sufficiently unique message ID.
        s = 'm.%s.%08d' % (self.config.get('project', 'url'), int(message_id))
        digest = hashlib.md5(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        email_id = '<%03d.%s@%s>' % (len(s), digest, host)
        return email_id

    def get_topic_email_id(self, topic_id):
        # Generate a predictable, but sufficiently unique topic ID.
        s = 't.%s.%08d' % (self.config.get('project', 'url'), int(topic_id))
        digest = hashlib.md5(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        email_id = '<%03d.%s@%s>' % (len(s), digest, host)
        return email_id

    def get_forum_email_id(self, forum_id):
        # Generate a predictable, but sufficiently unique topic ID.
        s = 'f.%s.%08d' % (self.config.get('project', 'url'), int(forum_id))
        digest = hashlib.md5(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        email_id = '<%03d.%s@%s>' % (len(s), digest, host)
        return email_id


class DiscussionEmailNotification(Component):
    """
        The e-mail notification component implements topic and message change
        listener interfaces and send e-mail notifications when topics and
        messages are created.
    """
    implements(IForumChangeListener, IMessageChangeListener,
               ITopicChangeListener)

    # Configuration options.

    smtp_always_cc = ListOption('discussion', 'smtp_always_cc', [],
    doc="""Always send discussion notifications to the listed e-mail 
    addresses.
    """)

    # IForumChangeListener methods.

    def forum_created(self, context, forum):
        # Send e-mail invitation.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.invite(forum, None, forum['subscribers'])

    def forum_changed(self, context, forum, old_forum):
        # Get new subscribers to topic.
        new_subscribers = [subscriber
                           for subscriber in forum['subscribers']
                           if subscriber not in old_forum['subscribers']]

        # We need to use complete forum dictionary.
        old_forum.update(forum)

        # Send e-mail invitation.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.invite(old_forum, None, new_subscribers)

    def forum_deleted(self, forum):
        self.log.debug('DiscussionEmailNotification.forum_deleted()')

    # ITopicChangeListener methods.

    def topic_created(self, context, topic):
        # Get forum of the topic.
        api = self.env[DiscussionApi]
        forum = api.get_forum(context, topic['forum'])

        # Send e-mail notification.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.notify(context, forum, topic, None)

    def topic_changed(self, context, topic, old_topic):
        if 'subscribers' in topic:
            # Get new subscribers to topic.
            new_subscribers = [subscriber
                               for subscriber in topic['subscribers']
                               if subscriber not in old_topic['subscribers']]

            # We need to use complete topic dictionary.
            old_topic.update(topic)

            # Get forum of the topic.
            api = self.env[DiscussionApi]
            forum = api.get_forum(context, old_topic['forum'])

            # Send e-mail invitation.
            notifier = DiscussionNotifyEmail(self.env)
            notifier.invite(forum, old_topic, new_subscribers)

    def topic_deleted(self, context, topic):
        pass

    # IMessageChangeListener methods.

    def message_created(self, context, message):
        # Get access to api component.
        api = self.env[DiscussionApi]
        forum = api.get_forum(context, message['forum'])
        topic = api.get_topic(context, message['topic'])

        # Send e-mail notification.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.notify(context, forum, topic, message)

    def message_changed(self, context, message, old_message):
        pass

    def message_deleted(self, context, message):
        pass
