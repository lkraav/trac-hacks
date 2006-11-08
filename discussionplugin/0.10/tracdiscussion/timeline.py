# -*- coding: utf8 -*-

from trac.core import *
from trac.Timeline import ITimelineEventProvider
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import Markup
from trac.util.html import html
import time

class DiscussionTimeline(Component):
    """
        The timeline module implements raising timeline events when
        forums, topics and messages are changed.
    """
    implements(ITimelineEventProvider)

    # ITimelineEventProvider
    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("start: %s, stop: %s, filters: %s" % (start, stop,
          filters))
        if 'discussion' in filters:
            # Create database context
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            format = req.args.get('format')
            self.log.debug("format: %s" % (format))

            # Get forum events
            for forum in self._get_changed_forums(cursor, start, stop):
                self.log.debug("forum: %s" % (forum))
                kind = 'changeset'
                title = Markup('New forum %s created by %s' %
                  (forum['name'], forum['author']))
                time = forum['time']
                author = forum['author']
                if format == 'rss':
                    href = self.env.abs_href.discussion(forum['id'])
                    message = wiki_to_html('%s - %s' % (forum['subject'],
                      forum['description']), self.env, req, db)
                else:
                    href = self.env.href.discussion(forum['id'])
                    message = wiki_to_oneliner('%s - %s' % (forum['subject'],
                      forum['description']), self.env, db)  
                yield kind, href, title, time, author, message

            # Get topic events
            for topic in self._get_changed_topics(cursor, start, stop):
                self.log.debug("topic: %s" % (topic))
                kind = 'newticket'
                title = Markup('New topic on %s created by %s' % \
                  (topic['forum_name'], topic['author']))
                time = topic['time']
                author = topic['author']
                if format == 'rss':
                    href = self.env.abs_href.discussion(topic['forum'],
                      topic['id'])
                    message = wiki_to_html(topic['subject'], self.env, req, db)
                else:
                    href = self.env.href.discussion(topic['forum'], topic['id'])
                    message = wiki_to_oneliner(topic['subject'], self.env, db)
                yield kind, href, title, time, author, message

            # Get message events
            for message in self._get_changed_messages(cursor, start, stop):
                self.log.debug("message: %s" % (message))
                kind = 'editedticket'
                title = Markup('New reply on %s created by %s' % \
                  (message['forum_name'], message['author']))
                time = message['time']
                author = message['author']
                if format == 'rss':
                    href = self.env.abs_href.discussion(message['forum'],
                      message['topic'], message['id']) + '#%s' % (message['id'])
                    message = wiki_to_html(message['topic_subject'], self.env,
                      req, db)
                else:
                    href = self.env.href.discussion(message['forum'],
                      message['topic'], message['id']) + '#%s' % (message['id'])
                    message = wiki_to_oneliner(message['topic_subject'],
                      self.env, db)
                yield kind, href, title, time, author, message

    def get_timeline_filters(self, req):
        if req.perm.has_permission('DISCUSSION_VIEW'):
            yield ('discussion', 'Discussion changes')

    def _get_changed_forums(self, cursor, start, stop):
        columns = ('id', 'name', 'author', 'subject', 'description', 'time')
        sql = "SELECT f.id, f.name, f.author, f.subject, f.description," \
          " f.time FROM forum f WHERE f.time BETWEEN %s AND %s"
        self.log.debug(sql % (start, stop))
        cursor.execute(sql, (start, stop))
        for row in cursor:
            row = dict(zip(columns, row))
            yield row

    def _get_changed_topics(self, cursor, start, stop):
        columns = ('id', 'subject', 'author', 'time', 'forum', 'forum_name')
        sql = "SELECT t.id, t.subject, t.author, t.time, t.forum, f.name" \
          " FROM topic t LEFT JOIN (SELECT name, id FROM forum GROUP BY id)" \
          " f ON t.forum = f.id WHERE time BETWEEN %s AND %s"
        self.log.debug(sql % (start, stop))
        cursor.execute(sql, (start, stop))
        for row in cursor:
            row = dict(zip(columns, row))
            yield row

    def _get_changed_messages(self, cursor, start, stop):
        columns = ('id', 'author', 'time', 'forum', 'topic', 'forum_name',
          'topic_subject')
        sql = "SELECT m.id, m.author, m.time, m.forum, m.topic, f.name," \
          " t.subject FROM message m, (SELECT name, id FROM forum GROUP BY" \
          " id) f, (SELECT subject, id FROM topic GROUP BY id) t WHERE" \
          " t.id = m.topic AND f.id = m.forum AND time BETWEEN %s AND %s"
        self.log.debug(sql % (start, stop))
        cursor.execute(sql, (start, stop))
        for row in cursor:
            row = dict(zip(columns, row))
            yield row
