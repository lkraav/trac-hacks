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

from trac.core import Component
from trac.mimeview import Context
from trac.resource import Resource
from trac.util.datefmt import to_timestamp
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
               " %(where)s" % (sql_values)
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
               " %(where)s" % (sql_values)
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
               " %(offset)s" % (sql_values)
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
               "  %(order_by)s" % (sql_values)
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
               "  %(order_by)s" % (sql_values))
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
               " %(offset)s" % (sql_values))
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
               " %(order_by)s" % (sql_values))
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
               " %(order_by)s" % (sql_values))
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
               " %(order_by)s"% (sql_values))
        values = (to_timestamp(start), to_timestamp(stop))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        return [dict(zip(columns, row)) for row in cursor]

    # Add items functions.

    def _add_item(self, context, table, item):
        fields = tuple(item.keys())
        values = tuple(item.values())
        sql_values = {'table' : table,
         'fields' : ', '.join(fields),
         'values' : ','.join(["%s" for I in range(len(values))])}
        sql = ("INSERT INTO %(table)s "
               "(%(fields)s) "
               "VALUES (%(values)s)" % (sql_values))
        cursor = context.db.cursor()
        cursor.execute(sql, values)
        context.db.commit()

    def add_group(self, context, group):
        self._add_item(context, 'forum_group', group)

    def add_forum(self, context, forum):
        tmp_forum = deepcopy(forum)

        # Pack moderators and subscribers fields.
        tmp_forum['moderators'] = ' '.join(tmp_forum['moderators'])
        tmp_forum['subscribers'] = ' '.join(tmp_forum['subscribers'])

        # Remove tags field.
        if tmp_forum.has_key('tags'):
            del tmp_forum['tags']

        # Add forum.
        self._add_item(context, 'forum', tmp_forum)

    def add_topic(self, context, topic):
        tmp_topic = deepcopy(topic)

        # Pack subscribers field.
        tmp_topic['subscribers'] = ' '.join(tmp_topic['subscribers'])
        tmp_topic['status'] = topic_status_from_list(
          tmp_topic.has_key('status') and tmp_topic['status'] or [])

        self._add_item(context, 'topic', tmp_topic)

    def add_message(self, context, message):
        self._add_item(context, 'message', message)

    # Delete items functions.

    def _delete_item(self, context, table, where = '', values = ()):
        sql_values = {'table' : table,
          'where' : (where and (' WHERE ' + where) or '')}
        sql = ("DELETE FROM %(table)s "
               "%(where)s" % (sql_values))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        context.db.commit()

    def delete_group(self, context, id):
        # Delete group.
        self._delete_item(context, 'forum_group', 'id = %s', (id,))

        # Assing forums of this group to none group.
        self._set_item(context, 'forum', 'forum_group', '0', 'forum_group = %s',
          (id,))

    def delete_forum(self, context, id):
        # Delete all messages of this forum.
        self._delete_item(context, 'message', 'forum = %s', (id,))

        # Delete all topics of this forum.
        self._delete_item(context, 'topic', 'forum = %s', (id,))

        # Finally delete forum.
        self._delete_item(context, 'forum', 'id = %s', (id,))

    def delete_topic(self, context, id):
        # Delete all messages of this topic.
        self._delete_item(context, 'message', 'topic = %s', (id,))

        # Delete topic itself.
        self._delete_item(context, 'topic', 'id = %s', (id,))

    def delete_message(self, context, id):
        # Delete all replies of this message.
        for reply in self.get_replies(context, id):
            self.delete_message(context, reply['id'])

        # Delete message itself.
        self._delete_item(context, 'message', 'id = %s', (id,))

    # Set item functions.

    def _set_item(self, context, table, column, value, where = '', values = ()):
        sql_values = {'table' : table,
          'column' : column,
          'where' : (where and ('WHERE ' + where) and '')}
        sql = ("UPDATE %(table)s "
               "SET %(column)s = %%s "
               "%(where)s" % (sql_values))
        values = (value,) + values

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        context.db.commit()

    def set_group(self, context, forum_id, group_id):
        # Change group of specified forum.
        self._set_item(context, 'forum', 'forum_group', group_id or '0',
          'id = %s', (forum_id,))

    def set_forum(self, context, topic_id, forum_id):
        # Change forum of all topics and messages.
        self._set_item(context, 'topic', 'forum', forum_id, 'id = %s',
          (topic_id,))
        self._set_item(context, 'message', 'forum', forum_id, 'topic = %s',
          (topic_id,))

    # Edit functions.

    def _edit_item(self, context, table, id, item):
        fields = tuple(item.keys())
        values = tuple(item.values())
        sql_values = {'table' : table,
         'fields' : ", ".join([("%s = %%s" % (field)) for field in fields]),
         'id' : id}
        sql = ("UPDATE %(table)s "
               "SET %(fields)s "
               "WHERE id = %(id)s" % (sql_values))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        context.db.commit()

    def edit_group(self, context, id, group):
        # Edit froum group.
        self._edit_item(context, 'forum_group', id, group)

    def edit_forum(self, context, id, forum):
        tmp_forum = deepcopy(forum)

        # Pack moderators and subscribers fields.
        if tmp_forum.has_key('moderators'):
            tmp_forum['moderators'] = ' '.join(tmp_forum['moderators'])
        if forum.has_key('subscribers'):
            tmp_forum['subscribers'] = ' '.join(tmp_forum['subscribers'])

        # Edit forum.
        self._edit_item(context, 'forum', id, tmp_forum)

    def edit_topic(self, context, id, topic):
        tmp_topic = deepcopy(topic)

        # Pack subscribers field.
        if tmp_topic.has_key('subscribers'):
            tmp_topic['subscribers'] = ' '.join(tmp_topic['subscribers'])

        # Encode status field.
        if tmp_topic.has_key('status'):
            tmp_topic['status'] = topic_status_from_list(tmp_topic['status'])

        # Edit topic.
        self._edit_item(context, 'topic', id, tmp_topic)

    def edit_message(self, context, id, message):
        # Edit message,
        self._edit_item(context, 'message', id, message)
