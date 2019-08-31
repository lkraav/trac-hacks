# -*- coding: utf-8 -*-

from datetime import datetime

from trac.db import Table, Column, Index
from trac.util import to_list
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc


SCHEMA = [
    Table('pullrequests', key='id')[
        Column('id', auto_increment=True),
        Column('status'),
        Column('author'),
        Column('reviewers'),
        Column('opened', type='int64'),
        Column('modified', type='int64'),
        Column('ticket', type='int'),
        Column('comment', type='int'),
        Column('wikilink'),
        Index(['status']),
        Index(['author']),
    ],
]


class PullRequest(object):

    def __init__(self, id, status, author, reviewers, opened, modified, ticket, comment, wikilink):
        self.id = id
        self.status = status
        self.author = author
        self.reviewers = reviewers
        self.opened = opened
        self.modified = modified
        self.ticket = ticket
        self.comment = comment
        self.wikilink = wikilink

    def add_reviewer(self, reviewer):
        if reviewer != self.author:
            rset = set(to_list(self.reviewers))
            rset.add(reviewer)
            self.reviewers = ','.join(rset)

    @classmethod
    def add(cls, env, pr):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
            INSERT INTO pullrequests
                        (status, author, reviewers, opened, modified, ticket, comment, wikilink)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (pr.status, pr.author, pr.reviewers, to_utimestamp(pr.opened), to_utimestamp(pr.modified), pr.ticket, pr.comment, pr.wikilink))
            pr.id = db.get_last_id(cursor, 'pullrequests')

    @classmethod
    def delete_by_ids(cls, env, ids):
        ids_sql = ','.join(["'%s'" % id for id in ids])
        with env.db_transaction as db:
            db("""
                DELETE FROM pullrequests
                WHERE id in (%s)
            """ % ids_sql)

    @classmethod
    def update_status_and_reviewers(cls, env, pr):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                UPDATE pullrequests
                SET status=%s, reviewers=%s, modified=%s
                WHERE id=%s
            """, (pr.status, pr.reviewers, to_utimestamp(datetime.now(utc)), pr.id))

    @classmethod
    def select_by_id(cls, env, id):
        rows = env.db_query("""
                SELECT status, author, reviewers, opened, modified, ticket, comment, wikilink
                FROM pullrequests
                WHERE id=%s
                """, (id,))
        if not rows:
            return None
        status, author, reviewers, opened, modified, ticket, comment, wikilink = rows[0]
        return PullRequest(id, status, author, reviewers, from_utimestamp(opened), from_utimestamp(modified), ticket, comment, wikilink)

    @classmethod
    def select(cls, env, **kwargs):
        with env.db_query as db:
            conditions = []
            args = []
            for name, value in sorted(kwargs.iteritems()):
                if value:
                    op = '='
                    if value.startswith('!'):
                        op = '!='
                        value = value[1:]
                    conditions.append(db.quote(name) + op + '%s')
                    args.append(value)
            query = 'SELECT id, status, author, reviewers, opened, modified, ticket, comment, wikilink FROM pullrequests'
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            query += ' ORDER BY id DESC'
            cursor = db.cursor()
            cursor.execute(query, args)
            return [PullRequest(id, status, author, reviewers, from_utimestamp(opened), from_utimestamp(modified), ticket, comment, wikilink)
                    for id, status, author, reviewers, opened, modified, ticket, comment, wikilink in cursor]

    @classmethod
    def select_all_paginated(cls, env, page, max_per_page):
        rows = env.db_query("""
                SELECT id, status, author, reviewers, opened, modified, ticket, comment, wikilink
                FROM pullrequests
                ORDER BY id DESC
                LIMIT %s OFFSET %s
                """, (max_per_page, max_per_page * (page - 1)))
        return [PullRequest(id, status, author, reviewers, from_utimestamp(opened), from_utimestamp(modified), ticket, comment, wikilink)
                for id, status, author, reviewers, opened, modified, ticket, comment, wikilink in rows]

    @classmethod
    def count_all(cls, env):
        with env.db_query as db:
            return db("""
                    SELECT COUNT(*)
                    FROM pullrequests
                    """)[0][0]
