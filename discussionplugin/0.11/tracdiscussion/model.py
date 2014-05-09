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
from trac.resource import Resource
from trac.util.datefmt import to_timestamp
from trac.util.text import to_unicode

try:
    from tractags.api import TagSystem
except:
    pass


class DiscussionDb(Component):
    """[main] Implements database access methods."""

    abstract = True

    forum_cols = ('id', 'forum_group', 'name', 'subject', 'time', 'author',
                  'moderators', 'subscribers', 'description')

    # Get one item functions.

    def _get_item(self, context, table, columns, where = '', values = ()):
        sql_values = {'columns' : ', '.join(columns),
          'table' : table,
          'where' : (where and ('WHERE ' + where) or '')}
        sql = ("SELECT %(columns)s "
               "FROM %(table)s "
               "%(where)s" % (sql_values))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        for row in cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_message(self, context, id):
        # Get message by ID.
        return self._get_item(context, 'message', ('id', 'forum', 'topic',
          'replyto', 'time', 'author', 'body'), 'id = %s', (id,))

    def get_message_by_time(self, context, time):
        # Get message by time of creation.
        return self._get_item(context, 'message', ('id', 'forum', 'topic',
          'replyto', 'time', 'author', 'body'), 'time = %s', (time,))

    def get_topic(self, context, id):
        # Get topic by ID.
        topic = self._get_item(context, 'topic', ('id', 'forum', 'time',
          'author', 'subscribers', 'subject', 'body', 'status', 'priority'),
          'id = %s', (id,))

        # Unpack list of subscribers.
        if topic:
            topic['subscribers'] = [subscribers.strip() for subscribers in
              topic['subscribers'].split()]
            topic['unregistered_subscribers'] = []
            for subscriber in topic['subscribers']:
                if subscriber not in context.users:
                    topic['unregistered_subscribers'].append(subscriber)
            topic['status'] = self._topic_status_to_list(topic['status'])

        return topic

    def get_topic_by_time(self, context, time):
        # Get topic by time of creation.
        topic = self._get_item(context, 'topic', ('id', 'forum', 'time',
          'author', 'subscribers', 'subject', 'body', 'status', 'priority'),
          'time = %s', (time,))

        # Unpack list of subscribers.
        if topic:
            topic['subscribers'] = [subscribers.strip() for subscribers in
              topic['subscribers'].split()]
            topic['unregistered_subscribers'] = []
            for subscriber in topic['subscribers']:
                if subscriber not in context.users:
                    topic['unregistered_subscribers'].append(subscriber)
            topic['status'] = self._topic_status_to_list(topic['status'])

        return topic

    def get_topic_by_subject(self, context, subject):
        # Get topic by subject.
        topic = self._get_item(context, 'topic', ('id', 'forum', 'time',
          'author', 'subscribers', 'subject', 'body', 'status', 'priority'),
          'subject = %s', (subject,))

        # Unpack list of subscribers.
        if topic:
            topic['subscribers'] = [subscribers.strip() for subscribers in
              topic['subscribers'].split()]
            topic['unregistered_subscribers'] = []
            for subscriber in topic['subscribers']:
                if subscriber not in context.users:
                    topic['unregistered_subscribers'].append(subscriber)
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

    def get_group(self, context, id):
        # Get forum group or none group.
        return self._get_item(context, 'forum_group', ('id', 'name',
          'description'), 'id = %s', (id,)) or {'id' : 0, 'name': 'None',
          'description': 'No Group'}

    # Get attribute functions.

    def get_topic_subject(self, context, id):
        # Get subject of the topic.
        topic = self._get_item(context, 'topic', ('subject',), 'id = %s', (id,))
        return topic['subject']

    # Get items count functions.

    def _get_items_count(self, context, table, where = '', values = ()):
        sql_values = {'table' : table,
          'where' : (where and ('WHERE ' + where) or '')}
        sql = ("SELECT COUNT(id) "
               "FROM %(table)s "
               "%(where)s" % (sql_values))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        for row in cursor:
            return row[0]
        return 0

    def get_topics_count(self, context, forum_id):
        return self._get_items_count(context, 'topic', 'forum = %s', (
          forum_id,))

    def get_messages_count(self, context, topic_id):
        return self._get_items_count(context, 'message', 'topic = %s', (
          topic_id,))

    # Get list functions.

    def _get_items(self, context, table, columns, where = '', values = (),
      order_by = '', desc = False, limit = 0, offset = 0):
        sql_values = {'columns' : ', '.join(columns),
          'table' : table,
          'where' : (where and ('WHERE ' + where) or ''),
          'order_by' : (order_by and ('ORDER BY ' + order_by + (' ASC', ' DESC')[bool(desc)]) or ''),
          'limit' : (limit and ('LIMIT ' + to_unicode(limit)) or ''),
          'offset' : (offset and (' OFFSET ' + to_unicode(offset)) or '')}
        sql = ("SELECT %(columns)s "
               "FROM %(table)s "
               "%(where)s "
               "%(order_by)s "
               "%(limit)s "
               "%(offset)s" % (sql_values))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        items = []
        for row in cursor:
            row = dict(zip(columns, row))
            items.append(row)
        return items

    def get_groups(self, context, order_by = 'id', desc = False):
        # Get count of forums without group.
        sql = ("SELECT COUNT(f.id) "
               "FROM forum f "
               "WHERE f.forum_group = 0")

        cursor = context.db.cursor()
        cursor.execute(sql)
        no_group_forums = 0
        for row in cursor:
            no_group_forums = row[0]
        groups = [{'id' : 0, 'name' : 'None', 'description' : 'No Group',
          'forums' : no_group_forums}]

        # Get forum groups.
        if order_by != 'forum':
            order_by = 'g.' + order_by
        columns = ('id', 'name', 'description', 'forums')
        sql_values = {'order_by' : (order_by and ('ORDER BY ' + order_by +
          (' ASC', ' DESC')[bool(desc)]) or '')}
        sql = ("SELECT g.id, g.name, g.description, f.forums "
               "FROM forum_group g "
               "LEFT JOIN "
                 "(SELECT COUNT(id) AS forums, forum_group "
                 "FROM forum "
                 "GROUP BY forum_group) f "
               "ON g.id = f.forum_group "
               "%(order_by)s" % (sql_values))

        cursor = context.db.cursor()
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            groups.append(row)
        return groups

    def get_forums(self, context, order_by = 'subject', desc = False):

        def _get_new_topic_count(context, forum_id):
            sql_values = {'forum_id' : forum_id,
              'time' : int(context.visited_forums.has_key(forum_id) and
                (context.visited_forums[forum_id] or 0))}
            sql = ("SELECT COUNT(id) "
                   "FROM topic t "
                   "WHERE t.forum = %(forum_id)s AND t.time > %(time)s" %
                     (sql_values))

            cursor = context.db.cursor()
            cursor.execute(sql)
            for row in cursor:
                return int(row[0])
            return 0

        def _get_new_replies_count(context, forum_id):
            sql_values = {'forum_id' : forum_id}
            sql = ("SELECT id "
                   "FROM topic t "
                   "WHERE t.forum = %(forum_id)s" % (sql_values))

            cursor = context.db.cursor()
            cursor.execute(sql)
            # Get IDs of topics in this forum.
            topics = []
            for row in cursor:
                topics.append(row[0])

            #Count unseen messages.
            count = 0
            for topic_id in topics:
                sql_values = {'topic_id' : topic_id,
                  'time' : int(context.visited_topics.has_key(topic_id) and
                    (context.visited_topics[topic_id] or 0))}
                sql = ("SELECT COUNT(id) "
                       "FROM message m "
                       "WHERE m.topic = %(topic_id)s AND m.time > %(time)s" %
                       (sql_values))

                cursor = context.db.cursor()
                cursor.execute(sql)
                for row in cursor:
                    count += int(row[0])

            return count

        if not order_by in ('topics', 'replies', 'lasttopic', 'lastreply'):
            order_by = 'f.' + order_by
        columns = ('id', 'name', 'author', 'time', 'moderators', 'subscribers',
          'forum_group', 'subject', 'description', 'topics', 'replies',
          'lasttopic', 'lastreply')
        sql_values = {'order_by' : (order_by and ('ORDER BY ' + order_by + (' ASC',
          ' DESC')[bool(desc)]) or '')}
        sql = ("SELECT f.id, f.name, f.author, f.time, f.moderators, "
                 "f.subscribers, f.forum_group, f.subject, f.description, "
                 "ta.topics, ta.replies, ta.lasttopic, ta.lastreply "
               "FROM forum f "
               "LEFT JOIN "
                 "(SELECT COUNT(t.id) AS topics, MAX(t.time) AS lasttopic, "
                   "SUM(ma.replies) AS replies, MAX(ma.lastreply) AS "
                   "lastreply, t.forum AS forum "
                 "FROM topic t "
                 "LEFT JOIN "
                   "(SELECT COUNT(m.id) AS replies, MAX(m.time) AS lastreply, "
                     "m.topic AS topic "
                   "FROM message m "
                   "GROUP BY m.topic) ma "
                 "ON t.id = ma.topic "
                 "GROUP BY forum) ta "
               "ON f.id = ta.forum "
               "%(order_by)s" %(sql_values))

        cursor = context.db.cursor()
        cursor.execute(sql)

        # Convert certain forum attributes.
        forums = []
        for row in cursor:
            row = dict(zip(columns, row))
            forums.append(row)

        for forum in forums:
            # Compute count of new replies and topics.
            forum['new_topics'] = _get_new_topic_count(context, forum['id'])
            forum['new_replies'] = _get_new_replies_count(context, forum['id'])

            # Convert FP result of SUM() above into integer.
            forum['replies'] = int(forum['replies'] or 0)

            # Split moderators list.
            forum['moderators'] = [subscribers.strip() for subscribers in
              forum['moderators'].split()]

            # Split subscriber list to uregistered and unregistered subscribers.
            forum['subscribers'] = [subscribers.strip() for subscribers in
              forum['subscribers'].split()]
            forum['unregistered_subscribers'] = []
            for subscriber in forum['subscribers']:
                if subscriber not in context.users:
                    forum['unregistered_subscribers'].append(subscriber)

            # Get forum tags.
            self.log.debug(context.resource)
            if context.has_tags:
                tag_system = TagSystem(self.env)
                forum['tags'] = tag_system.get_tags(context.req, Resource(
                  'discussion', 'forum/%s' % (forum['id'])))

        return forums

    def get_changed_forums(self, context, start, stop, order_by = 'time', desc
      = False):
        columns = ('id', 'name', 'author', 'time', 'subject', 'description')
        sql_values = {'order_by' : (order_by and ('ORDER BY ' + order_by + (' ASC', ' DESC')
          [bool(desc)]) and '')}
        sql = ("SELECT f.id, f.name, f.author, f.time, f.subject, f.description "
               "FROM forum f "
               "WHERE f.time BETWEEN %%s AND %%s "
               "%(order_by)s "% (sql_values))
        values = (to_timestamp(start), to_timestamp(stop))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        # Convert row to dictionaries.
        for row in cursor:
            row = dict(zip(columns, row))
            yield row

    def get_topics(self, context, forum_id, order_by = 'time', desc = False,
      limit = 0, offset = 0, with_body = True):

        def _get_new_replies_count(context, topic_id):
            sql_values = {'topic_id' : topic_id,
              'time' : int(context.visited_topics.has_key(topic_id) and
                (context.visited_topics[topic_id] or 0))}
            sql = ("SELECT COUNT(id) "
                   "FROM message m "
                   "WHERE m.topic = %(topic_id)s AND m.time > %(time)s" %
                     (sql_values))

            cursor = context.db.cursor()
            cursor.execute(sql)
            for row in cursor:
                return int(row[0])
            return 0

        # Prepere SQL query.
        if not order_by in ('replies', 'lastreply'):
            order_by = 't.' + order_by
        if with_body:
            columns = ('id', 'forum', 'time', 'author', 'subscribers',
              'subject', 'body', 'status', 'priority', 'replies', 'lastreply')
        else:
            columns = ('id', 'forum', 'time', 'author', 'subscribers',
              'subject', 'status', 'priority', 'replies', 'lastreply')
        sql_values = {'with_body' : (with_body and 't.body, ' or ''),
          'order_by' : (order_by and ('ORDER BY priority DESC' + (", " + order_by + (' ASC',
          ' DESC')[bool(desc)])) or ''),
          'limit' : (limit and 'LIMIT %s' or ''),
          'offset' : (offset and 'OFFSET %s' or '')}
        sql = ("SELECT t.id, t.forum, t.time, t.author, t.subscribers, "
                 "t.subject, %(with_body)s t.status, t.priority, m.replies, "
                 "m.lastreply "
               "FROM topic t "
               "LEFT JOIN "
                 "(SELECT COUNT(id) AS replies, MAX(time) AS lastreply, topic "
                 "FROM message "
                 "GROUP BY topic) m "
               "ON t.id = m.topic "
               "WHERE t.forum = %%s "
               "%(order_by)s "
               "%(limit)s "
               "%(offset)s" % (sql_values))
        values = [forum_id]
        if limit:
            values.append(limit)
        if offset:
            values.append(offset)
        values = tuple(values)

        # Execute the query.
        cursor = context.db.cursor()
        cursor.execute(sql, values)

        # Convert result to dictionaries.
        topics = []
        for row in cursor:
            row = dict(zip(columns, row))
            topics.append(row)

        for topic in topics:
            # Compute count of new replies.
            topic['new_replies'] = _get_new_replies_count(context, topic['id'])
            topic['subscribers'] = [subscribers.strip() for subscribers in
              topic['subscribers'].split()]
            topic['unregistered_subscribers'] = []
            for subscriber in topic['subscribers']:
                if subscriber not in context.users:
                    topic['unregistered_subscribers'].append(subscriber)
            topic['status'] = self._topic_status_to_list(topic['status'])
            if context.has_tags:
                tag_system = TagSystem(self.env)
                topic['tags'] = tag_system.get_tags(context.req, Resource(
                  'discussion', 'topic/%s' % (topic['id'])))
        return topics

    def get_changed_topics(self, context, start, stop, order_by = 'time',
      desc = False):
        columns = ('id', 'forum', 'forum_name', 'time', 'author', 'subject',
          'status')
        sql_values = {'order_by' : (order_by and ('ORDER BY ' + order_by + (' ASC', ' DESC')
          [bool(desc)]) and '')}
        sql = ("SELECT t.id, t.forum, f.name, t.time, t.author, t.subject, "
                 "t.status "
               "FROM topic t "
               "LEFT JOIN "
                 "(SELECT id, name "
                 "FROM forum) f "
               "ON t.forum = f.id "
               "WHERE t.time BETWEEN %%s AND %%s "
               "%(order_by)s" % (sql_values))
        values = (to_timestamp(start), to_timestamp(stop))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        for row in cursor:
            row = dict(zip(columns, row))
            row['status'] = self._topic_status_to_list(row['status'])
            yield row

    def get_messages(self, context, topic_id, order_by = 'time', desc = False):
        order_by = 'm.' + order_by
        columns = ('id', 'replyto', 'time', 'author', 'body')
        sql_values = {'topic_id' : to_unicode(topic_id),
          'order_by' : (order_by and ('ORDER BY ' + order_by + (' ASC',' DESC')[bool(desc)]
            ) or '')}
        sql = ("SELECT m.id, m.replyto, m.time, m.author, m.body "
               "FROM message m "
               "WHERE m.topic = %(topic_id)s "
               "%(order_by)s" % (sql_values))

        cursor = context.db.cursor()
        cursor.execute(sql)
        messagemap = {}
        messages = []
        for row in cursor:
            row = dict(zip(columns, row))
            messagemap[row['id']] = row

            # Add top-level messages to the main list, in order of time.
            if row['replyto'] == -1:
                messages.append(row)

        # Second pass, add replies.
        for message in messagemap.values():
            if message['replyto'] != -1:
                parent = messagemap[message['replyto']]
                if 'replies' in parent:
                    parent['replies'].append(message)
                else:
                    parent['replies'] = [message]
        return messages;

    def get_flat_messages(self, context, id, order_by = 'time', desc = False,
      limit = 0, offset = 0):
        # Return messages of specified topic.
        return self._get_items(context, 'message', ('id', 'replyto', 'time',
          'author', 'body'), 'topic = %s', (id,), order_by, desc, limit, offset)

    def get_flat_messages_by_forum(self, context, id, order_by = 'time',
      desc = False, limit = 0, offset = 0):
        # Return messages of specified topic.
        return self._get_items(context, 'message', ('id', 'replyto', 'topic',
          'time', 'author', 'body'), 'forum = %s', (id,), order_by, desc, limit,
          offset)

    def get_changed_messages(self, context, start, stop, order_by = 'time',
      desc = False):
        columns = ('id', 'forum', 'forum_name', 'topic', 'topic_subject', 'time',
          'author')
        sql_values = {'order_by' : (order_by and ('ORDER BY ' + order_by + (' ASC', ' DESC')
          [bool(desc)]) or '')}
        sql = ("SELECT m.id, m.forum, f.name, m.topic, t.subject, m.time, "
                 "m.author "
               "FROM message m "
               "LEFT JOIN "
                 "(SELECT id, name "
                 "FROM forum) f "
               "ON m.forum = f.id "
               "LEFT JOIN "
                 "(SELECT id, subject "
                 "FROM topic) t "
               "ON m.topic = t.id "
               "WHERE time BETWEEN %%s AND %%s "
               "%(order_by)s"% (sql_values))
        values = (to_timestamp(start), to_timestamp(stop))

        cursor = context.db.cursor()
        cursor.execute(sql, values)
        for row in cursor:
            row = dict(zip(columns, row))
            yield row

    def get_replies(self, context, id, order_by = 'time', desc = False):
        # Return replies of specified message.
        return self._get_items(context, 'message', ('id', 'replyto', 'time',
          'author', 'body'), 'replyto = %s',(id,), order_by, desc)

    def get_users(self, context):
        # Return users that Trac knows.
        users = []
        for user in self.env.get_known_users():
            users.append(user[0])
        return users

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
        tmp_topic['status'] = self._topic_status_from_list(
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
            tmp_topic['status'] = self._topic_status_from_list(tmp_topic['status'])

        # Edit topic.
        self._edit_item(context, 'topic', id, tmp_topic)

    def edit_message(self, context, id, message):
        # Edit message,
        self._edit_item(context, 'message', id, message)
