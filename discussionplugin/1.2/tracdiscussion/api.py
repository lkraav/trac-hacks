# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2012-2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
from copy import deepcopy
import functools

from trac.attachment import AttachmentModule, ILegacyAttachmentPolicyDelegate
from trac.core import ExtensionPoint, Interface, TracError
from trac.core import implements
from trac.config import IntOption, Option
from trac.perm import IPermissionRequestor, PermissionError, PermissionSystem
from trac.resource import IResourceManager, Resource
from trac.util import as_bool, as_int, to_list
from trac.util.datefmt import datetime_now, to_timestamp, utc
from trac.util.presentation import Paginator
from trac.util.text import to_unicode
from trac.web.chrome import add_link, add_script, add_stylesheet
from trac.web.chrome import exception_to_unicode, add_ctxtnav
from trac.web.href import Href

from tracdiscussion.model import DiscussionDb
from tracdiscussion.util import format_to_oneliner_no_links
from tracdiscussion.util import prepare_topic, topic_status_from_list

try:
    from tractags.api import TagSystem
except ImportError:
    pass


def is_tags_enabled(env):
    return env.is_enabled('tractags.api.TagSystem') and \
           env.is_enabled('tracdiscussion.tags.DiscussionTags')


class IDiscussionFilter(Interface):
    """Extension point interface for components that want to filter
    discussion topics and messages before their addition.
    """

    def filter_topic(context, topic):
        """ Called before new topic creation. May return tuple (False,
        <error_message>) or (True, <topic>) where <error_message> is a
        message that will be displayed when topic creation will be canceled
        and <topic> is modified topic that will be added.
        """

    def filter_message(context, message):
        """ Called before new message creation. May return tuple (False,
        <error_message>) or (True, <message>) where <error_message> is a
        message that will be displayed when message creation will be canceled
        and <message> is modified message that will be added.
        """


class IForumChangeListener(Interface):
    """Extension point interface for components that require notification
    when new forums are created, modified or deleted.
    """

    def forum_created(context, forum):
        """Called when a forum is created. Argument `forum` is a dictionary
        with forum attributes.
        """

    def forum_changed(context, forum, old_forum):
        """Called when a forum is modified. `old_forum` is a dictionary
        containing the previous values of the forum attributes and `forum` is
        a dictionary with new values that has changed.
        """

    def forum_deleted(context, forum):
        """Called when a forum is deleted. Argument `forum` is a dictionary
        with values of attributes of just deleted forum.
        """


class ITopicChangeListener(Interface):
    """Extension point interface for components that require notification
    when new forum topics are created, modified or deleted.
    """

    def topic_created(context, topic):
        """Called when a topic is created. Argument `topic` is a dictionary
        with topic attributes.
        """

    def topic_changed(context, topic, old_topic):
        """Called when a topic is modified. `old_topic` is a dictionary
        containing the previous values of the topic attributes and `topic` is
        a dictionary with new values that has changed.
        """

    def topic_deleted(context, topic):
        """Called when a topic is deleted. Argument `topic` is a dictionary
        with values of attributes of just deleted topic.
        """


class IMessageChangeListener(Interface):
    """Extension point interface for components that require notification
    when new forum messages are created, modified or deleted.
    """

    def message_created(context, message):
        """Called when a message is created. Argument `message` is a
        dictionary with message attributes.
        """

    def message_changed(context, message, old_message):
        """Called when a message is modified. `old_message` is a dictionary
        containing the previous values of the message attributes and
        `message` is a dictionary with new values that has changed.
        """

    def message_deleted(context, message):
        """Called when a message is deleted. Argument `message` is a
        dictionary with values of attributes of just deleted message.
        """


