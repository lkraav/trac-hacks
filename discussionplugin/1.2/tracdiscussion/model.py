# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2012-2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Component
from trac.resource import Resource
from trac.search import search_to_sql, shorten_result
from trac.util import shorten_line
from trac.util.datefmt import datetime_now, to_datetime, to_timestamp, utc

from tracdiscussion.util import topic_status_to_list


class DiscussionDb(Component):
    """[main] Implements database access methods."""

    abstract = True  # not instantiated directly, but as part of API module

    forum_cols = ('id', 'forum_group', 'name', 'subject', 'time', 'author',
                  'moderators', 'subscribers', 'description')
    topic_cols = ('id', 'forum', 'time', 'author', 'subscribers', 'subject',
                  'body', 'status', 'priority')
    message_cols = ('id', 'forum', 'topic', 'replyto', 'time', 'author',
                    'body')
    msg_cols = ('id', 'replyto', 'time', 'author', 'body')

    def get_item(self, table, columns, where='', values=()):
        """Universal single item getter method."""
        sql_values = {
            'columns': ', '.join(columns),
            'table': table,
            'where': ' '.join(['WHERE', where]) if where else ''
        }
        for row in self.env.db_query("""
                SELECT %(columns)s FROM %(table)s %(where)s
                """ % sql_values, values):
            return dict(zip(columns, row))
        return None

    def get_items_count(self, table, where='', values=()):
        """Versatile item counter method."""

        sql_values = {
            'table': table,
            'where': ' '.join(['WHERE', where]) if where else ''
        }
        for count, in self.env.db_query("""
                SELECT COUNT(id) FROM %(table)s %(where)s
                """ % sql_values, values):
            return count
        return 0

    # List getter methods.

    def get_items(self, table, columns, where='', values=(), order_by='',
                  desc=False, limit=0, offset=0):
        """Universal dataset getter method."""

        sql_values = {
            'columns': ', '.join(columns),
            'table': table,
            'where': ' '.join(['WHERE', where]) if where else '',
            'order_by': ' '.join(['ORDER BY', order_by,
                                   ('ASC', 'DESC')[bool(desc)]])
                        if order_by else '',
            'limit': 'LIMIT %s' if limit else '',
            'offset': 'OFFSET %s' if offset else ''
        }
        values = list(values)
        if limit:
            values.append(limit)
        if offset:
            values.append(offset)
        return [dict(zip(columns, row))
                for row in self.env.db_query("""
                    SELECT %(columns)s
                    FROM %(table)s %(where)s %(order_by)s %(limit)s %(offset)s
                    """ % sql_values, values)]

    def get_groups(self, order_by='id', desc=False):
        """Return coarse information on forums by forum group."""

        # Count forums without group assignment.
        unassigned = [dict(id=0, name='None', description='No Group',
                           forums=self.get_items_count('forum',
                                                       'forum_group=0', []))]
        # Get all grouped forums.
        columns = ('id', 'name', 'description', 'forums')
        if order_by != 'forum':
            # All other group-able columns are from forum_group db table.
            order_by = '.'.join(['g', order_by])
        sql_values = {
            'order_by': ' '.join(['ORDER BY', order_by,
                                  ('ASC', 'DESC')[bool(desc)]])
                        if order_by else ''
        }
        return unassigned + \
               [dict(zip(columns, row))
                for row in self.env.db_query("""
                    SELECT g.id, g.name, g.description, f.forums
                    FROM forum_group g
                    LEFT JOIN (SELECT COUNT(id) AS forums, forum_group
                               FROM forum GROUP BY forum_group) f
                     ON g.id = f.forum_group
                    %(order_by)s
                    """ % sql_values)]

    def _get_forums(self, order_by='subject', desc=False):
        """Return detailed information on forums."""

        forum_cols = self.forum_cols
        topic_cols = ('topics', 'replies', 'lasttopic', 'lastreply')

        # All other group-able columns are from forum db table.
        if order_by not in ('topics', 'replies', 'lasttopic', 'lastreply'):
            order_by = '.'.join(['f', order_by])
        sql_values = {
            'forum_cols': 'f.' + ', f.'.join(forum_cols),
            'topic_cols': 'ta.' + ', ta.'.join(topic_cols),
            'order_by': ' '.join(['ORDER BY', order_by,
                                  ('ASC', 'DESC')[bool(desc)]])
                        if order_by else ''
        }
        return [dict(zip(forum_cols + topic_cols, row))
                for row in self.env.db_query("""
                    SELECT %(forum_cols)s, %(topic_cols)s
                    FROM forum f
                    LEFT JOIN
                     (SELECT COUNT(t.id) AS topics,
                       MAX(t.time) AS lasttopic,
                       SUM(ma.replies) AS replies,
                       MAX(ma.lastreply) AS lastreply,
                       t.forum AS forum
                      FROM topic t
                      LEFT JOIN
                       (SELECT COUNT(m.id) AS replies,
                         MAX(m.time) AS lastreply,
                         m.topic AS topic
                        FROM message m
                        GROUP BY m.topic) ma
                      ON t.id=ma.topic
                      GROUP BY forum) ta
                    ON f.id = ta.forum
                    %(order_by)s
                    """ % sql_values)]

    def _get_topics(self, forum_id, order_by='time', desc=False, limit=0,
                    offset=0, with_body=True):

        # All other group-able columns are from topic db table.
        message_cols = ('replies', 'lastreply')
        topic_cols = list(self.topic_cols)
        if not with_body:
            topic_cols.pop(6)
        topic_cols = tuple(topic_cols)  # fixture for subsequent concatenation
        if order_by not in ('replies', 'lastreply'):
            order_by = '.'.join(['t', order_by])
        sql_values = {
            'message_cols': 'm.' + ', m.'.join(message_cols),
            'topic_cols': 't.' + ', t.'.join(topic_cols),
            'order_by': ' '.join(['ORDER BY', order_by,
                                  ('ASC', 'DESC')[bool(desc)]])
                        if order_by else '',
            'limit': 'LIMIT %s' if limit else '',
            'offset': 'OFFSET %s' if offset else ''
        }
        values = [forum_id]
        if limit:
            values.append(limit)
        if offset:
            values.append(offset)
        return [dict(zip(topic_cols + message_cols, row))
                for row in self.env.db_query("""
                    SELECT %(topic_cols)s, %(message_cols)s
                    FROM topic t
                    LEFT JOIN
                     (SELECT COUNT(id) AS replies, MAX(time) AS lastreply,
                       topic
                      FROM message
                      GROUP BY topic) m
                    ON t.id=m.topic
                    WHERE t.forum=%%s
                    %(order_by)s %(limit)s %(offset)s
                    """ % sql_values, values)]

    def get_changed_topics(self, start, stop, order_by='time', desc=False):
        """Return topic content for timeline."""

        columns = ('id', 'forum', 'forum_name', 'time', 'author', 'subject',
                   'status')
        sql_values = {
            'order_by': ' '.join(['ORDER BY', order_by,
                                  ('ASC', 'DESC')[bool(desc)]])
                        if order_by else ''
        }
        values = (to_timestamp(start), to_timestamp(stop))

        idx_status = list(columns).index('status')
        return [dict(zip(columns, row),
                     status=topic_status_to_list(row[idx_status]))
                for row in self.env.db_query("""
                    SELECT t.id, t.forum, f.name, t.time, t.author,
                           t.subject, t.status
                    FROM topic t
                    LEFT JOIN
                     (SELECT id, name FROM forum) f
                    ON t.forum=f.id
                    WHERE t.time BETWEEN %%s AND %%s
                    %(order_by)s
                    """ % sql_values, values)]

    def get_recent_topics(self, forum_id, limit):
        columns = ('forum', 'topic', 'time')
        values = []
        if forum_id:
            values.append(forum_id)
        if limit:
            values.append(limit)
        values = tuple(values)

        return [dict(zip(columns, row))
                for row in self.env.db_query("""
                    SELECT forum, topic, MAX(time) AS max_time
                    FROM (SELECT forum, topic, time FROM message
                          UNION
                          SELECT forum, id AS topic, time
                          FROM topic)
                    %(where)s
                    GROUP BY topic
                    ORDER BY max_time DESC %(limit)s
                    """ % {
                        'where': "WHERE forum=%s" if forum_id else '',
                        'limit': "LIMIT %s" if limit else ''
                    }, values)]

    def get_messages(self, topic_id, order_by='time', desc=False):
        columns = self.msg_cols
        sql_values = {
            'columns': ', '.join(columns),
            'topic_id': topic_id,
            'order_by': ' '.join(['ORDER BY', order_by,
                                  ('ASC', 'DESC')[bool(desc)]])
                        if order_by else ''
        }
        values = [topic_id]

        messagemap = {}
        messages = []
        for row in self.env.db_query("""
                SELECT %(columns)s FROM message
                WHERE topic=%%s %(order_by)s
                """ % sql_values, values):
            row = dict(zip(columns, row))
            messagemap[row['id']] = row
            # Add top-level messages to the main list, in order of time.
            if row['replyto'] == -1:
                messages.append(row)

        # Second pass: Add replies.
        for message in messagemap.values():
            if message['replyto'] != -1:
                parent = messagemap[message['replyto']]
                if 'replies' in parent:
                    parent['replies'].append(message)
                else:
                    parent['replies'] = [message]
        return messages

    def get_changed_messages(self, start, stop, order_by='time', desc=False):
        """Return message content for timeline."""

        columns = ('id', 'forum', 'forum_name', 'topic', 'topic_subject',
                   'time', 'author')
        sql_values = {
            'order_by': ' '.join(['ORDER BY', order_by,
                                  ('ASC', 'DESC')[bool(desc)]])
                        if order_by else ''
        }
        values = (to_timestamp(start), to_timestamp(stop))

        return [dict(zip(columns, row))
                for row in self.env.db_query("""
                    SELECT m.id, m.forum, f.name, m.topic, t.subject,
                           m.time, m.author
                    FROM message m
                    LEFT JOIN
                     (SELECT id, name FROM forum) f
                    ON m.forum=f.id
                    LEFT JOIN (SELECT id, subject FROM topic) t
                    ON m.topic=t.id
                    WHERE time BETWEEN %%s AND %%s
                    %(order_by)s
                    """ % sql_values, values)]

    def get_search_results(self, href, terms):
        """Returns discussion content matching TracSearch terms."""

        # Search in topics.
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        with self.env.db_query as db:
            query, args = search_to_sql(db, ['author', 'subject', 'body'],
                                        terms)

            for row in db("""
                    SELECT %s FROM topic WHERE %s
                    """ % (', '.join(columns), query), args):
                # Class references are valid only in sub-class (api).
                row = dict(zip(columns, row))
                resource = Resource(self.realm, 'forum/%s/topic/%s'
                                    % (row['forum'], row['id']))
                yield (''.join(
                    [self.get_resource_url(resource, href), '#-1']),
                       "Topic #%d: %s" % (row['id'],
                                          shorten_line(row['subject'])),
                       to_datetime(row['time'], utc), row['author'],
                       shorten_result(row['body'], [query]))

            # Search in messages.
            query, args = search_to_sql(db,
                                        ['m.author', 'm.body', 't.subject'],
                                        terms)
            columns = ('id', 'forum', 'topic', 'time', 'author', 'body',
                       'subject')

            for row in db("""
                    SELECT %s, t.subject FROM message m
                    LEFT JOIN (SELECT subject, id FROM topic) t
                     ON t.id=m.topic
                    WHERE %s
                    """ % ('m.' + ', m.'.join(columns[:-1]), query), args):
                # Class references are valid only in sub-class (api).
                row = dict(zip(columns, row))
                parent = Resource(self.realm, 'forum/%s/topic/%s'
                                  % (row['forum'], row['topic']))
                resource = Resource(self.realm,
                                    'forum/%s/topic/%s/message/%s'
                                    % (row['forum'], row['topic'], row['id']),
                                    parent=parent)
                yield (self.get_resource_url(resource, href),
                       "Message  #%d: %s" % (row['id'],
                                             shorten_line(row['subject'])),
                       to_datetime(row['time'], utc), row['author'],
                       shorten_result(row['body'], [query]))

    # Item manipulation methods.

    def add_item(self, table, item):
        fields = tuple(item.keys())
        values = tuple(item.values())
        if not 'forum_group' == table:
            fields += ('time',)
            values += (to_timestamp(datetime_now(utc)),)

        sql_values = {
            'table': table,
            'fields': ', '.join(fields),
            'values': ', '.join(('%s',) * len(values))
        }

        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO %(table)s (%(fields)s) VALUES (%(values)s)
                """ % sql_values, values)
            return db.get_last_id(cursor, table)

    def delete_item(self, table, where='', values=()):
        sql_values = {
            'table': table,
            'where': ' '.join(['WHERE', where]) if where else ''
        }

        self.env.db_transaction("""
            DELETE FROM %(table)s %(where)s
            """ % sql_values, values)

    def edit_item(self, table, id, item):
        sql_values = {
            'table': table,
            'fields': ', '.join(('%s=%%s' % field) for field in item.keys()),
            'id': id
        }

        self.env.db_transaction("""
            UPDATE %(table)s SET %(fields)s WHERE id=%(id)s
            """ % sql_values, item.values())

    def set_item(self, table, column, value, where='', values=()):
        sql_values = {
            'table': table,
            'column': column,
            'where': ' '.join(['WHERE', where]) if where else ''
        }
        values = (value,) + values

        self.env.db_transaction("""
            UPDATE %(table)s SET %(column)s=%%s %(where)s
            """ % sql_values, values)
