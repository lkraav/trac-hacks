# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2012-2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from copy import deepcopy
from datetime import datetime

from trac.core import Component
from trac.mimeview import Context
from trac.resource import Resource
from trac.search import search_to_sql, shorten_result
from trac.util import shorten_line
from trac.util.datefmt import to_datetime, to_timestamp, utc
from trac.util.text import to_unicode

from tracdiscussion.util import topic_status_from_list, topic_status_to_list


class DiscussionDb(Component):
    """[main] Implements database access methods."""

    abstract = True # not instantiated directly, but as part of API module

    forum_cols = ('id', 'forum_group', 'name', 'subject', 'time', 'author',
                  'moderators', 'subscribers', 'description')
    topic_cols = ('id', 'forum', 'time', 'author', 'subscribers', 'subject',
                  'body', 'status', 'priority')
    message_cols = ('id', 'forum', 'topic', 'replyto', 'time', 'author',
                    'body')
    msg_cols = ('id', 'replyto', 'time', 'author', 'body')

    def _get_item(self, context, table, columns, where='', values=()):
        """Universal single item getter method."""
        if not context:
            # Prepare generic context for database access.
            context = Context('discussion-core')
            context.db = self.env.get_db_cnx()

        sql_values = {
            'columns': ', '.join(columns),
            'table': table,
            'where': where and ' '.join(['WHERE', where]) or ''
        }
        sql = ("SELECT %(columns)s"
               "  FROM %(table)s"
               " %(where)s" % sql_values
        )
        cursor = context.db.cursor()
        cursor.execute(sql, values)
        for row in cursor:
            return dict(zip(columns, row))
        return None

    def _get_items_count(self, context, table, where='', values = ()):
        """Versatile item counter method."""

        sql_values = {
            'table': table,
            'where': where and ' '.join(['WHERE', where]) or ''
        }
        sql = ("SELECT COUNT(id)"
               "  FROM %(table)s"
               " %(where)s" % sql_values
        )
        cursor = context.db.cursor()
        cursor.execute(sql, values)
        for row in cursor:
            return row[0]
        return 0

    # List getter methods.

    def _get_items(self, context, table, columns, where='', values=(),
                   order_by='', desc=False, limit=0, offset=0):
        """Universal dataset getter method."""

        sql_values = {
            'columns': ', '.join(columns),
            'table': table,
            'where': where and ' '.join(['WHERE', where]) or '',
            'order_by': order_by and ' '.join(['ORDER BY', order_by,
                                               ('ASC', 'DESC')[bool(desc)]]) \
                        or '',
            'limit': limit and 'LIMIT %s' or '',
            'offset': offset and 'OFFSET %s' or ''
        }
        sql = ("SELECT %(columns)s"
               "  FROM %(table)s"
               " %(where)s"
               " %(order_by)s"
               " %(limit)s"
               " %(offset)s" % sql_values
        )
        values = list(values)
        if limit:
            values.append(limit)
        if offset:
            values.append(offset)
        cursor = context.db.cursor()
        cursor.execute(sql, values)
        return [dict(zip(columns, row)) for row in cursor]

    def get_groups(self, context, order_by='id', desc=False):
        """Return coarse information on forums by forum group."""

        # Count forums without group assignment.
        unassigned = [dict(id=0, name='None', description='No Group',
                      forums=self._get_items_count(context, 'forum',
                                                   'forum_group=0', []))]
        # Get all grouped forums.
        columns = ('id', 'name', 'description', 'forums')
        if order_by != 'forum':
            # All other group-able columns are from forum_group db table.
            order_by = '.'.join(['g', order_by])
        sql_values = {
            'order_by': order_by and ' '.join(['ORDER BY', order_by,
                                               ('ASC', 'DESC')[bool(desc)]]) \
                        or ''
        }
        sql = ("SELECT g.id, g.name, g.description, f.forums"
               "  FROM forum_group g"
               "  LEFT JOIN"
               "  (SELECT COUNT(id) AS forums, forum_group"
               "     FROM forum"
               "    GROUP BY forum_group) f"
               "  ON g.id = f.forum_group"
               "  %(order_by)s" % sql_values
        )
        cursor = context.db.cursor()
        cursor.execute(sql)
        return unassigned + [dict(zip(columns, row)) for row in cursor]

    def _get_forums(self, context, order_by='subject', desc=False):
        """Return detailed information on forums."""

        forum_cols = self.forum_cols
        topic_cols = ('topics', 'replies', 'lasttopic', 'lastreply')

        # All other group-able columns are from forum db table.
        if not order_by in ('topics', 'replies', 'lasttopic', 'lastreply'):
            order_by = '.'.join(['f', order_by])
        sql_values = {
            'forum_cols': 'f.' + ', f.'.join(forum_cols),
            'topic_cols': 'ta.' + ', ta.'.join(topic_cols),
            'order_by': order_by and ' '.join(['ORDER BY', order_by,
                                               ('ASC', 'DESC')[bool(desc)]]) \
                        or ''
        }
        sql = ("SELECT %(forum_cols)s, %(topic_cols)s"
               "  FROM forum f"
               "  LEFT JOIN"
               "  (SELECT COUNT(t.id) AS topics, MAX(t.time) AS lasttopic,"
                       "  SUM(ma.replies) AS replies,"
                       "  MAX(ma.lastreply) AS lastreply, t.forum AS forum"
                   " FROM topic t"
                   " LEFT JOIN"
                   " (SELECT COUNT(m.id) AS replies,"
                           " MAX(m.time) AS lastreply, m.topic AS topic"
                   "    FROM message m"
                   "   GROUP BY m.topic) ma"
                   " ON t.id=ma.topic"
                   " GROUP BY forum) ta"
               "  ON f.id = ta.forum"
               "  %(order_by)s" % sql_values)
        cursor = context.db.cursor()
        cursor.execute(sql)
        return [dict(zip(forum_cols + topic_cols, row)) for row in cursor]

    def _get_topics(self, context, forum_id, order_by='time', desc=False,
                    limit=0, offset=0, with_body=True):

        # All other group-able columns are from topic db table.
        message_cols = ('replies', 'lastreply')
        topic_cols = list(self.topic_cols)
        if not with_body:
            topic_cols.pop(6)
        topic_cols = tuple(topic_cols) # fixture for subsequent concatenation
        if not order_by in ('replies', 'lastreply'):
            order_by = '.'.join(['t', order_by])
        sql_values = {
            'message_cols': 'm.' + ', m.'.join(message_cols),
            'topic_cols': 't.' + ', t.'.join(topic_cols),
            'order_by': order_by and ' '.join(['ORDER BY', order_by,
                                               ('ASC', 'DESC')[bool(desc)]]) \
                         or '',
            'limit': limit and 'LIMIT %s' or '',
            'offset': offset and 'OFFSET %s' or ''
        }
        sql = ("SELECT %(topic_cols)s, %(message_cols)s"
               "  FROM topic t"
               "  LEFT JOIN"
               "  (SELECT COUNT(id) AS replies, MAX(time) AS lastreply,"
                       "  topic"
                   " FROM message"
               "    GROUP BY topic) m"
               "  ON t.id=m.topic"
               " WHERE t.forum=%%s"
               " %(order_by)s"
               " %(limit)s"
               " %(offset)s" % sql_values)
        values = [forum_id]
        if limit:
            values.append(limit)
        if offset:
            values.append(offset)
        cursor = context.db.cursor()
        cursor.execute(sql, values)
        return [dict(zip(topic_cols + message_cols, row)) for row in cursor]

    def get_changed_topics(self, context, start, stop, order_by='time',
                           desc=False):
        """Return topic content for timeline."""

        columns = ('id', 'forum', 'forum_name', 'time', 'author', 'subject',
                   'status')
        sql_values = {
            'order_by': order_by and ' '.join(['ORDER BY', order_by,
                                               ('ASC', 'DESC')[bool(desc)]]) \
                        or ''
        }
        sql = ("SELECT t.id, t.forum, f.name, t.time, t.author, t.subject,"
                   "   t.status"
               "  FROM topic t"
               "  LEFT JOIN"
               "  (SELECT id, name"
                   " FROM forum) f"
               "  ON t.forum=f.id"
               " WHERE t.time BETWEEN %%s AND %%s"
               " %(order_by)s" % sql_values)
        values = (to_timestamp(start), to_timestamp(stop))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        return [dict(zip(columns, row),
                     status=topic_status_to_list(row['status']))
                for row in cursor]

    def get_messages(self, context, topic_id, order_by='time', desc=False):
        columns = self.msg_cols
        sql_values = {
            'columns': ', '.join(columns),
            'topic_id': topic_id,
            'order_by': order_by and ' '.join(['ORDER BY', order_by,
                                               ('ASC', 'DESC')[bool(desc)]]) \
                        or ''
        }
        sql = ("SELECT %(columns)s"
               "  FROM message"
               " WHERE topic=%%s"
               " %(order_by)s" % sql_values)
        values = [topic_id]

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        messagemap = {}
        messages = []
        for row in cursor:
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

    def get_changed_messages(self, context, start, stop, order_by='time',
                             desc=False):
        """Return message content for timeline."""

        columns = ('id', 'forum', 'forum_name', 'topic', 'topic_subject',
                   'time', 'author')
        sql_values = {
            'order_by': order_by and ' '.join(['ORDER BY', order_by,
                                               ('ASC', 'DESC')[bool(desc)]]) \
                        or ''
        }
        sql = ("SELECT m.id, m.forum, f.name, m.topic, t.subject, m.time,"
                   "   m.author"
               "  FROM message m"
               "  LEFT JOIN"
               "  (SELECT id, name"
                   " FROM forum) f"
               "  ON m.forum=f.id"
               "  LEFT JOIN"
               "  (SELECT id, subject"
                   " FROM topic) t"
               "  ON m.topic=t.id"
               " WHERE time BETWEEN %%s AND %%s"
               " %(order_by)s" % sql_values)
        values = (to_timestamp(start), to_timestamp(stop))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        return [dict(zip(columns, row)) for row in cursor]

    def get_search_results(self, href, terms):
        """Returns discussion content matching TracSearch terms."""

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Search in topics.
        query, args = search_to_sql(db, ['author', 'subject', 'body'], terms)
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        sql = ("SELECT %s"
               "  FROM topic"
               " WHERE %s" % (', '.join(columns), query))
        cursor.execute(sql, args)
        for row in cursor:
            # Class references are valid only in sub-class (api).
            row = dict(zip(columns, row))
            resource = Resource(self.realm, 'forum/%s/topic/%s'
                                            % (row['forum'], row['id']))
            yield (''.join([self.get_resource_url(resource, href), '#-1']),
                   "Topic #%d: %s" % (row['id'],
                                      shorten_line(row['subject'])),
                   to_datetime(row['time'], utc), row['author'],
                   shorten_result(row['body'], [query]))

        # Search in messages.
        query, args = search_to_sql(db, ['m.author', 'm.body', 't.subject'],
                                    terms)
        columns = ('id', 'forum', 'topic', 'time', 'author', 'body', 'subject')
        sql = ("SELECT %s, t.subject"
               "  FROM message m"
               "  LEFT JOIN"
               "  (SELECT subject, id"
                   " FROM topic) t"
               "  ON t.id=m.topic"
               " WHERE %s" % ('m.' + ', m.'.join(columns[:-1]), query))

        cursor.execute(sql, args)
        for row in cursor:
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

    def _add_item(self, context, table, item):
        fields = tuple(item.keys())
        values = tuple(item.values())
        if not 'forum_group' == table:
            fields += ('time',)
            values += (to_timestamp(datetime.now(utc)),)

        sql_values = {
            'table': table,
            'fields': ', '.join(fields),
            'values': ', '.join(('%s',) * len(values))}
        sql = ("INSERT INTO %(table)s"
                   "   (%(fields)s) "
               "VALUES (%(values)s)" % sql_values)

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        context.db.commit()
        return context.db.get_last_id(cursor, table)

    def _delete_item(self, context, table, where='', values=()):
        sql_values = {
            'table': table,
            'where': where and ' '.join(['WHERE', where]) or ''
        }
        sql = ("DELETE FROM %(table)s %(where)s" % sql_values)

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        context.db.commit()

    def _edit_item(self, context, table, id, item):
        sql_values = {
            'table': table,
            'fields' : ', '.join([('%s=%%s' % field)
                                  for field in item.keys()]),
            'id' : id}
        sql = ("UPDATE %(table)s"
               "   SET %(fields)s"
               " WHERE id=%(id)s" % sql_values)

        cursor = context.db.cursor()
        cursor.execute(sql, item.values())
        context.db.commit()

    def _set_item(self, context, table, column, value, where='', values=()):
        sql_values = {
            'table': table,
            'column': column,
            'where': where and ' '.join(['WHERE', where]) or ''
        }
        sql = ("UPDATE %(table)s "
               "   SET %(column)s=%%s"
               " %(where)s" % sql_values)
        values = (value,) + values

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        context.db.commit()