class DiscussionApi(DiscussionDb):
    """[main] Provides essential definitions including configuration options,
    permission actions and request handling instructions.
    """
    # Hint: Methods for database access within plugin's schema are inherited
    #       from tracdiscussion.model.DiscussionDb.

    implements(ILegacyAttachmentPolicyDelegate, IPermissionRequestor,
               IResourceManager)

    default_topic_display = Option('discussion', 'default_topic_display',
        'classic', doc="""Default display mode for forum topics list.""")

    default_message_display = Option('discussion', 'default_message_display',
        'tree', doc="""Default display mode for topic messages list.""")

    forum_sort = Option('discussion', 'forum_sort', 'lasttopic',
        doc="""Column by which will be sorted forum lists. Possible values
        are: id, group, name, subject, time, moderators, description,
        topics, replies, lasttopic, lastreply.
        """)

    forum_sort_direction = Option('discussion', 'forum_sort_direction', 'asc',
        doc="""Direction of forum lists sorting. Possible values are:
        asc, desc.
        """)

    topic_sort = Option('discussion', 'topic_sort', 'lastreply', doc="""
        Column by which will be sorted topic lists. Possible values are:
        id, forum, subject, time, author, body, replies, lastreply.
        """)

    topic_sort_direction = Option('discussion', 'topic_sort_direction', 'asc',
        doc="""Direction of topic lists sorting. Possible values are:
        asc, desc.
        """)

    topics_per_page = IntOption('discussion', 'topics_per_page', 30,
        doc="""Number of topics per page in topic list.""")

    messages_per_page = IntOption('discussion', 'messages_per_page', 50,
        doc="""Number of messages per page in message list.""")

    discussion_filters = ExtensionPoint(IDiscussionFilter)
    forum_change_listeners = ExtensionPoint(IForumChangeListener)
    message_change_listeners = ExtensionPoint(IMessageChangeListener)
    topic_change_listeners = ExtensionPoint(ITopicChangeListener)

    realm = 'discussion'

    # ILegacyAttachmentPolicyDelegate method

    def check_attachment_permission(self, action, username, resource, perm):
        if resource.parent.realm == 'discussion':
            if action in ('ATTACHMENT_CREATE', 'ATTACHMENT_DELETE'):
                return 'DISCUSSION_ATTACH' in perm(resource.parent)
            elif action == 'ATTACHMENT_VIEW':
                return 'DISCUSSION_VIEW' in perm(resource.parent)

    # IPermissionRequestor method

    def get_permission_actions(self):
        action = ('DISCUSSION_VIEW', 'DISCUSSION_APPEND',
                  'DISCUSSION_ATTACH', 'DISCUSSION_MODERATE')
        append = (action[1], action[:1])
        attach = (action[2], action[:2])
        moderate = (action[3], action[:3])
        admin = ('DISCUSSION_ADMIN', action)
        return [action[0], append, attach, moderate, admin]

    # IResourceManager methods

    def get_resource_realms(self):
        yield self.realm

    def get_resource_url(self, resource, href, **kwargs):
        if resource.id:
            type, id = self._parse_resource_id(resource)
            # Topic view has one anchor per message.
            if 'message' == type:
                return '%s#message_%s' % \
                       (self.get_resource_url(resource.parent, href),
                        resource.id.split('/')[-1])
            return href(resource.realm, type, id, **kwargs)
        else:
            return href(resource.realm, **kwargs)

    def get_resource_description(self, resource, format=None, **kwargs):
        type_, id_ = self._parse_resource_id(resource)
        if 'forum' == type_:
            forum = self.get_item('forum', ('id', 'name', 'subject'),
                                  where='id=%s', values=(id_,))
            if 'compact' == format:
                return '#%s' % forum['id']
            elif 'summary' == format:
                return 'Forum %s - %s' % (forum['name'], forum['subject'])
            else:
                return 'Forum %s' % forum['name']
        elif 'topic' == type_:
            topic = self.get_item('topic', ('id', 'subject'), where='id=%s',
                                  values=(id_,))
            if 'compact' == format:
                return '#%s' % topic['id']
            elif 'summary' == format:
                return 'Topic #%s (%s)' % (topic['id'], topic['subject'])
            else:
                return 'Topic #%s' % topic['id']
        elif 'message' == type_:
            if 'compact' == format:
                return '#%s' % id_
            else:
                return 'Message #%s' % id_

    def resource_exists(self, resource):
        type, id = self._parse_resource_id(resource)
        if type in ('forum', 'topic', 'message'):
            return self.get_item(type, ('id',), where='id=%s',
                                 values=(id,)) is not None

    # Main request processing function.

    def process_discussion(self, context):
        req = context.req
        req.perm.require('DISCUSSION_VIEW')

        # Get request items and actions.
        self._prepare_context(context)
        actions = self._get_actions(context)

        # Get session data.
        context.visited_forums = eval(req.session.get('visited-forums')
                                      or '{}')
        context.visited_topics = eval(req.session.get('visited-topics')
                                      or '{}')

        # Perform actions.
        self._do_actions(context, actions)

        # Update session data.
        req.session['visited-topics'] = to_unicode(context.visited_topics)
        req.session['visited-forums'] = to_unicode(context.visited_forums)

        # Fill up template data structure.
        context.data['users'] = context.users
        context.data['moderators'] = \
            self.get_users(None, 'DISCUSSION_MODERATE')
        context.data['has_tags'] = context.has_tags
        context.data['group'] = context.group
        context.data['forum'] = context.forum
        context.data['topic'] = context.topic
        context.data['message'] = context.message
        context.data['moderator'] = context.moderator
        context.data['authname'] = req.authname
        context.data['authemail'] = context.authemail
        context.data['realm'] = context.realm
        context.data['mode'] = actions[-1]
        context.data['time'] = datetime_now(utc)
        context.data['env'] = self.env
        context.data['format_to_oneliner_no_links'] = \
            functools.partial(format_to_oneliner_no_links, self.env)

        # Add context navigation.
        if context.forum:
            add_ctxtnav(req, 'Forum Index', req.href.discussion())
        if context.topic:
            add_ctxtnav(req,
                        format_to_oneliner_no_links(self.env, context,
                                                    context.forum['name']),
                        req.href.discussion('forum', context.forum['id']),
                        context.forum['name'])
        if context.message:
            add_ctxtnav(req,
                        format_to_oneliner_no_links(self.env, context,
                                                    context.topic['subject']),
                        req.href.discussion('topic', context.topic['id']),
                        context.topic['subject'])

        # Add CSS styles and scripts.
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'discussion/css/discussion.css')
        add_stylesheet(req, 'discussion/css/admin.css')
        add_script(req, 'common/js/trac.js')
        add_script(req, 'common/js/search.js')
        add_script(req, 'common/js/wikitoolbar.js')
        add_script(req, 'discussion/js/discussion.js')

        # Determine template name.
        context.template = self._get_template(context, actions)
        self.log.debug("Discussion template: %s data: %s", context.template,
                       context.data)
        return context.template, {'discussion': context.data}

    # Internal methods.

    def _parse_resource_id(self, resource):
        """Return discussion resource type and resource ID for a discussion
        identifier, typically a request path.
        """
        match = re.match(
            r'''(?:/?$|forum/(\d+)'''
            r'''(?:/?$|/topic/(\d+)'''
            r'''(?:/?$|/message/(\d+)(?:/?$))))''',
            resource.id)
        type_ = id_ = None
        if match:
            forum, topic, message = match.groups()
            if message:
                type_ = 'message'
                id_ = message
            elif topic:
                type_ = 'topic'
                id_ = topic
            elif forum:
                type_ = 'forum'
                id_ = forum
        else:
            type_, id_ = resource.id.split('/')
        return type_, id_

    def _prepare_context(self, context):
        req = context.req
        # Prepare template data.
        context.data = {}

        # Get list of users with DISCUSSION_VIEW permission.
        context.users = self.get_users(context)

        # Check if TracTags plugin is enabled.
        context.has_tags = is_tags_enabled(self.env)

        # Populate active message.
        context.group = None
        context.forum = None
        context.topic = None
        context.message = None

        realm = Resource(self.realm)
        if 'message' in req.args:
            message_id = req.args.getint('message', 0)
            context.message = self.get_message(message_id)
            if not context.message:
                raise TracError('Message with ID %s does not exist.'
                                % message_id)
            # Create request resource.
            context.topic = self.get_topic(context, context.message['topic'])
            context.forum = self.get_forum(context, context.topic['forum'])
            context.group = self.get_group(context.forum['forum_group'])
            context.resource = realm(id='forum/%s/topic/%s/message/%s'
                                        % (context.forum['id'],
                                           context.topic['id'],
                                           context.message['id']),
                                     parent=realm(id='forum/%s/topic/%s'
                                                     % (context.forum['id'],
                                                        context.topic['id'])))

        # Populate active topic.
        elif 'topic' in req.args:
            topic_id = req.args.getint('topic', 0)
            context.topic = self.get_topic(context, topic_id)
            if not context.topic:
                raise TracError("Topic with ID %s does not exist." % topic_id)

            # Create request resource.
            context.forum = self.get_forum(context, context.topic['forum'])
            context.group = self.get_group(context.forum['forum_group'])
            context.resource = realm(id='forum/%s/topic/%s'
                                        % (context.forum['id'],
                                           context.topic['id']))

        # Populate active forum.
        elif 'forum' in req.args:
            forum_id = req.args.getint('forum', 0)
            context.forum = self.get_forum(context, forum_id)
            if not context.forum:
                raise TracError('Forum with ID %s does not exist.' % forum_id)

            context.group = self.get_group(context.forum['forum_group'])
            context.resource = realm(id='forum/%s' % forum_id)

        # Populate active group.
        elif 'group' in req.args:
            group_id = req.args.getint('group', 0)
            context.group = self.get_group(group_id)
            if not context.group:
                raise TracError('Group with ID %s does not exist.' % group_id)

            # Create request resource.
            context.resource = realm(id='group/%s' % context.group['id'])

        # Determine moderator rights.
        context.moderator = context.forum and \
                            req.authname in context.forum['moderators'] and \
                            'DISCUSSION_MODERATE' in req.perm

        # Determine if user has e-mail set.
        context.authemail = req.session.get('email')

        # Prepare other general context attributes.
        context.redirect_url = None
        context.format = req.args.get('format')

    def _get_actions(self, context):
        req = context.req
        action = req.args.get('discussion_action')
        preview = 'preview' in req.args
        submit = 'submit' in req.args
        self.log.debug("realm: %s, action: %s, format: %s preview: %s, "
                       "submit: %s", context.realm, action, context.format,
                       preview, submit)

        # Determine mode.
        if context.message:
            if context.realm == 'discussion-admin':
                pass
            elif context.realm == 'discussion-ajax':
                if action == 'edit-attribute':
                    return ['message-edit-attribute']
                elif action == 'subscribe':
                    return ['topic-subscribe']
                elif action == 'unsubscribe':
                    return ['topic-unsubscribe']
            elif context.realm == 'discussion-wiki':
                if action == 'add':
                    return ['message-add', 'wiki-message-list']
                elif action == 'quote':
                    return ['message-quote', 'wiki-message-list']
                elif action == 'post-add':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['message-post-add']
                elif action == 'edit':
                    return ['message-edit', 'wiki-message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['message-post-edit']
                elif action == 'delete':
                    return ['message-delete']
                elif action == 'set-display':
                    return ['topic-set-display', 'wiki-message-list']
                else:
                    return ['wiki-message-list']
            else:
                if context.format == 'rss':
                    return ['topic-rss']
                if action == 'add':
                    return ['message-add', 'message-list']
                elif action == 'quote':
                    return ['message-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add']
                elif action == 'edit':
                    return ['message-edit', 'message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-edit']
                elif action == 'delete':
                    return ['message-delete']
                elif action == 'set-display':
                    return ['topic-set-display', 'message-list']
                else:
                    return ['message-list']
        if context.topic:
            if context.realm == 'discussion-admin':
                pass
            elif context.realm == 'discussion-ajax':
                if action == 'edit-attribute':
                    return ['topic-edit-attribute']
                elif action == 'subscribe':
                    return ['topic-subscribe']
                elif action == 'unsubscribe':
                    return ['topic-unsubscribe']
            elif context.realm == 'discussion-wiki':
                if action == 'add':
                    return ['message-add', 'wiki-message-list']
                elif action == 'quote':
                    return ['topic-quote', 'wiki-message-list']
                elif action == 'post-add':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['message-post-add']
                elif action == 'edit':
                    return ['topic-edit', 'wiki-message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['topic-post-edit']
                elif action == 'set-display':
                    return ['topic-set-display', 'wiki-message-list']
                elif action == 'subscriptions-post-add':
                    return ['topic-subscriptions-post-add']
                elif action == 'subscriptions-post-edit':
                    return ['topic-subscriptions-post-edit']
                else:
                    return ['wiki-message-list']
            else:
                if context.format == 'rss':
                    return ['topic-rss']
                if action == 'add':
                    return ['message-add', 'message-list']
                elif action == 'quote':
                    return ['topic-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add']
                elif action == 'edit':
                    return ['topic-edit', 'message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['message-list']
                    else:
                        return ['topic-post-edit']
                elif action == 'delete':
                    return ['topic-delete']
                elif action == 'move':
                    return ['topic-move']
                elif action == 'post-move':
                    return ['topic-post-move']
                elif action == 'set-display':
                    return ['topic-set-display', 'message-list']
                elif action == 'subscriptions-post-add':
                    return ['topic-subscriptions-post-add']
                elif action == 'subscriptions-post-edit':
                    return ['topic-subscriptions-post-edit']
                else:
                    return ['message-list']
        elif context.forum:
            if context.realm == 'discussion-admin':
                if action == 'post-edit':
                    return ['forum-post-edit']
                else:
                    return ['admin-forum-list']
            elif context.realm == 'discussion-ajax':
                if action == 'edit-attribute':
                    return ['forum-edit-attribute']
                elif action == 'subscribe':
                    return ['forum-subscribe']
                elif action == 'unsubscribe':
                    return ['forum-unsubscribe']
            elif context.realm == 'discussion-wiki':
                return ['wiki-message-list']
            else:
                if context.format == 'rss':
                    return ['forum-rss']
                if action == 'add':
                    return ['topic-add']
                elif action == 'post-add':
                    if preview:
                        return ['topic-add']
                    else:
                        return ['topic-post-add']
                elif action == 'delete':
                    return ['forum-delete']
                elif action == 'set-display':
                    return ['forum-set-display', 'topic-list']
                elif action == 'subscriptions-post-edit':
                    return ['forum-subscriptions-post-edit']
                elif action == 'topic-last':
                    return ['topic-last']
                else:
                    return ['topic-list']
        elif context.group:
            if context.realm == 'discussion-admin':
                if action == 'post-add':
                    return ['forum-post-add']
                elif action == 'post-edit':
                    return ['group-post-edit']
                elif action == 'delete':
                    return ['forums-delete']
                else:
                    if context.group['id']:
                        return ['admin-group-list']
                    else:
                        return ['admin-forum-list']
            elif context.realm == 'discussion-ajax':
                if action == 'edit-attribute':
                    return ['group-edit-attribute']
            elif context.realm == 'discussion-wiki':
                return ['wiki-message-list']
            else:
                if action == 'post-add':
                    return ['forum-post-add']
                else:
                    return ['forum-list']
        else:
            if context.realm == 'discussion-admin':
                if action == 'post-add':
                    return ['group-post-add']
                elif action == 'delete':
                    return ['groups-delete']
                else:
                    return ['admin-group-list']
            elif context.realm == 'discussion-wiki':
                return ['wiki-message-list']
            else:
                if action == 'add':
                    return ['forum-add']
                elif action == 'post-add':
                    return ['forum-post-add']
                else:
                    return ['forum-list']

    def _get_template(self, context, actions):
        if context.format == 'rss':
            return actions[-1].replace('-rss', '') + '.rss'
        else:
            return actions[-1] + '.html'

    def _do_actions(self, context, actions):
        req = context.req
        for action in actions:
            if action == 'group-list':
                req.perm.require('DISCUSSION_VIEW')

                # Display groups.
                context.data['groups'] = self.get_groups()

            elif action == 'admin-group-list':
                req.perm.require('DISCUSSION_ADMIN')

                # Get form values.
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc') == '1'

                # Display groups.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['groups'] = self.get_groups(order, desc)

            elif action == 'group-add':
                req.perm.require('DISCUSSION_ADMIN')

            elif action == 'group-post-add':
                req.perm.require('DISCUSSION_ADMIN')

                # Get form values.
                group = {'name': req.args.get('name'),
                         'description': req.args.get('description')}

                # Add new group.
                self.add_group(group)

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'group-post-edit':
                req.perm.require('DISCUSSION_ADMIN')

                # Get form values.
                group = {'name': req.args.get('name'),
                         'description': req.args.get('description')}

                # Edit group.
                self.edit_group(context.group['id'], group)

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'group-delete':
                req.perm.require('DISCUSSION_ADMIN')

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'groups-delete':
                req.perm.require('DISCUSSION_ADMIN')

                # Get selected groups.
                selection = req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete selected groups.
                if selection:
                    for group_id in selection:
                        self.delete_group(int(group_id))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'forum-list':
                req.perm.require('DISCUSSION_VIEW')

                # Get form values.
                order = req.args.get('order') or self.forum_sort
                if 'desc' in req.args:
                    desc = req.args.get('desc') == '1'
                else:
                    desc = self.forum_sort_direction == 'desc'

                # Display forums.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['groups'] = self.get_groups()
                context.data['forums'] = self.get_forums(context, order, desc)

            elif action == 'admin-forum-list':
                req.perm.require('DISCUSSION_ADMIN')

                # Get ordering arguments values.
                order = req.args.get('order') or self.forum_sort
                if 'desc' in req.args:
                    desc = req.args.get('desc') == '1'
                else:
                    desc = self.forum_sort_direction == 'desc'

                # Display forums.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['groups'] = self.get_groups()
                context.data['forums'] = self.get_forums(context, order, desc)

            elif action == 'forum-rss':
                req.perm.require('DISCUSSION_VIEW', context.resource)

                # Get topics and messages.
                messages = self.get_flat_messages_by_forum(
                    context.forum['id'], desc=True,
                    limit=self.messages_per_page)
                topics = self.get_topics(context.forum['id'], context,
                                         desc=True,
                                         limit=self.topics_per_page)

                # Create map of topic subjects.
                topic_subjects = {}
                for message in messages:
                    if not message['topic'] in topic_subjects:
                        topic_subjects[message['topic']] = \
                            self.get_topic_subject(message['topic'])

                # Prepare list of topics and messages of the forum.
                context.data['topics'] = topics
                context.data['messages'] = messages
                context.data['topic_subjects'] = topic_subjects

            elif action == 'forum-add':
                req.perm.require('DISCUSSION_ADMIN')

                # Display Add Forum form.
                context.data['groups'] = self.get_groups()

            elif action == 'forum-post-add':
                req.perm.require('DISCUSSION_ADMIN')

                # Get form values
                forum = {
                    'name': req.args.get('name'),
                    'author': req.authname,
                    'subject': req.args.get('subject'),
                    'description': req.args.get('description'),
                    'moderators': req.args.get('moderators'),
                    'subscribers': req.args.get('subscribers'),
                    'forum_group': req.args.getint('group', 0),
                    'tags': req.args.get('tags')
                }

                # Fix moderators attribute to be a list.
                if not forum['moderators']:
                    forum['moderators'] = []
                if not isinstance(forum['moderators'], list):
                    forum['moderators'] = to_list(forum['moderators'] or '')

                # Fix subscribers attribute to be a list.
                if not forum['subscribers']:
                    forum['subscribers'] = []
                if not isinstance(forum['subscribers'], list):
                    forum['subscribers'] = to_list(forum['subscribers'] or '')
                forum['subscribers'] += \
                    to_list(req.args.get('unregistered_subscribers'))

                # Fix tags attribute to be a list
                if not forum['tags']:
                    forum['tags'] = []
                if not isinstance(forum['tags'], list):
                    forum['tags'] = to_list(forum['tags'] or '')

                # Perform new forum add.
                forum_id = self.add_forum(forum)
                context.forum = self.get_forum(context, forum_id)

                # Copy tags field which is not stored in the database table.
                context.forum['tags'] = forum['tags']

                # Notify change listeners.
                self.log.debug("forum_change_listeners: %s",
                               self.forum_change_listeners)
                for listener in self.forum_change_listeners:
                    try:
                        listener.forum_created(context, context.forum)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'forum-post-edit':
                req.perm.require('DISCUSSION_ADMIN')

                # Get form values.
                forum = {
                    'name': req.args.get('name'),
                    'subject': req.args.get('subject'),
                    'description': req.args.get('description'),
                    'moderators': req.args.get('moderators'),
                    'subscribers': req.args.get('subscribers'),
                    'forum_group': req.args.getint('group', 0),
                }

                # Fix moderators attribute to be a list.
                if not forum['moderators']:
                    forum['moderators'] = []
                if not isinstance(forum['moderators'], list):
                    forum['moderators'] = to_list(forum['moderators'] or '')

                # Fix subscribers attribute to be a list.
                if not forum['subscribers']:
                    forum['subscribers'] = []
                if not isinstance(forum['subscribers'], list):
                    forum['subscribers'] = to_list(forum['subscribers'] or '')
                forum['subscribers'] += \
                    to_list(req.args.get('unregistered_subscribers'))

                # Perform forum edit.
                self.edit_forum(context.forum['id'], forum)

                for listener in self.forum_change_listeners:
                    try:
                        listener.forum_changed(context, forum, context.forum)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'forum-delete':
                req.perm.require('DISCUSSION_ADMIN')

                # Delete forum.
                self.delete_forum(context.forum['id'])

                for listener in self.forum_change_listeners:
                    try:
                        listener.forum_deleted(context.forum)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'forums-delete':
                req.perm.require('DISCUSSION_ADMIN')

                # Get selected forums.
                selection = req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete selected forums.
                if selection:
                    for forum_id in selection:
                        # Retrieve current forum attributes.
                        forum = self.get_forum(context, int(forum_id))
                        self.delete_forum(forum['id'])

                        for listener in self.forum_change_listeners:
                            try:
                                listener.forum_deleted(forum)
                            except Exception, e:
                                self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'forum-set-display':
                req.perm.require('DISCUSSION_VIEW')

                # Get form values.
                display = req.args.get('display')

                # Set message list display mode to session.
                req.session['topic-list-display'] = display

            elif action == 'forum-subscriptions-post-edit':
                req.perm.require('DISCUSSION_MODERATE', context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Prepare edited attributes of the forum.
                forum = {'subscribers': req.args.get('subscribers')}
                if not forum['subscribers']:
                    forum['subscribers'] = []
                if not isinstance(forum['subscribers'], list):
                    forum['subscribers'] = to_list(forum['subscribers'] or '')
                forum['subscribers'] += \
                    to_list(req.args.get('unregistered_subscribers'))

                # Edit topic.
                self.edit_forum(context.forum['id'], forum)

                for listener in self.forum_change_listeners:
                    try:
                        listener.forum_changed(context, forum, context.forum)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '#subscriptions')

            elif action == 'forum-subscribe':
                req.perm.require('DISCUSSION_VIEW', context.resource)
                if context.authemail and \
                        req.authname not in context.forum['subscribers']:
                    # Prepare edited attributes of the forum.
                    forum = {'subscribers': deepcopy(context.forum[
                                                         'subscribers'])}
                    forum['subscribers'].append(req.authname)

                    # Edit topic.
                    self.edit_forum(context.forum['id'], forum)

                    for listener in self.forum_change_listeners:
                        try:
                            listener.forum_changed(context, forum,
                                                   context.forum)
                        except Exception, e:
                            self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '#subscriptions')

            elif action == 'forum-unsubscribe':
                req.perm.require('DISCUSSION_VIEW', context.resource)
                if context.authemail and \
                        req.authname in context.forum['subscribers']:

                    # Prepare edited attributes of the topic.
                    forum = {
                        'subscribers': deepcopy(context.forum['subscribers'])
                    }
                    forum['subscribers'].remove(req.authname)

                    # Edit topic.
                    self.edit_forum(context.forum['id'], forum)

                    for listener in self.forum_change_listeners:
                        try:
                            listener.forum_changed(context, forum,
                                                   context.forum)
                        except Exception, e:
                            self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '#subscriptions')

            elif action == 'topic-last':
                columns = ('id',)
                forum_id = context.forum['id']
                href = Href('discussion')
                topic = self.get_items('topic', columns, 'forum=%s',
                                       (forum_id,), 'time', True, limit=1)
                if topic:
                    context.redirect_url = (href('topic', topic[0]['id']), '')
                else:
                    # On empty forum redirect to forum's topic list.
                    context.redirect_url = (href('forum', forum_id), '')

            elif action == 'topic-list':
                req.perm.require('DISCUSSION_VIEW', context.resource)

                # Update this forum visit time.
                context.visited_forums[context.forum['id']] = \
                    to_timestamp(datetime_now(utc))

                # Get form values.
                order = req.args.get('order') or self.topic_sort
                if 'desc' in req.args:
                    desc = req.args.get('desc') == '1'
                else:
                    desc = self.topic_sort_direction == 'desc'
                page = req.args.getint('discussion_page', 1) - 1

                # Get topic list display type from session.
                display = req.session.get('topic-list-display') or \
                          self.default_topic_display

                # Get topics of the current page.
                topics_count = self.get_topics_count(context.forum['id'])
                topics = self.get_topics(context.forum['id'], context, order,
                                         desc, self.topics_per_page,
                                         page * self.topics_per_page, False)
                paginator = self._get_paginator(context, page,
                                                self.topics_per_page,
                                                topics_count)

                # Display the topics.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['display'] = display
                context.data['topics'] = topics
                context.data['paginator'] = paginator

            elif action == 'topic-rss':
                req.perm.require('DISCUSSION_VIEW', context.resource)

                # Display list of messages for topic.
                context.data['messages'] = \
                    self.get_flat_messages(context.topic['id'], desc=True,
                                           limit=self.messages_per_page)

            elif action == 'topic-add':
                req.perm.require('DISCUSSION_APPEND', context.resource)

            elif action == 'topic-quote':
                req.perm.require('DISCUSSION_APPEND', context.resource)

                # Prepare old content.
                lines = context.topic['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                req.args['body'] = '\n'.join(lines)

            elif action == 'topic-post-add':
                req.perm.require('DISCUSSION_APPEND', context.resource)

                # Get form values.
                topic = {
                    'forum': context.forum['id'],
                    'subject': req.args.get('subject'),
                    'author': req.args.get('author'),
                    'subscribers': req.args.get('subscribers'),
                    'body': req.args.get('body')
                }

                # Fix subscribers attribute to be a list.
                if not topic['subscribers']:
                    topic['subscribers'] = []
                if not isinstance(topic['subscribers'], list):
                    topic['subscribers'] = to_list(topic['subscribers'] or '')
                topic['subscribers'] += \
                    to_list(req.args.get('unregistered_subscribers'))

                # Add user e-mail if subscription checked.
                if req.args.get('subscribe') and context.authemail and \
                        req.authname not in topic['subscribers']:
                    topic['subscribers'].append(req.authname)

                # Filter topic.
                for discussion_filter in self.discussion_filters:
                    self.log.debug("filtering topic: %s", topic)
                    accept, topic_or_error = discussion_filter.filter_topic(
                        context, topic)
                    if accept:
                        topic = topic_or_error
                    else:
                        raise TracError(topic_or_error)

                # Add new topic.
                topic_id = self.add_topic(topic)
                context.topic = self.get_topic(context, topic_id)

                self.log.debug("topic_change_listeners: %s",
                               self.topic_change_listeners)
                for listener in self.topic_change_listeners:
                    try:
                        listener.topic_created(context, context.topic)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                if context.realm != 'discussion-wiki':
                    href = Href('discussion')
                    context.redirect_url = (
                        href('topic', context.topic['id']),
                        '#topic')
                else:
                    context.redirect_url = (req.path_info, '#topic')

            elif action == 'topic-edit':
                req.perm.require('DISCUSSION_APPEND', context.resource)
                if not context.moderator and \
                        context.topic['author'] != req.authname:
                    raise PermissionError('Topic edit')

                # Prepare form values.
                req.args['subject'] = context.topic['subject']
                req.args['body'] = context.topic['body']

            elif action == 'topic-post-edit':
                req.perm.require('DISCUSSION_APPEND', context.resource)

                # Check if user can edit topic.
                if not context.moderator and \
                        context.topic['author'] != req.authname:
                    raise PermissionError('Topic editing')

                # Check if user can edit locked topic.
                if not context.moderator and \
                        'locked' in context.topic['status']:
                    raise PermissionError("Locked topic editing")

                # Get form values.
                topic = {'subject': req.args.get('subject'),
                         'body': req.args.get('body')}

                # Edit topic.
                self.edit_topic(context.topic['id'], topic)

                for listener in self.topic_change_listeners:
                    try:
                        listener.topic_changed(context, topic, context.topic)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '#topic')

            elif action == 'topic-edit-attribute':
                # Check general topic editing permission.
                req.perm.require('DISCUSSION_APPEND', context.resource)
                if not context.moderator and \
                        context.topic['author'] != req.authname:
                    raise PermissionError("Topic editing")

                # Get form values.
                if 'name' not in req.args and 'value' in req.args:
                    raise TracError("Missing request arguments.")
                name = req.args.get('name')
                value = req.args.get('value')

                # Important flag is implemented as integer priority.
                if name == 'important':
                    name = 'priority'
                    value = as_bool(value)

                # Attributes that can be changed only by administrator.
                topic = {}
                if name in ('id', 'time'):
                    req.perm.require('DISCUSSION_ADMIN')
                    topic[name] = value
                # Attributes that can be changed by moderator.
                elif name in ('forum', 'author', 'subscribers', 'priority',
                              'status.locked', 'status'):
                    req.perm.require('DISCUSSION_MODERATE', context.resource)
                    if not context.moderator:
                        raise PermissionError("Topic editing")

                    # Decode status flag to status list.
                    if name == 'status.locked':
                        topic['status'] = context.topic['status'].copy()
                        if as_bool(value):
                            topic['status'] |= set(['locked'])
                        else:
                            topic['status'] -= set(['locked'])
                    else:
                        topic[name] = value

                # Attributes that can be changed by owner of the topic or the
                # moderator.
                elif name in ('subject', 'body', 'status.solved'):
                    req.perm.require('DISCUSSION_APPEND', context.resource)

                    # Check if user can edit topic.
                    if not context.moderator and \
                            context.topic['author'] != req.authname:
                        raise PermissionError("Topic editing")

                    # Decode status flag to status list.
                    if name == 'status.solved':
                        topic['status'] = context.topic['status'].copy()
                        if as_bool(value):
                            topic['status'] |= set(['solved'])
                            topic['status'] -= set(['unsolved'])
                        else:
                            topic['status'] |= set(['unsolved'])
                            topic['status'] -= set(['solved'])
                    else:
                        topic[name] = value
                else:
                    raise PermissionError("Topic editing")

                # Update the attribute value.
                self.edit_topic(context.topic['id'], topic)

            elif action == 'topic-move':
                req.perm.require('DISCUSSION_MODERATE', context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Display Move Topic form.
                context.data['forums'] = self.get_forums(context)

            elif action == 'topic-post-move':
                req.perm.require('DISCUSSION_MODERATE', context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Get form values.
                forum_id = req.args.getint('new_forum', 0)

                # Move topic.
                self.set_forum(context.topic['id'], forum_id)

                # Redirect request to prevent re-submit.
                context.redirect_url = (req.path_info, '')

            elif action == 'topic-delete':
                req.perm.require('DISCUSSION_MODERATE', context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Delete topic.
                self.delete_topic(context.topic['id'])

                for listener in self.topic_change_listeners:
                    try:
                        listener.topic_deleted(context, context.topic)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                if context.realm != 'discussion-wiki':
                    href = Href('discussion')
                    context.redirect_url = (href('forum',
                                                 context.topic['forum']), '')
                else:
                    context.redirect_url = (req.path_info, '')

            elif action == 'topic-set-display':
                req.perm.require('DISCUSSION_VIEW')

                # Get form values.
                display = req.args.get('display')

                # Set message list display mode to session.
                req.session['message-list-display'] = display

            elif action == 'topic-subscriptions-post-edit':
                req.perm.require('DISCUSSION_MODERATE', context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Prepare edited attributes of the topic.
                topic = {'subscribers': req.args.get('subscribers')}
                if not topic['subscribers']:
                    topic['subscribers'] = []
                if not isinstance(topic['subscribers'], list):
                    topic['subscribers'] = to_list(topic['subscribers'] or '')
                topic['subscribers'] += \
                    to_list(req.args.get('unregistered_subscribers'))

                # Edit topic.
                self.edit_topic(context.topic['id'], topic)

                for listener in self.topic_change_listeners:
                    try:
                        listener.topic_changed(context, topic, context.topic)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = (
                    req.path_info, '#subscriptions')

            elif action == 'topic-subscriptions-post-add':
                req.perm.require('DISCUSSION_VIEW', context.resource)

                # Prepare edited attributes of the forum..
                topic = {'subscribers': context.topic['subscribers']}
                for subscriber in to_list(req.args.get('subscribers')):
                    if subscriber not in topic['subscribers']:
                        topic['subscribers'].append(subscriber)

                # Edit topic.
                self.edit_topic(context.topic['id'], topic)

                for listener in self.topic_change_listeners:
                    try:
                        listener.topic_changed(context, topic, context.topic)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = req.path_info, '#subscriptions'

            elif action == 'topic-subscribe':
                req.perm.require('DISCUSSION_VIEW', context.resource)

                if context.authemail and \
                        req.authname not in context.topic['subscribers']:

                    # Prepare edited attributes of the topic.
                    topic = {
                        'subscribers': deepcopy(context.topic['subscribers'])
                    }
                    topic['subscribers'].append(req.authname)

                    # Edit topic.
                    self.edit_topic(context.topic['id'], topic)

                    for listener in self.topic_change_listeners:
                        try:
                            listener.topic_changed(context, topic,
                                                   context.topic)
                        except Exception, e:
                            self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = req.path_info, '#subscriptions'

            elif action == 'topic-unsubscribe':
                req.perm.require('DISCUSSION_VIEW', context.resource)

                if context.authemail and \
                        req.authname in context.topic['subscribers']:

                    # Prepare edited attributes of the topic.
                    topic = {'subscribers': deepcopy(context.topic[
                                                         'subscribers'])}
                    topic['subscribers'].remove(req.authname)

                    # Edit topic.
                    self.edit_topic(context.topic['id'], topic)

                    for listener in self.topic_change_listeners:
                        try:
                            listener.topic_changed(context, topic,
                                                   context.topic)
                        except Exception, e:
                            self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = req.path_info, '#subscriptions'

            elif action == 'message-list':
                req.perm.require('DISCUSSION_VIEW', context.resource)
                self._prepare_message_list(context, context.topic)

            elif action == 'wiki-message-list':
                if context.topic:
                    self._prepare_message_list(context, context.topic)

            elif action == 'message-add':
                req.perm.require('DISCUSSION_APPEND', context.resource)

            elif action == 'message-quote':
                req.perm.require('DISCUSSION_APPEND', context.resource)

                # Prepare old content.
                lines = context.message['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                req.args['body'] = '\n'.join(lines)

            elif action == 'message-post-add':
                req.perm.require('DISCUSSION_APPEND', context.resource)

                # Check if user can post to locked topic.
                if not context.moderator and \
                        'locked' in context.topic['status']:
                    raise PermissionError("Locked topic posting")

                # Get form values.
                message = {
                    'forum': context.forum['id'],
                    'topic': context.topic['id'],
                    'replyto': context.message['id']
                               if context.message else -1,
                    'author': req.args.get('author'),
                    'body': req.args.get('body')
                }

                # Filter message.
                for discussion_filter in self.discussion_filters:
                    self.log.debug("filtering message: %s", message)
                    accept, message_or_error = \
                        discussion_filter.filter_message(context, message)
                    if accept:
                        message = message_or_error
                    else:
                        raise TracError(message_or_error)

                # Add message.
                message_id = self.add_message(message)
                context.message = self.get_message(message_id)

                self.log.debug('message_change_listeners: %s',
                               self.message_change_listeners)
                for listener in self.message_change_listeners:
                    try:
                        listener.message_created(context, context.message)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = \
                    req.path_info, '#message%s' % (context.message['id'],)

            elif action == 'message-edit':
                req.perm.require('DISCUSSION_APPEND', context.resource)
                if not context.moderator and \
                        context.message['author'] != req.authname:
                    raise PermissionError('Message edit')

                # Prepare form values.
                req.args['body'] = context.message['body']

            elif action == 'message-post-edit':
                req.perm.require('DISCUSSION_APPEND', context.resource)

                # Check if user can edit message.
                if not context.moderator and \
                        context.message['author'] != req.authname:
                    raise PermissionError('Message edit')

                # Check if user can edit locked topic.
                if not context.moderator and \
                        'locked' in context.topic['status']:
                    raise PermissionError("Locked topic editing")

                # Get form values.
                message = {'body': req.args.get('body')}

                # Edit message.
                self.edit_message(context.message['id'], message)

                for listener in self.message_change_listeners:
                    try:
                        listener.message_changed(context, message,
                                                 context.message)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = \
                    req.path_info, '#message%s' % context.message['id']

            elif action == 'message-delete':
                req.perm.require('DISCUSSION_MODERATE', context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Delete message.
                self.delete_message(context.message['id'])

                for listener in self.message_change_listeners:
                    try:
                        listener.message_deleted(context, context.message)
                    except Exception, e:
                        self.log.warning(exception_to_unicode(e))

                # Redirect request to prevent re-submit.
                context.redirect_url = \
                    req.path_info, '#message%s' % context.message['replyto']

        # Redirection is not necessary.
        return None

    def _prepare_message_list(self, context, topic):
        req = context.req
        # Get time when topic was visited from session.
        visit_time = as_int(context.visited_topics.get(topic['id']), 0)

        # Get form values
        page = req.args.getint('discussion_page', 1) - 1

        # Update this topic visit time.
        context.visited_topics[topic['id']] = to_timestamp(datetime_now(utc))

        # Get topic messages for the current page.
        display = req.session.get('message-list-display') or \
                  self.default_message_display
        if display == 'flat-asc':
            messages_count = self.get_messages_count(topic['id'])
            messages = self.get_flat_messages(topic['id'], desc=False,
                limit=self.messages_per_page,
                offset=page * self.messages_per_page)
        elif display in ('flat-desc', 'flat'):
            messages_count = self.get_messages_count(topic['id'])
            messages = self.get_flat_messages(topic['id'], desc=True,
                limit=self.messages_per_page,
                offset=page * self.messages_per_page)
        elif display in ('tree', ''):
            messages_count = 0
            messages = self.get_messages(topic['id'])
        else:
            raise TracError('Unsupported display mode: %s' % display)

        # Create paginator.
        paginator = self._get_paginator(context, page, self.messages_per_page,
                                        messages_count, anchor='#topic')

        # Prepare display of messages.
        context.data['visit_time'] = visit_time
        context.data['display'] = display
        context.data['messages'] = messages
        context.data['paginator'] = paginator

        # Display list of attachments.
        real_resource = context.resource
        # DEVEL: Work around for AttachmentModule.process_request() that
        #        calculates the parent id from the path.
        #        Therefore we need to fix the attach_href property.
        if 'topic' != context.resource.id.split('/')[-2]:
            context.resource = Resource('discussion', '/'.join(
                context.resource.id.split('/')[-4:-2]))
        context.resource = Resource('discussion', '/'.join(
            context.resource.id.split('/')[-2:]))
        context.data['attachments'] = AttachmentModule(self.env) \
            .attachment_data(context)
        context.resource = real_resource

    def _get_paginator(self, context, page, items_limit, items_count,
                       anchor=''):
        req = context.req
        # Create paginator object.
        paginator = Paginator([], page, items_limit, items_count)

        # Initialize pages.
        page_data = []
        shown_pages = paginator.get_shown_pages(21)
        for shown_page in shown_pages:
            page_data.append([req.href(req.path_info,
                                       discussion_page=shown_page,
                                       order=req.args.get('order'),
                                       desc=req.args.get('desc')) + anchor,
                              None, to_unicode(shown_page),
                              'page %s' % (shown_page,)])
        fields = ['href', 'class', 'string', 'title']
        paginator.shown_pages = [dict(zip(fields, p)) for p in page_data]

        paginator.current_page = {'href': None, 'class': 'current', 'string':
            str(page + 1), 'title': None}

        # Prepare links to next or previous page.
        if paginator.has_next_page:
            add_link(req, 'next', req.href(req.path_info,
                                           discussion_page=paginator.page + 2,
                     order=req.args.get('order'),
                     desc=req.args.get('desc')) + anchor, 'Next Page')
        if paginator.has_previous_page:
            add_link(req, 'prev', req.href(req.path_info,
                                           discussion_page=paginator.page,
                     order=req.args.get('order'),
                     desc=req.args.get('desc')) + anchor, 'Previous Page')

        return paginator

    # Item getter methods.

    def get_group(self, id):
        # Get forum group.
        return self.get_item('forum_group', ('id', 'name', 'description'),
                             'id=%s', (id,)) or dict(id=0, name='None',
                                                     description='No Group')

    def get_forum(self, context, forum_id):
        """Get forum by ID."""
        context.resource = Resource(self.realm, 'forum/%s' % forum_id)
        forum = self.get_item('forum', self.forum_cols, 'id=%s',
                              (context.resource.id.split('/')[-1],))
        # Unpack list of moderators and subscribers and get forum tags.
        if forum:
            forum['moderators'] = to_list(forum['moderators'] or '')
            forum['subscribers'] = to_list(forum['subscribers'] or '')
            forum['unregistered_subscribers'] = set(
                forum['subscribers']).difference(self.get_users(context))
            if context.has_tags:
                tag_system = TagSystem(self.env)
                forum['tags'] = tag_system.get_tags(context.req,
                                                    context.resource)
        return forum

    def get_forums(self, context, order_by='subject', desc=False):

        def _new_replies_count(context, forum_id):
            # Get IDs of topics in this forum.
            where = "forum=%s"
            topics = [topic['id'] for topic in
                      self.get_items('topic', ('id',), where, (forum_id,))]
            # Count unseen messages.
            count = 0
            for topic_id in topics:
                values = (topic_id,
                          as_int(context.visited_topics.get(topic_id), 0))
                where = "topic=%s AND time>%s"
                count += self.get_items_count('message', where, values)
            return count

        def _new_topic_count(context, forum_id):
            values = (forum_id,
                      as_int(context.visited_forums.get(forum_id), 0))
            where = "forum=%s AND time>%s"
            return self.get_items_count('topic', where, values)

        forums = self._get_forums(order_by, desc)
        # Add some more forum attributes and convert others.
        for forum in forums:
            # Compute count of new replies and topics.
            forum['new_topics'] = _new_topic_count(context, forum['id'])
            forum['new_replies'] = _new_replies_count(context, forum['id'])

            # Convert floating-point result of SUM() above into integer.
            forum['replies'] = as_int(forum.get('replies'), 0)
            # Unpack list of moderators and subscribers and get forum tags.
            forum['moderators'] = to_list(forum['moderators'] or '')
            forum['subscribers'] = to_list(forum['subscribers'] or '')
            forum['unregistered_subscribers'] = set(
                forum['subscribers']).difference(self.get_users(context))
            if context.has_tags:
                tag_system = TagSystem(self.env)
                forum['tags'] = tag_system.get_tags(context.req, Resource(
                    'discussion', 'forum/%s' % forum['id']))
        return forums

    def get_changed_forums(self, start, stop, order_by='time', desc=False):
        """Return forum content for timeline."""

        columns = ('id', 'name', 'author', 'time', 'subject', 'description')
        where = "time BETWEEN %s AND %s"
        values = (to_timestamp(start), to_timestamp(stop))
        return self.get_items('forum', columns, where, values)

    def get_topic(self, context, id):
        """Get topic by ID."""
        topic = self.get_item('topic', self.topic_cols, 'id=%s', (id,))
        return prepare_topic(self.get_users(context), topic)

    def get_topic_by_subject(self, context, subject):
        """Get topic by subject."""
        topic = self.get_item('topic', self.topic_cols, 'subject=%s',
                              (subject,))
        return prepare_topic(self.get_users(context), topic)

    def get_topics(self, forum_id, context, order_by='time', desc=False,
                   limit=0, offset=0, with_body=True):

        def _new_replies_count(context, topic_id):
            values = (topic_id,
                      as_int(context.visited_topics.get(topic_id), 0))
            where = "topic=%s AND time>%s"
            return self.get_items_count('message', where, values)

        topics = self._get_topics(forum_id, order_by, desc, limit, offset,
                                  with_body)
        # Add some more topic attributes and convert others.
        for topic in topics:
            topic['new_replies'] = _new_replies_count(context, topic['id'])
            # Unpack list of topic subscribers and get topic status.
            topic = prepare_topic(self.get_users(context), topic)
            if context.has_tags:
                tag_system = TagSystem(self.env)
                topic['tags'] = tag_system.get_tags(context.req, Resource(
                    'discussion', 'topic/%s' % topic['id']))
        return topics

    def get_message(self, id):
        """Get message by ID."""
        return self.get_item('message', self.message_cols, 'id=%s', (id,))

    def get_flat_messages(self, id, order_by='time', desc=False, limit=0,
                          offset=0):
        # Return messages of specified topic.
        return self.get_items('message', self.msg_cols, 'topic=%s', (id,),
                              order_by, desc, limit, offset)

    def get_flat_messages_by_forum(self, id, order_by='time', desc=False,
                                   limit=0, offset=0):
        # Return messages of specified topic.
        return self.get_items('message', ('id', 'replyto', 'topic',
                                          'time', 'author', 'body'),
                              'forum=%s', (id,), order_by, desc, limit,
                              offset)

    def get_replies(self, id, order_by='time', desc=False):
        # Return replies of specified message.
        return self.get_items('message', self.msg_cols, 'replyto=%s', (id,),
                              order_by, desc)

    # Attribute getter methods.

    def get_forum_subject(self, id):
        """Get subject of the forum."""
        forum = self.get_item('forum', ('subject',), 'id=%s', (id,))
        if forum:
            return forum['subject']

    def get_topic_subject(self, id):
        """Get subject of the topic."""
        topic = self.get_item('topic', ('subject',), 'id=%s', (id,))
        if topic:
            return topic['subject']

    # Counter methods.

    def get_topics_count(self, forum_id):
        return self.get_items_count('topic', 'forum=%s', (forum_id,))

    def get_messages_count(self, topic_id):
        return self.get_items_count('message', 'topic=%s', (topic_id,))

    def get_users(self, context, action='DISCUSSION_VIEW'):
        try:
            # Use already customized discussion context.
            return context.users
        except AttributeError:
            # Fallback for pristine Trac context:
            # Return users with satisfying permission.
            return PermissionSystem(self.env) \
                .get_users_with_permission(action)

    # Add item methods.

    def add_group(self, group):
        return self.add_item('forum_group', group)

    def add_forum(self, forum):
        tmp_forum = deepcopy(forum)

        # Pack moderators and subscribers fields.
        tmp_forum['moderators'] = ' '.join(tmp_forum['moderators'])
        tmp_forum['subscribers'] = ' '.join(tmp_forum['subscribers'])

        # Tags are not stored in discussion schema.
        if 'tags' in tmp_forum:
            # DEVEL: Store tags instead of discarging them.
            del tmp_forum['tags']

        return self.add_item('forum', tmp_forum)

    def add_topic(self, topic):
        tmp_topic = deepcopy(topic)

        # Pack subscribers field.
        tmp_topic['subscribers'] = ' '.join(tmp_topic['subscribers'])
        # Encode status field.
        tmp_topic['status'] = topic_status_from_list(
            'status' in tmp_topic and tmp_topic['status'] or [])

        return self.add_item('topic', tmp_topic)

    def add_message(self, message):
        return self.add_item('message', message)

    # Delete item methods

    def delete_group(self, id):
        # Assing forums of this group to 'None' group first.
        self.set_item('forum', 'forum_group', '0', 'forum_group=%s', (id,))
        self.delete_item('forum_group', 'id=%s', (id,))

    def delete_forum(self, id):
        # Delete all forum messages and topics first.
        self.delete_item('message', 'forum=%s', (id,))
        self.delete_item('topic', 'forum=%s', (id,))
        self.delete_item('forum', 'id=%s', (id,))

    def delete_topic(self, id):
        # Delete all topic messages first.
        self.delete_item('message', 'topic=%s', (id,))
        self.delete_item('topic', 'id=%s', (id,))

    def delete_message(self, id):
        # Delete all replies to this message first.
        for reply in self.get_replies(id):
            self.delete_message(reply['id'])
        self.delete_item('message', 'id=%s', (id,))

    # Edit item methods

    def edit_group(self, id, group):
        # Edit forum group.
        self.edit_item('forum_group', id, group)

    def edit_forum(self, id, forum):
        tmp_forum = deepcopy(forum)

        # Pack moderators and subscribers fields.
        if 'moderators' in tmp_forum:
            tmp_forum['moderators'] = ' '.join(tmp_forum['moderators'])
        if 'subscribers' in tmp_forum:
            tmp_forum['subscribers'] = ' '.join(tmp_forum['subscribers'])

        self.edit_item('forum', id, tmp_forum)

    def edit_topic(self, id, topic):
        tmp_topic = deepcopy(topic)

        # Pack subscribers field.
        if 'subscribers' in tmp_topic:
            tmp_topic['subscribers'] = ' '.join(tmp_topic['subscribers'])
        # Encode status field.
        if 'status' in tmp_topic:
            tmp_topic['status'] = topic_status_from_list(tmp_topic['status'])

        self.edit_item('topic', id, tmp_topic)

    def edit_message(self, id, message):
        self.edit_item('message', id, message)

    # Set item methods

    def set_group(self, forum_id, group_id):
        # Change group of specified forum.
        self.set_item('forum', 'forum_group', group_id or '0', 'id=%s',
                      (forum_id,))

    def set_forum(self, topic_id, forum_id):
        # Change forum of all topics and messages.
        self.set_item('topic', 'forum', forum_id, 'id=%s', (topic_id,))
        self.set_item('message', 'forum', forum_id, 'topic=%s', (topic_id,))
