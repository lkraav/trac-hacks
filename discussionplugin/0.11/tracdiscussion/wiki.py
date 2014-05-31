# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2006-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from genshi.builder import tag

from trac.core import Component, TracError, implements
from trac.mimeview.api import Context
from trac.resource import Resource, ResourceNotFound
from trac.web.chrome import Chrome, add_stylesheet
from trac.web.href import Href
from trac.web.main import IRequestFilter
from trac.wiki import IWikiSyntaxProvider
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.wiki.web_ui import WikiModule
from trac.util import format_date, format_datetime
from trac.util.text import to_unicode
from trac.util.translation import _

from tracdiscussion.api import DiscussionApi


class DiscussionWiki(Component):
    """[opt] Implements TracLinks syntax and WikiMacros for references to
    disussion forums, topics and individual messages.
    """

    implements(IRequestFilter, IWikiMacroProvider, IWikiSyntaxProvider)

    # Wiki macro documentation

    view_topic_doc = _("Displays content of a discussion topic. Unless "
        "argument passed, it tries to find the topic with the same name as "
        "the current wiki page. If a name is passed, displays that topic.")

    recent_topics_doc = _("Lists all topics, that have been recently active, "
        "grouping them by the day they were lastly active. Accepts two "
        "parameters: First one is a forum ID. If provided, only topics in "
        "that forum are included in the resulting list. Otherwise topics "
        "from all forums are listed. Second parameter is a number. I. e. "
        "specifying 5 will result in only the five most recently active "
        "topics to be included in the list.")

    def __init__(self):
        self.api = DiscussionApi(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        # Change method from POST to GET.
        match = re.match(r'^/wiki(?:/(.*))?', req.path_info)
        action = req.args.get('discussion_action')
        if match and action and 'POST' == req.method:
            req.environ['REQUEST_METHOD'] = 'GET'
        # Continue processing request.
        return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)

    # IWikiSyntaxProvider methods

    def get_link_resolvers(self):
        yield ('forum', self._discussion_link)
        yield ('last-forum', self._discussion_link)
        yield ('topic', self._discussion_link)
        yield ('last-topic', self._discussion_link)
        yield ('message', self._discussion_link)
        yield ('topic-attachment', self._discussion_attachment_link)
        yield ('raw-topic-attachment', self._discussion_attachment_link)

    def get_wiki_syntax(self):
        return []

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ViewTopic'
        yield 'RecentTopics'

    def get_macro_description(self, name):
        if name == 'ViewTopic':
            return self.view_topic_doc
        elif name == 'RecentTopics':
            return self.recent_topics_doc

    def expand_macro(self, formatter, name, content):
        if not formatter.perm.has_permission('DISCUSSION_VIEW'):
            return
        if name == 'ViewTopic':
            return self._view_topic(formatter, content)
        elif name == 'RecentTopics':
            return self._recent_topics(formatter, content)

    # Internal methods

    def _view_topic(self, formatter, content):

        # Determine topic subject
        page_name = formatter.req.path_info[6:] or 'WikiStart'
        subject = content or page_name

        # Prepare context including db access.
        context = Context.from_request(formatter.req)
        context.realm = 'discussion-wiki'
        context.db = self.env.get_db_cnx()

        try:
            id = int(subject)
            topic = self.api.get_topic(context, id)
        except:
            topic = self.api.get_topic_by_subject(context, subject)

        if topic:
            context.req.args['topic'] = topic['id']
            context.resource = Resource('discussion',
                                        'forum/%s/topic/%s'
                                        % (topic['forum'], topic['id']))
        # Process discussion request.
        template, data = self.api.process_discussion(context)

        # Return rendered template.
        data['discussion']['mode'] = 'message-list'
        data['discussion']['page_name'] = page_name
        if context.redirect_url:
            # Generate HTML elements for redirection.
            href = context.req.href(context.redirect_url[0]) + \
              context.redirect_url[1]
            self.log.debug("Redirecting to %s" % (href))
            return tag.div(tag.strong('Redirect: '),
              ' This page redirects to ', tag.a(href, href = href),
              tag.script("window.location = '" + context.req.href('discussion',
              'redirect', redirect_url = href) + "'", language = "JavaScript"),
              class_ = "system-message")
        else:
            # Render template.
            return to_unicode(Chrome(self.env).render_template(formatter.req,
                                               template, data, 'text/html',
                                               True))

    def _recent_topics(self, formatter, content):
        # Prepare context including db access.
        context = Context.from_request(formatter.req)
        context.realm = 'discussion-wiki'
        context.db = self.env.get_db_cnx()
        context.users = self.api.get_users(context)
        # Don't care for tags here.
        context.has_tags = False

        args, kw = parse_args(content)
        forum_id = None
        limit = 10
        if 1 == len(args):
            limit = args[0]
        elif 2 == len(args):
            forum_id, limit = args[:2]
        else:
            raise TracError("Invalid number of macro arguments.")

        entries = self.api.get_recent_topics(context, forum_id, limit)
        entries_per_date = []
        prevdate = None
        for entry in entries:
            date = format_date(entry['time'])
            if date != prevdate:
                prevdate = date
                entries_per_date.append((date, []))
            forum_name = self.api.get_forum(context, entry['forum'])['name']
            topic_subject = self.api.get_topic_subject(context, entry['topic'])
            entries_per_date[-1][1].append((entry['forum'], forum_name,
                                            entry['topic'], topic_subject))
        href = formatter.href
        return tag.div(
               (tag.h3(date),
                    tag.ul(
                        tag.li(
                            tag.a(forum_name,
                                  href=href.discussion('forum', forum_id)),
                            ': ',
                            tag.a(topic_subject,
                                  href=href.discussion('topic', topic_id)))
                        for forum_id, forum_name, topic_id, topic_subject
                        in entries)
                    )
               for date, entries in entries_per_date)

    def _discussion_link(self, formatter, namespace, params, label):
        # Prepare context including db access.
        context = Context.from_request(formatter.req)
        context.realm = 'discussion-wiki'
        context.db = self.env.get_db_cnx()

        href = formatter.href
        title = label.replace('"', '')
        try:
            id = int(params)
        except (TypeError, ValueError):
            id = -1

        if 'forum' == namespace:
            columns = ('subject',)
            forum = self.api._get_item(context, 'forum', columns, 'id=%s',
                                       (id,))
            if forum:
                return tag.a(label, href=href.discussion('forum', id),
                             title=forum['subject'].replace('"', ''))
            return tag.a(label, href=href.discussion('forum', id),
                         title=title, class_='missing')

        elif 'last-forum' == namespace:
            columns = ('id', 'subject')
            forum = self.api._get_items(context, 'forum', columns,
                                        'forum_group=%s', (id,),
                                        'time', True, limit=1)
            if forum:
                return tag.a(label,
                             href=href.discussion('forum', forum[0]['id']),
                             title=forum[0]['subject'].replace('"', ''))
            return tag.a(label, href=href.discussion('forum', '-1'),
                         title=title, class_='missing')

        elif 'topic' == namespace:
            columns = ('forum', 'subject')
            topic = self.api._get_item(context, 'topic', columns, 'id=%s',
                                       (id,))
            if topic:
                forum_subject = self.api.get_forum_subject(context,
                                                           topic['forum'])
                return tag.a(label, href='%s#-1'
                                         % href.discussion('topic', id),
                             title=('%s: %s'
                                    % (forum_subject, topic['subject']))
                                   .replace('"', ''))
            return tag.a(label, href=href.discussion('topic', id),
                         title=title, class_='missing')

        elif 'last-topic' == namespace:
            columns = ('id', 'forum', 'subject')
            topic = self.api._get_items(context, 'topic', columns,
                                        'forum=%s', (id,),
                                        'time', True, limit=1)
            if topic:
                forum_subject = self.api.get_forum_subject(context,
                                                           topic[0]['forum'])
                return tag.a(label, href='%s#-1'
                                         % (href.discussion('topic',
                                                            topic[0]['id']),),
                             title=('%s: %s'
                                    % (forum_subject, topic[0]['subject']))
                                   .replace('"', ''))
            return tag.a(label, href=href.discussion('topic', '-1'),
                         title=title, class_='missing')

        elif 'message' == namespace:
            message = self.api.get_message(context, id)
            if message:
                forum_subject = self.api.get_forum_subject(context,
                                                           message['forum'])
                topic_subject = self.api.get_topic_subject(context,
                                                           message['topic'])
                return tag.a(label, href='%s#message_%s'
                                         % (href.discussion('topic',
                                                            message['topic']),
                                            id),
                             title=('%s: %s' % (forum_subject, topic_subject))
                                   .replace('"', ''))
            return tag.a(label, href=href.discussion('message', id),
                         title=title, class_='missing')

    def _discussion_attachment_link(self, fmt, namespace, params, label):
        # Prepare context.
        context = Context.from_request(fmt.req)
        context.realm = 'discussion-wiki'

        try:
            id, name = params.split(':')
        except (TypeError, ValueError):
            raise ResourceNotFound('Invalid identifier %s' % params)

        if 'topic-attachment' == namespace:
            return format_to_html(self.env, context,
                                  '[attachment:discussion:topic/%s:%s %s]'
                                  % (id, name, label))

        elif 'raw-topic-attachment' == namespace:
            return format_to_html(self.env, context,
                                  '[raw-attachment:discussion:topic/%s:%s %s]'
                                  % (id, name, label))
