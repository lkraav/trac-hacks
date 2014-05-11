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
from datetime import datetime

from genshi.input import HTML
from genshi.core import Markup
from genshi.filters import Transformer

from trac.attachment import AttachmentModule, ILegacyAttachmentPolicyDelegate
from trac.core import ExtensionPoint, Interface, TracError
from trac.core import implements
from trac.config import IntOption, Option
from trac.mimeview import Context
from trac.perm import IPermissionRequestor, PermissionError
from trac.resource import IResourceManager, Resource
from trac.web.chrome import Chrome, add_link, add_script, add_stylesheet
from trac.web.chrome import add_ctxtnav
from trac.web.href import Href
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import format_datetime, pretty_timedelta, to_datetime
from trac.util.datefmt import to_timestamp, utc
from trac.util.html import html
from trac.util.presentation import Paginator
from trac.util.text import to_unicode

from tracdiscussion.model import DiscussionDb

try:
    from tractags.api import TagSystem
except ImportError:
    pass


def is_tags_enabled(env):
    return env.is_component_enabled('tractags.api.TagSystem') and \
           env.is_component_enabled('tracdiscussion.tags.DiscussionTags')


class IDiscussionFilter(Interface):
    """Extension point interface for components that want to filter discussion
    topics and messages before their addition.
    """

    def filter_topic(context, topic):
        """ Called before new topic creation. May return tuple (False,
        <error_message>) or (True, <topic>) where <error_message> is a message
        that will be displayed when topic creation will be canceled and <topic>
        is modified topic that will be added.
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
        """Called when a message is created. Argument `message` is a dictionary
        with message attributes.
        """

    def message_changed(context, message, old_message):
        """Called when a message is modified. `old_message` is a dictionary
        containing the previous values of the message attributes and `message`
        is a dictionary with new values that has changed.
        """

    def message_deleted(context, message):
        """Called when a message is deleted. Argument `message` is a dictionary
        with values of attributes of just deleted message.
        """


class DiscussionApi(DiscussionDb):
    """[main] Provides essential definitions including configuration options,
    permission actions and request handling instructions.

    Database access methods are inherited from
    `tracdiscussion.model.DiscussionDb`.
    """

    implements(ILegacyAttachmentPolicyDelegate, IResourceManager,
               IPermissionRequestor)

    default_topic_display = Option(
        'discussion', 'default_topic_display', 'classic',
        doc='Default display mode for forum topics list.')
    default_message_display = Option(
        'discussion', 'default_message_display', 'tree',
        doc='Default display mode for topic messages list.')
    forum_sort = Option(
        'discussion', 'forum_sort', 'lasttopic',
        doc='Column by which will be sorted forum lists. Possible values '
            'are: id, group, name, subject, time, moderators, description, '
            'topics, replies, lasttopic, lastreply.')
    forum_sort_direction = Option(
        'discussion', 'forum_sort_direction', 'asc',
        doc='Direction of forum lists sorting. Possible values are: '
            'asc, desc.')
    topic_sort = Option(
        'discussion', 'topic_sort', 'lastreply',
        doc='Column by which will be sorted topic lists. Possible values '
            'are: id, forum, subject, time, author, body, replies, lastreply.')
    topic_sort_direction = Option(
        'discussion', 'topic_sort_direction', 'asc',
        doc='Direction of topic lists sorting. Possible values are: '
            'asc, desc.')
    topics_per_page = IntOption(
        'discussion', 'topics_per_page', 30,
        doc='Number of topics per page in topic list.')
    messages_per_page = IntOption(
        'discussion', 'messages_per_page', 50,
        doc='Number of messages per page in message list.')

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
            elif action in ('ATTACHMENT_VIEW'):
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
        # Create context.
        context = Context('discussion-core')

        # Get database access.
        context.db = self.env.get_db_cnx()

        type, id = self._parse_resource_id(resource)

        # Generate description for forums.
        if type == 'forum':
            forum = self._get_item(context, 'forum', ('id', 'name', 'subject'),
              where = 'id = %s', values = (id,))
            if format == 'compact':
                return '#%s' % (forum['id'],)
            elif format == 'summary':
                return 'Forum %s - %s' % (forum['name'], forum['subject'])
            else:
                return 'Forum %s' % (forum['name'],)

        # Generate description for topics.
        elif type == 'topic':
            topic = self._get_item(context, 'topic', ('id', 'subject'), where =
              'id = %s', values = (id,))
            if format == 'compact':
                return '#%s' % (topic['id'],)
            elif format == 'summary':
                return 'Topic #%s (%s)' % (topic['id'], topic['subject'])
            else:
                return 'Topic #%s' % (topic['id'],)

        # Generate description for messages.
        elif type == 'message':
            if format == 'compact':
                return '#%s' % (id,)
            elif format == 'summary':
                return 'Message #%s' % (id,)
            else:
                return 'Message #%s' % (id,)

    def resource_exists(self, resource):
        # Create context.
        context = Context('discussion-core')

        # Get database access.
        context.db = self.env.get_db_cnx()

        type, id = self._parse_resource_id(resource)

        # Check if forum exists.
        if type == 'forum':
            return self._get_item(context, 'forum', ('id',), where = 'id = %s',
              values = (id,)) != None

        # Check if topic exits.
        elif type == 'topic':
            return self._get_item(context, 'topic', ('id',), where = 'id = %s',
              values = (id,)) != None

        # Check if message exists.
        elif type == 'message':
            return self._get_item(context, 'message', ('id',), where = 'id = %s',
              values = (id,)) != None

    # Main request processing function.

    def process_discussion(self, context):
        # Get database access.
        context.db = self.env.get_db_cnx()

        # Get request items and actions.
        self._prepare_context(context)
        actions = self._get_actions(context)
        self.log.debug('actions: %s' % (actions,))
        self.log.debug('req.args: %s' % (str(context.req.args)))

        # Get session data.
        context.visited_forums = eval(context.req.session.get('visited-forums')
          or '{}')
        context.visited_topics = eval(context.req.session.get('visited-topics')
          or '{}')

        # Perform actions.
        self._do_actions(context, actions)

        # Update session data.
        context.req.session['visited-topics'] = to_unicode(context.visited_topics)
        context.req.session['visited-forums'] = to_unicode(context.visited_forums)

        # Fill up template data structure.
        context.data['users'] = context.users
        context.data['has_tags'] = context.has_tags
        context.data['group'] = context.group
        context.data['forum'] = context.forum
        context.data['topic'] = context.topic
        context.data['message'] = context.message
        context.data['moderator'] = context.moderator
        context.data['authname'] = context.req.authname
        context.data['authemail'] = context.authemail
        context.data['realm'] = context.realm
        context.data['mode'] = actions[-1]
        context.data['time'] = datetime.now(utc)
        context.data['env'] = self.env

        # Add context navigation.
        if context.forum:
            add_ctxtnav(context.req, 'Forum Index',
              context.req.href.discussion())
        if context.topic:
            add_ctxtnav(context.req, format_to_oneliner_no_links(self.env,
              context, context.forum['name']), context.req.href.discussion(
              'forum', context.forum['id']), context.forum['name'])
        if context.message:
            add_ctxtnav(context.req, format_to_oneliner_no_links(self.env,
              context, context.topic['subject']), context.req.href.discussion(
              'topic', context.topic['id']), context.topic['subject'])

        # Add CSS styles and scripts.
        add_stylesheet(context.req, 'common/css/wiki.css')
        add_stylesheet(context.req, 'discussion/css/discussion.css')
        add_stylesheet(context.req, 'discussion/css/admin.css')
        add_script(context.req, 'common/js/trac.js')
        add_script(context.req, 'common/js/search.js')
        add_script(context.req, 'common/js/wikitoolbar.js')
        add_script(context.req, 'discussion/js/discussion.js')

        # Determine template name.
        context.template = self._get_template(context, actions)

        # Return request template and data.
        self.log.debug('template: %s data: %s' % (context.template,
          context.data,))
        return context.template, {'discussion' : context.data}

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
        if match:
            forum, topic, message = match.groups()
            if message:
                type = 'message'
                id = message
            elif topic:
                type = 'topic'
                id = topic
            elif forum:
                type = 'forum'
                id = forum
        else:
            type, id = resource.id.split('/')
        return type, id

    def _prepare_context(self, context):
        # Prepare template data.
        context.data = {}

        # Get list of Trac users.
        context.users = self.get_users(context)

        # Check if TracTags plugin is enabled.
        context.has_tags = is_tags_enabled(self.env)

        # Populate active message.
        context.group = None
        context.forum = None
        context.topic = None
        context.message = None

        realm = Resource(self.realm)
        if 'message' in context.req.args:
            message_id = int(context.req.args.get('message') or 0)
            context.message = self.get_message(context, message_id)
            if not context.message:
                raise TracError('Message with ID %s does not exist.'
                                % message_id)
            # Create request resource.
            context.topic = self.get_topic(context, context.message['topic'])
            context.forum = self.get_forum(context, context.topic['forum'])
            context.group = self.get_group(context,
                                           context.forum['forum_group'])
            context.resource = realm(id='forum/%s/topic/%s/message/%s'
                                        % (context.forum['id'],
                                           context.topic['id'],
                                           context.message['id']))

        # Populate active topic.
        elif context.req.args.has_key('topic'):
            topic_id = int(context.req.args.get('topic') or 0)
            context.topic = self.get_topic(context, topic_id)
            if not context.topic:
                raise TracError('Topic with ID %s does not exist.' % topic_id)

            # Create request resource.
            context.forum = self.get_forum(context, context.topic['forum'])
            context.group = self.get_group(context,
                                           context.forum['forum_group'])
            context.resource = realm(id='forum/%s/topic/%s'
                                        % (context.forum['id'],
                                           context.topic['id']))

        # Populate active forum.
        elif context.req.args.has_key('forum'):
            forum_id = int(context.req.args.get('forum') or 0)
            context.resource = realm(id='forum/%s' % forum_id)
            context.forum = self._get_forum(context)
            if not context.forum:
                raise TracError('Forum with ID %s does not exist.' % forum_id)

            context.group = self.get_group(context,
                                           context.forum['forum_group'])

        # Populate active group.
        elif context.req.args.has_key('group'):
            group_id = int(context.req.args.get('group') or 0)
            context.group = self.get_group(context, group_id)
            if not context.group:
                raise TracError('Group with ID %s does not exist.' % group_id)

            # Create request resource.
            context.resource = realm(id='group/%s' % context.group['id'])

        # Determine moderator rights.
        context.moderator = context.forum and \
            (context.req.authname in context.forum['moderators']) and \
            context.req.perm.has_permission('DISCUSSION_MODERATE')

        # Determine if user has e-mail set.
        context.authemail = context.req.session.get('email')

        # Prepare other general context attributes.
        context.redirect_url = None
        context.format = context.req.args.get('format')

    def _get_actions(self, context):
        # Get action.
        action = context.req.args.get('discussion_action')
        preview = context.req.args.has_key('preview');
        submit = context.req.args.has_key('submit');
        self.log.debug('realm: %s, action: %s, format: %s preview: %s, submit:'
          ' %s' % (context.realm, action, context.format, preview, submit))

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
                    return ['topic-quote','wiki-message-list']
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
        for action in actions:
            if action == 'group-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Display groups.
                context.data['groups'] = self.get_groups(context)

            elif action == 'admin-group-list':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc') == '1'

                # Display groups.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['groups'] = self.get_groups(context, order, desc)

            elif action == 'group-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

            elif action == 'group-post-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                group = {'name' : context.req.args.get('name'),
                         'description' : context.req.args.get('description')}

                # Add new group.
                self.add_group(context, group)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'group-post-edit':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                group = {'name' : context.req.args.get('name'),
                         'description' : context.req.args.get('description')}

                # Edit group.
                self.edit_group(context, context.group['id'], group)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'group-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'groups-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get selected groups.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete selected groups.
                if selection:
                    for group_id in selection:
                        self.delete_group(context, int(group_id))

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'forum-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values.
                order = context.req.args.get('order') or self.forum_sort
                if 'desc' in context.req.args:
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.forum_sort_direction == 'desc'

                # Display forums.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['groups'] = self.get_groups(context)
                context.data['forums'] = self.get_forums(context, order, desc)

            elif action == 'admin-forum-list':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get ordering arguments values.
                order = context.req.args.get('order') or self.forum_sort
                if 'desc' in context.req.args:
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.forum_sort_direction == 'desc'

                # Display forums.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['groups'] = self.get_groups(context)
                context.data['forums'] = self.get_forums(context, order, desc)

            elif action == 'forum-rss':
                context.req.perm.assert_permission('DISCUSSION_VIEW',
                                                   context.resource)

                # Get topics and messges.
                messages =  self.get_flat_messages_by_forum(context,
                  context.forum['id'], desc = True, limit =
                  self.messages_per_page)
                topics = self.get_topics(context, context.forum['id'],
                  desc = True, limit = self.topics_per_page)

                # Create map of topic subjects.
                topic_subjects = {}
                for message in messages:
                    if not topic_subjects.has_key(message['topic']):
                        topic_subjects[message['topic']] = \
                          self.get_topic_subject(context, message['topic'])

                # Prepare list of topics and messages of the forum.
                context.data['topics'] = topics
                context.data['messages'] = messages
                context.data['topic_subjects'] = topic_subjects

            elif action == 'forum-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Display Add Forum form.
                context.data['groups'] = self.get_groups(context)

            elif action == 'forum-post-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values
                forum = {'name' : context.req.args.get('name'),
                         'author' : context.req.authname,
                         'subject' : context.req.args.get('subject'),
                         'description' : context.req.args.get('description'),
                         'moderators' : context.req.args.get('moderators'),
                         'subscribers' : context.req.args.get('subscribers'),
                         'forum_group' : int(context.req.args.get('group') or 0),
                         'time': to_timestamp(datetime.now(utc)),
                         'tags': context.req.args.get('tags')}

                # Fix moderators attribute to be a list.
                if not forum['moderators']:
                    forum['moderators'] = []
                if not isinstance(forum['moderators'], list):
                    forum['moderators'] = [moderator.strip() for moderator in
                      forum['moderators'].replace(',', ' ').split()]

                # Fix subscribers attribute to be a list.
                if not forum['subscribers']:
                    forum['subscribers'] = []
                if not isinstance(forum['subscribers'], list):
                    forum['subscribers'] = [subscribers.strip() for subscribers
                      in forum['subscribers'].replace(',', ' ').split()]
                forum['subscribers'] += [subscriber.strip() for subscriber in
                  context.req.args.get('unregistered_subscribers').replace(',',
                  ' ').split()]

                # Fix tags attribute to be a list
                if not forum['tags']:
                    forum['tags'] = []
                if not isinstance(forum['tags'], list):
                    forum['tags'] = [tag.strip() for tag in forum['tags']
                      .replace(',', ' ').split()]

                # Perform new forum add.
                self.add_forum(context, forum)

                # Get inserted forum with new ID.
                context.forum = self.get_forum_by_time(context, forum['time'])

                # Copy tags field which is not stored in the database table.
                context.forum['tags'] = forum['tags']

                # Notify change listeners.
                self.log.debug('forum_change_listeners: %s' % (
                  self.forum_change_listeners))
                for listener in self.forum_change_listeners:
                    listener.forum_created(context, context.forum)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'forum-post-edit':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                forum = {'name' : context.req.args.get('name'),
                         'subject' : context.req.args.get('subject'),
                         'description' : context.req.args.get('description'),
                         'moderators' : context.req.args.get('moderators'),
                         'subscribers' : context.req.args.get('subscribers'),
                         'forum_group' : int(context.req.args.get('group') or 0)}

                # Fix moderators attribute to be a list.
                if not forum['moderators']:
                    forum['moderators'] = []
                if not isinstance(forum['moderators'], list):
                    forum['moderators'] = [moderator.strip() for moderator in
                      forum['moderators'].replace(',', ' ').split()]

                # Fix subscribers attribute to be a list.
                if not forum['subscribers']:
                    forum['subscribers'] = []
                if not isinstance(forum['subscribers'], list):
                    forum['subscribers'] = [subscribers.strip() for subscribers
                      in forum['subscribers'].replace(',', ' ').split()]
                forum['subscribers'] += [subscriber.strip() for subscriber in
                  context.req.args.get('unregistered_subscribers').replace(',',
                  ' ').split()]

                # Perform forum edit.
                self.edit_forum(context, context.forum['id'], forum)

                # Notify change listeners.
                for listener in self.forum_change_listeners:
                    listener.forum_changed(context, forum, context.forum)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'forum-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Delete forum.
                self.delete_forum(context, context.forum['id'])

                # Notify change listeners.
                for listener in self.forum_change_listeners:
                    listener.forum_deleted(context, context.forum)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'forums-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get selected forums.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete selected forums.
                if selection:
                    for forum_id in selection:
                        # Delete forum.
                        self.delete_forum(context, int(forum_id))

                        # Notify change listeners.
                        for listener in self.forum_change_listeners:
                            listener.forum_deleted(context, int(forum_id))

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'forum-set-display':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values.
                display = context.req.args.get('display')

                # Set message list display mode to session.
                context.req.session['topic-list-display'] = display

            elif action == 'forum-subscriptions-post-edit':
                context.req.perm.assert_permission('DISCUSSION_MODERATE',
                                                   context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Prepare edited attributes of the forum.
                forum = {'subscribers' : context.req.args.get('subscribers')}
                if not forum['subscribers']:
                    forum['subscribers'] = []
                if not isinstance(forum['subscribers'], list):
                    forum['subscribers'] = [subscribers.strip() for subscribers
                      in forum['subscribers'].replace(',', ' ').split()]
                forum['subscribers'] += [subscriber.strip() for subscriber in
                  context.req.args.get('unregistered_subscribers').replace(',',
                    ' ').split()]

                # Edit topic.
                self.edit_forum(context, context.forum['id'], forum)

                # Notify change listeners.
                for listener in self.forum_change_listeners:
                    listener.forum_changed(context, forum, context.forum)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#subscriptions')

            elif action == 'forum-subscribe':
                context.req.perm.assert_permission('DISCUSSION_VIEW',
                                                   context.resource)
                if context.authemail and not (context.req.authname in
                  context.forum['subscribers']):

                    # Prepare edited attributes of the forum.
                    forum = {'subscribers' : deepcopy(context.forum[
                      'subscribers'])}
                    forum['subscribers'].append(context.req.authname)

                    # Edit topic.
                    self.edit_forum(context, context.forum['id'], forum)

                    # Notify change listeners.
                    for listener in self.forum_change_listeners:
                        listener.forum_changed(context, forum, context.forum)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#subscriptions')

            elif action == 'forum-unsubscribe':
                context.req.perm.assert_permission('DISCUSSION_VIEW',
                                                   context.resource)
                if context.authemail and (context.req.authname in
                  context.forum['subscribers']):

                    # Prepare edited attributes of the topic.
                    forum = {'subscribers' : deepcopy(context.forum[
                      'subscribers'])}
                    forum['subscribers'].remove(context.req.authname)

                    # Edit topic.
                    self.edit_forum(context, context.forum['id'], forum)

                    # Notify change listeners.
                    for listener in self.forum_change_listeners:
                        listener.forum_changed(context, forum, context.forum)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#subscriptions')

            elif action == 'topic-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW',
                                                   context.resource)

                # Update this forum visit time.
                context.visited_forums[context.forum['id']] = to_timestamp(
                  datetime.now(utc))

                # Get form values.
                order = context.req.args.get('order') or self.topic_sort
                if 'desc' in context.req.args:
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.topic_sort_direction == 'desc'
                page = int(context.req.args.get('discussion_page') or '1') - 1

                # Get topic list display type from session.
                display = context.req.session.get('topic-list-display') or \
                  self.default_topic_display

                # Get topics of the current page.
                topics_count = self.get_topics_count(context,
                  context.forum['id'])
                topics = self.get_topics(context, context.forum['id'], order,
                  desc, self.topics_per_page, page * self.topics_per_page,
                  False)
                paginator = self._get_paginator(context, page,
                  self.topics_per_page, topics_count)

                # Display the topics.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['display'] = display
                context.data['topics'] = topics
                context.data['paginator'] = paginator

            elif action == 'topic-rss':
                context.req.perm.assert_permission('DISCUSSION_VIEW',
                                                   context.resource)

                # Display list of messages for topic.
                context.data['messages'] = self.get_flat_messages(context,
                  context.topic['id'], desc = True, limit =
                  self.messages_per_page);

            elif action == 'topic-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND',
                                                   context.resource)

            elif action == 'topic-quote':
                context.req.perm.assert_permission('DISCUSSION_APPEND',
                                                   context.resource)

                # Prepare old content.
                lines = context.topic['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                context.req.args['body'] = '\n'.join(lines)

            elif action == 'topic-post-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND',
                                                   context.resource)

                # Get form values.
                topic = {'forum' : context.forum['id'],
                         'subject' : context.req.args.get('subject'),
                         'time': to_timestamp(datetime.now(utc)),
                         'author' : context.req.args.get('author'),
                         'subscribers' : context.req.args.get('subscribers'),
                         'body' : context.req.args.get('body')}

                # Fix subscribers attribute to be a list.
                if not topic['subscribers']:
                    topic['subscribers'] = []
                if not isinstance(topic['subscribers'], list):
                    topic['subscribers'] = [subscribers.strip() for subscribers
                      in topic['subscribers'].replace(',', ' ').split()]
                topic['subscribers'] += [subscriber.strip() for subscriber in
                  context.req.args.get('unregistered_subscribers').replace(',',
                        ' ').split()]

                # Add user e-mail if subscription checked.
                if context.req.args.get('subscribe') and context.authemail and \
                  not (context.req.authname in topic['subscribers']):
                    topic['subscribers'].append(context.req.authname)

                # Filter topic.
                for discussion_filter in self.discussion_filters:
                    self.log.debug('filtering topic: %s' % (topic,))
                    accept, topic_or_error = discussion_filter.filter_topic(
                      context, topic)
                    if accept:
                        topic = topic_or_error
                    else:
                        raise TracError(topic_or_error)

                # Add new topic.
                self.add_topic(context, topic)

                # Get inserted topic with new ID.
                context.topic = self.get_topic_by_time(context, topic['time'])

                # Notify change listeners.
                self.log.debug('topic_change_listeners: %s' % (
                  self.topic_change_listeners))
                for listener in self.topic_change_listeners:
                    listener.topic_created(context, context.topic)

                # Redirect request to prevent re-submit.
                if context.realm != 'discussion-wiki':
                    href = Href('discussion')
                    context.redirect_url = (href('topic', context.topic['id']),
                      '#topic')
                else:
                    context.redirect_url = (context.req.path_info, '#topic')

            elif action == 'topic-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND',
                                                   context.resource)
                if not context.moderator and (context.topic['author'] !=
                  context.req.authname):
                    raise PermissionError('Topic edit')

                # Prepare form values.
                context.req.args['subject'] = context.topic['subject']
                context.req.args['body'] = context.topic['body']

            elif action == 'topic-post-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND', 
                                                   context.resource)

                # Check if user can edit topic.
                if not context.moderator and (context.topic['author'] !=
                  context.req.authname):
                    raise PermissionError('Topic editing')

                # Check if user can edit locked topic.
                if not context.moderator and ('locked' in
                  context.topic['status']):
                    raise PermissionError("Locked topic editing")

                # Get form values.
                topic = {'subject' : context.req.args.get('subject'),
                         'body' : context.req.args.get('body')}

                # Edit topic.
                self.edit_topic(context, context.topic['id'], topic)

                # Notify change listeners.
                for listener in self.topic_change_listeners:
                    listener.topic_changed(context, topic, context.topic)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#topic')

            elif action == 'topic-edit-attribute':
                # Check general topic editing permission.
                context.req.perm.assert_permission('DISCUSSION_APPEND', 
                                                   context.resource)
                if not context.moderator and (context.topic['author'] !=
                  context.req.authname):
                    raise PermissionError("Topic editing")

                # Get form values.
                if not context.req.args.has_key('name') and \
                  context.req.args.has_key('value'):
                    raise TracError("Missing request arguments.")
                name = context.req.args.get('name')
                value = context.req.args.get('value')

                # Important flag is implemented as integer priority.
                if name == 'important':
                    name = 'priority'
                    value = (value in ('true', 'yes', True) and 1 or 0);

                # Attributes that can be changed only by administrator.
                topic = {}
                if name in ('id', 'time'):
                    context.req.perm.assert_permission('DISCUSSION_ADMIN')
                    topic[name] = value;
                # Attributes that can be changed by moderator.
                elif name in ('forum', 'author', 'subscribers', 'priority',
                  'status.locked', 'status'):
                    context.req.perm.assert_permission('DISCUSSION_MODERATE', 
                                                       context.resource)
                    if not context.moderator:
                        raise PermissionError("Topic editing")

                    # Decode status flag to status list.
                    if name in ('status.locked'):
                        topic['status'] = context.topic['status'].copy()
                        if value in ('true', 'yes', True):
                            topic['status'] |= set(['locked'])
                        else:
                            topic['status'] -= set(['locked'])
                    else:
                        topic[name] = value;

                # Attributes that can be changed by owner of the topic or the
                # moderator.
                elif name in ('subject', 'body', 'status.solved'):

                    self.log.debug((context.topic['author'], context.req.authname))
                    context.req.perm.assert_permission('DISCUSSION_APPEND', 
                                                       context.resource)

                    # Check if user can edit topic.
                    if not context.moderator and (context.topic['author'] !=
                      context.req.authname):
                        raise PermissionError("Topic editing")

                    # Decode status flag to status list.
                    if name in ('status.solved'):
                        topic['status'] = context.topic['status'].copy()
                        if value in ('true', 'yes', True):
                            topic['status'] |= set(['solved'])
                            topic['status'] -= set(['unsolved'])
                        else:
                            topic['status'] |= set(['unsolved'])
                            topic['status'] -= set(['solved'])
                    else:
                        topic[name] = value;
                else:
                    raise PermissionError("Topic editing")

                # Update the attribute value.
                self.edit_topic(context, context.topic['id'], topic)

            elif action == 'topic-move':
                context.req.perm.assert_permission('DISCUSSION_MODERATE', 
                                                   context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Display Move Topic form.
                context.data['forums'] = self.get_forums(context)

            elif action == 'topic-post-move':
                context.req.perm.assert_permission('DISCUSSION_MODERATE', 
                                                   context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Get form values.
                forum_id = int(context.req.args.get('new_forum') or 0)

                # Move topic.
                self.set_forum(context, context.topic['id'], forum_id)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '')

            elif action == 'topic-delete':
                context.req.perm.assert_permission('DISCUSSION_MODERATE', 
                                                   context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Delete topic.
                self.delete_topic(context, context.topic['id'])

                # Notify change listeners.
                for listener in self.topic_change_listeners:
                    listener.topic_deleted(context, context.topic)

                # Redirect request to prevent re-submit.
                if context.realm != 'discussion-wiki':
                    href = Href('discussion')
                    context.redirect_url = (href('forum',
                      context.topic['forum']), '')
                else:
                    context.redirect_url = (context.req.path_info, '')

            elif action == 'topic-set-display':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values.
                display = context.req.args.get('display')

                # Set message list display mode to session.
                context.req.session['message-list-display'] = display

            elif action == 'topic-subscriptions-post-edit':
                context.req.perm.assert_permission('DISCUSSION_MODERATE', 
                                                   context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Prepare edited attributes of the topic.
                topic = {'subscribers' : context.req.args.get('subscribers')}
                if not topic['subscribers']:
                    topic['subscribers'] = []
                if not isinstance(topic['subscribers'], list):
                    topic['subscribers'] = [subscribers.strip() for subscribers
                      in topic['subscribers'].replace(',', ' ').split()]
                topic['subscribers'] += [subscriber.strip() for subscriber in
                  context.req.args.get('unregistered_subscribers').replace(',',
                  ' ').split()]

                # Edit topic.
                self.edit_topic(context, context.topic['id'], topic)

                # Notify change listeners.
                for listener in self.topic_change_listeners:
                    listener.topic_changed(context, topic, context.topic)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#subscriptions')

            elif action == 'topic-subscriptions-post-add':
                context.req.perm.assert_permission('DISCUSSION_VIEW', 
                                                   context.resource)

                # Prepare edited attributes of the forum..
                topic = {'subscribers' : context.topic['subscribers']}
                for subscriber in context.req.args.get('subscribers') \
                  .replace(',', ' ').split():
                    subscriber.strip()
                    if not subscriber in topic['subscribers']:
                        topic['subscribers'].append(subscriber)

                # Edit topic.
                self.edit_topic(context, context.topic['id'], topic)

                # Notify change listeners.
                for listener in self.topic_change_listeners:
                    listener.topic_changed(context, topic, context.topic)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#subscriptions')

            elif action == 'topic-subscribe':
                context.req.perm.assert_permission('DISCUSSION_VIEW', 
                                                   context.resource)

                if context.authemail and not (context.req.authname in
                  context.topic['subscribers']):

                    # Prepare edited attributes of the topic.
                    topic = {'subscribers' : deepcopy(context.topic[
                      'subscribers'])}
                    topic['subscribers'].append(context.req.authname)

                    # Edit topic.
                    self.edit_topic(context, context.topic['id'], topic)

                    # Notify change listeners.
                    for listener in self.topic_change_listeners:
                        listener.topic_changed(context, topic, context.topic)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#subscriptions')

            elif action == 'topic-unsubscribe':
                context.req.perm.assert_permission('DISCUSSION_VIEW', 
                                                   context.resource)

                if context.authemail and (context.req.authname in
                  context.topic['subscribers']):

                    # Prepare edited attributes of the topic.
                    topic = {'subscribers' : deepcopy(context.topic[
                      'subscribers'])}
                    topic['subscribers'].remove(context.req.authname)

                    # Edit topic.
                    self.edit_topic(context, context.topic['id'], topic)

                    # Notify change listeners.
                    for listener in self.topic_change_listeners:
                        listener.topic_changed(context, topic, context.topic)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#subscriptions')

            elif action == 'message-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW', 
                                                   context.resource)
                self._prepare_message_list(context, context.topic)

            elif action == 'wiki-message-list':
                if context.topic:
                    self._prepare_message_list(context, context.topic)

            elif action == 'message-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND', 
                                                   context.resource)

            elif action == 'message-quote':
                context.req.perm.assert_permission('DISCUSSION_APPEND', 
                                                   context.resource)

                # Prepare old content.
                lines = context.message['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                context.req.args['body'] = '\n'.join(lines)

            elif action == 'message-post-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND', 
                                                   context.resource)

                # Check if user can post to locked topic.
                if not context.moderator and ('locked' in
                  context.topic['status']):
                    raise PermissionError("Locked topic posting")

                # Get form values.
                message = {'forum' : context.forum['id'],
                           'topic' : context.topic['id'],
                           'replyto' : context.message and context.message['id']
                              or -1,
                           'author' : context.req.args.get('author'),
                           'body' : context.req.args.get('body'),
                           'time' : to_timestamp(datetime.now(utc))}

                # Filter message.
                for discussion_filter in self.discussion_filters:
                    self.log.debug('filtering message: %s' % (message,))
                    accept, message_or_error = discussion_filter.filter_message(
                      context, message)
                    if accept:
                        message = message_or_error
                    else:
                        raise TracError(message_or_error)

                # Add message.
                self.add_message(context, message)

                # Get inserted message with new ID.
                context.message = self.get_message_by_time(context,
                  message['time'])

                # Notify change listeners.
                self.log.debug('message_change_listeners: %s' % (
                  self.message_change_listeners))
                for listener in self.message_change_listeners:
                    listener.message_created(context, context.message)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#message%s' % (
                  context.message['id'],))

            elif action == 'message-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND', 
                                                   context.resource)
                if not context.moderator and (context.message['author'] !=
                  context.req.authname):
                    raise PermissionError('Message edit')

                # Prepare form values.
                context.req.args['body'] = context.message['body']

            elif action == 'message-post-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND', 
                                                   context.resource)

                # Check if user can edit message.
                if not context.moderator and (context.message['author'] !=
                  context.req.authname):
                    raise PermissionError('Message edit')

                # Check if user can edit locked topic.
                if not context.moderator and ('locked' in
                  context.topic['status']):
                    raise PermissionError("Locked topic editing")

                # Get form values.
                message = {'body' : context.req.args.get('body')}

                # Edit message.
                self.edit_message(context, context.message['id'], message)

                # Notify change listeners.
                for listener in self.message_change_listeners:
                    listener.message_changed(context, message, context.message)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#message%s' % (
                  context.message['id'],))

            elif action == 'message-delete':
                context.req.perm.assert_permission('DISCUSSION_MODERATE', 
                                                   context.resource)
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Delete message.
                self.delete_message(context, context.message['id'])

                # Notify change listeners.
                for listener in self.message_change_listeners:
                    listener.message_deleted(context, context.message)

                # Redirect request to prevent re-submit.
                context.redirect_url = (context.req.path_info, '#message%s' % (
                  context.message['replyto'],))

        # Redirection is not necessary.
        return None

    def _prepare_message_list(self, context, topic):
        # Get time when topic was visited from session.
        visit_time = int(context.visited_topics.has_key(topic['id']) and
          (context.visited_topics[topic['id']] or 0))

        # Get form values
        page = int(context.req.args.get('discussion_page') or '1') - 1

        # Update this topic visit time.
        context.visited_topics[topic['id']] = to_timestamp(datetime.now(utc))

        # Get topic messages for the current page.
        display = context.req.session.get('message-list-display') or \
          self.default_message_display
        if display == 'flat-asc':
            messages_count = self.get_messages_count(context, topic['id'])
            messages = self.get_flat_messages(context, topic['id'], desc =
              False, limit = self.messages_per_page, offset = page *
              self.messages_per_page)
        elif display in ('flat-desc', 'flat'):
            messages_count = self.get_messages_count(context, topic['id'])
            messages = self.get_flat_messages(context, topic['id'], desc =
              True, limit = self.messages_per_page, offset = page *
              self.messages_per_page)
        elif display in ('tree', ''):
            messages_count = 0
            messages = self.get_messages(context, topic['id'])
        else:
            raise TracError('Unsupported display mode: %s' % (display))

        # Create paginator.
        paginator = self._get_paginator(context, page, self.messages_per_page,
          messages_count, anchor = '#topic')

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
        context.resource = Resource('discussion', '/'.join(
                                    context.resource.id.split('/')[-2:]))
        context.data['attachments'] = AttachmentModule(self.env) \
                                      .attachment_data(context)
        context.resource = real_resource

    def _get_paginator(self, context, page, items_limit, items_count,
      anchor = ''):
        # Create paginator object.
        paginator = Paginator([], page, items_limit, items_count)

        # Initialize pages.
        page_data = []
        shown_pages = paginator.get_shown_pages(21)
        for shown_page in shown_pages:
            page_data.append([context.req.href(context.req.path_info,
              discussion_page = shown_page, order = context.req.args.get('order'),
              desc = context.req.args.get('desc')) + anchor, None, to_unicode(shown_page),
              'page %s' % (shown_page,)])
        fields = ['href', 'class', 'string', 'title']
        paginator.shown_pages = [dict(zip(fields, p)) for p in page_data]

        paginator.current_page = {'href' : None, 'class' : 'current', 'string':
          str(page + 1), 'title' : None}

        # Prepare links to next or previous page.
        if paginator.has_next_page:
            add_link(context.req, 'next', context.req.href(
              context.req.path_info, discussion_page = paginator.page + 2,
              order = context.req.args.get('order'), desc = context.req.args.get('desc'))
                     + anchor, 'Next Page')
        if paginator.has_previous_page:
            add_link(context.req, 'prev', context.req.href(
              context.req.path_info, discussion_page = paginator.page,
                        order = context.req.args.get('order'), desc = context.req.args.get('desc'))
                     + anchor, 'Previous Page')

        return paginator

    def get_group(self, context, id):
        # Get forum group.
        return self._get_item(context, 'forum_group',
                              ('id', 'name', 'description'), 'id=%s', (id,)
               ) or dict(id=0, name='None', description='No Group')

    def get_topic(self, context, id):
        # Get topic by ID.
        topic = self._get_item(context, 'topic', self.topic_cols, 'id=%s',
                               (id,))
        return self._prepare_topic(context, topic)

    def get_topic_by_time(self, context, time):
        # Get topic by time of creation.
        topic = self._get_item(context, 'topic', self.topic_cols, 'time=%s',
                               (time,))
        return self._prepare_topic(context, topic)

    def get_topic_by_subject(self, context, subject):
        # Get topic by subject.
        topic = self._get_item(context, 'topic', self.topic_cols,
                               'subject=%s', (subject,))
        return self._prepare_topic(context, topic)

    def _prepare_topic(self, context, topic):
        """Unpack list of topic subscribers and get topic status."""
        if topic:
            topic['subscribers'] = as_list(topic['subscribers'])
            topic['unregistered_subscribers'] = [
                subscriber for subscriber in topic['subscribers']
                if subscriber not in context.users
            ]
            topic['status'] = self._topic_status_to_list(topic['status'])
        return topic

    def _topic_status_to_list(self, status):
        if status == 0:
            return set(['unsolved'])
        status_list = set([])
        if status & 0x01:
            status_list.add('solved')
        else:
            status_list.add('unsolved')
        if status & 0x02:
            status_list.add('locked')
        return status_list

    def _topic_status_from_list(self, status_list):
        status = 0
        if 'solved' in status_list:
            status = status | 0x01
        if 'locked' in status_list:
            status = status | 0x02
        return status

    def get_forum(self, context, forum_id):
        context.resource = Resource(self.realm, 'forum/%s' % forum_id)
        return self._get_forum(context)

    def get_forum_by_time(self, context, time):
        # Get forum by time of creation.
        forum_id = self._get_item(context, 'forum', ('id',), 'time=%s',
                                  (time,))
        return self.get_forum(context, forum_id)

    def _get_forum(self, context):
        # Get forum by ID.
        forum = self._get_item(context, 'forum', self.forum_cols, 'id=%s',
                               (context.resource.id.split('/')[-1],))
        # Unpack list of moderators and subscribers and get forum tags.
        if forum:
            forum['moderators'] = as_list(forum['moderators'])
            forum['subscribers'] = as_list(forum['subscribers'])
            forum['unregistered_subscribers'] = set(forum['subscribers']) \
                                                .difference(context.users)
            if context.has_tags:
                tag_system = TagSystem(self.env)
                forum['tags'] = tag_system.get_tags(context.req,
                                                    context.resource)
        return forum

    def get_forums(self, context, order_by='subject', desc=False):

        def _new_replies_count(context, forum_id):
            # Get IDs of topics in this forum.
            where = "forum=%s"
            topics = [topic['id'] for topic in self._get_items(
                          context, 'topic', ('id',), where, (forum_id,))]
            # Count unseen messages.
            count = 0
            for topic_id in topics:
                values = (topic_id, topic_id in context.visited_topics and
                                    int(context.visited_topics[topic_id]) or 0)
                where = "topic=%s AND time>%s"
                count += self._get_items_count(context, 'message', where,
                                               values )
            return count

        def _new_topic_count(context, forum_id):
            values = (forum_id, forum_id in context.visited_forums and
                                int(context.visited_forums[forum_id]) or 0)
            where = "forum=%s AND time>%s"
            return self._get_items_count(context, 'topic', where, values)

        forums = self._get_forums(context, order_by, desc)
        # Add some more forum attributes and convert others.
        for forum in forums:
            # Compute count of new replies and topics.
            forum['new_topics'] = _new_topic_count(context, forum['id'])
            forum['new_replies'] = _new_replies_count(context, forum['id'])

            # Convert floating-point result of SUM() above into integer.
            forum['replies'] = int(forum['replies'] or 0)
            forum['moderators'] = as_list(forum['moderators'])
            forum['subscribers'] = as_list(forum['subscribers'])
            forum['unregistered_subscribers'] = set(forum['subscribers']) \
                                                .difference(context.users)

            # Get forum tags.
            if context.has_tags:
                tag_system = TagSystem(self.env)
                forum['tags'] = tag_system.get_tags(context.req, Resource(
                    'discussion', 'forum/%s' % forum['id']))
        return forums

    def get_message(self, context, id):
        # Get message by ID.
        return self._get_item(context, 'message', self.message_cols, 'id=%s',
                              (id,))

    def get_message_by_time(self, context, time):
        # Get message by time of creation.
        return self._get_item(context, 'message', self.message_cols,
                              'time=%s', (time,))

    # Attribute getter methods.

    def get_topic_subject(self, context, id):
        # Get subject of the topic.
        return self._get_item(context, 'topic', ('subject',), 'id=%s',
                              (id,))['subject']
    # Counter methods.

    def get_topics_count(self, context, forum_id):
        return self._get_items_count(context, 'topic', 'forum=%s',
                                     (forum_id,))

    def get_messages_count(self, context, topic_id):
        return self._get_items_count(context, 'message', 'topic=%s',
                                     (topic_id,))


def as_list(value):
    if isinstance(value, basestring):
        return [s.strip() for s in value.split()]
    # Handle None value and empty objects gracefully.
    if not value:
        return []
    raise NotImplementedError('Conversion of %r to list is not implemented'
                              % value)

# Formats wiki text to single line HTML but removes all links.
def format_to_oneliner_no_links(env, context, content):
    stream = HTML(format_to_oneliner(env, context, to_unicode(content)))
    return Markup(stream | Transformer('//a').unwrap())
