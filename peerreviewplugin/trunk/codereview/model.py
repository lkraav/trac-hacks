# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#
from time import time
from trac.resource import ResourceNotFound
from trac.util.text import _
from trac.util import format_date
__author__ = 'Cinc'

def get_threshold(env):
    return env.config.getint('peer-review', 'vote_threshold', 100)

def set_threshold(env, val):
    env.config.set('peer-review', 'vote_threshold', val)
    env.config.save()


def get_users(env):
    db = env.get_read_db()
    cursor = db.cursor()
    cursor.execute("""SELECT DISTINCT p1.username FROM permission AS p1
                      LEFT JOIN permission AS p2 ON p1.action = p2.username
                      WHERE p2.action = 'CODE_REVIEW_DEV'
                      OR p1.action = 'CODE_REVIEW_DEV'
                      OR p1.action = 'TRAC_ADMIN'
                      """)
    users = []
    for row in cursor:
        users.append(row[0])
    if users:
        # Filter groups from the results. We should probably do this using the group provider component
        cursor.execute("""Select DISTINCT p3.action FROM permission AS p3
                          JOIN permission p4 ON p3.action = p4.username""")
        groups = []
        for row in cursor:
            groups.append(row[0])
        groups.append('authenticated')
        users = list(set(users)-set(groups))
    return sorted(users)


class Vote(object):

    def __init__(self, env, review_id):
        if not review_id:
            raise ValueError("No review id given during creation of Vote object.")
        self._votes = {'yes': 0, 'no': 0, 'pending': 0}
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT vote FROM peer_reviewer WHERE review_id = %s", (review_id,))
        for row in cursor:
            if row[0] == -1:
                self._votes['pending'] += 1
            elif row[0] == 1:
                self._votes['yes'] += 1
            elif row[0] == 0:
                self._votes['no'] += 1

    @property
    def yes(self):
        return self._votes['yes']

    @property
    def no(self):
        return self._votes['no']

    @property
    def pending(self):
        return self._votes['pending']

    @property
    def votes(self):
        return self._votes


class Reviewer(object):
    """Model for a reviewer working on a code review."""
    def __init__(self, env, review_id=None, name=None):
        self.env = env

        if name and review_id:
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT review_id, reviewer, status, vote FROM peer_reviewer WHERE reviewer=%s
                AND review_id=%s
                """, (name, review_id))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_("Reviewer '%(name)s' does not exist for review '#%(review)s'.",
                                         name=name, review=review_id), _('Peer Review Error'))
            self._init_from_row(row)
        else:
            self._init_from_row((None,)*4)

    def _init_from_row(self, row):
        rev_id, reviewer, status, vote = row
        self.review_id = rev_id
        self.reviewer = reviewer
        self.status = status
        self.vote = vote

    def insert(self):
        if not self.review_id:
            raise ValueError("No review id given during creation of Reviewer entry.")
        @self.env.with_transaction()
        def do_insert(db):
            cursor = db.cursor()
            self.env.log.debug("Creating new reviewer entry for '%s'" % self.review_id)
            cursor.execute("""INSERT INTO peer_reviewer (review_id, reviewer, status, vote)
                              VALUES (%s, %s, %s, %s)
                           """, (self.review_id, self.reviewer, self.status, self.vote))

    def update(self):
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            self.env.log.debug("Updating reviewer %s for review '%s'" % (self.reviewer, self.review_id))
            cursor.execute("""UPDATE peer_reviewer
                        SET review_id=%s, reviewer=%s, status=%s, vote=%s
                        WHERE reviewer=%s AND review_id=%s
                        """, (self.review_id, self.reviewer, self.status, self.vote, self.reviewer, self.review_id))

    def delete(self):
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            cursor.execute("""DELETE FROM peer_reviewer
                        WHERE review_id=%s AND reviewer=%s
                        """, (self.review_id, self.reviewer))

    @classmethod
    def select_by_review_id(cls, env, review_id, rev_name=None):
        db = env.get_read_db()
        cursor = db.cursor()
        if rev_name:
            sql = "SELECT review_id, reviewer, status, vote FROM peer_reviewer WHERE review_id = %s " \
                  "AND reviewer = %s"
            data = (review_id, rev_name)
            cursor.execute(sql, data)
            row = cursor.fetchone()
            if row:
                reviewer = cls(env)
                reviewer._init_from_row(row)
            else:
                reviewer = None
            return reviewer
        else:
            sql = "SELECT review_id, reviewer, status, vote FROM peer_reviewer WHERE review_id = %s"
            data = (review_id,)
        cursor.execute(sql, data)
        reviewers = []
        for row in cursor:
            reviewer = cls(env)
            reviewer._init_from_row(row)
            reviewers.append(reviewer)
        return reviewers


class Review(object):
    def __init__(self, env, review_id=None):
        self.env = env

        if review_id:
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT review_id, owner, status, created, name, notes, parent_id FROM peer_review WHERE review_id=%s
                """, (review_id,))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_('Review %(name)s does not exist.',
                                         name=review_id), _('Peer Review Error'))
            self._init_from_row(row)
        else:
            self._init_from_row((None,)*7)
            self.raw_date = int(time())
            self.parent_id = 0

    def _init_from_row(self, row):
        rev_id, author, status, creation_date, name, notes, parent_id = row
        self.name = self._old_name = name
        self.review_id = rev_id
        self.author = author
        self.status = status
        self.raw_date = creation_date
        self.creation_date = format_date(creation_date)
        self.notes = notes or ''
        self.parent_id = parent_id or 0

    exists = property(lambda self: self._old_name is not None)

    def insert(self):
        if not self.raw_date:
            self.raw_date = int(time())
        @self.env.with_transaction()
        def do_insert(db):
            cursor = db.cursor()
            self.env.log.debug("Creating new review '%s'" % self.review_id)
            cursor.execute("""INSERT INTO peer_review (owner, status, created, name, notes, parent_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """, (self.author, self.status, self.raw_date, self.name, self.notes, self.parent_id))
            self.review_id = db.get_last_id(cursor, 'peer_review', 'review_id')

    def update(self):
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            self.env.log.debug("Updating review '%s'" % self.review_id)
            cursor.execute("""UPDATE peer_review
                            SET owner=%s, status=%s, created=%s, name=%s, notes=%s, parent_id=%s
                            WHERE review_id=%s
                            """, (self.author, self.status, self.raw_date, self.name, self.notes, self.parent_id,
                                  self.review_id))

    @classmethod
    def select(cls, env):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT review_id, owner, status, created, name, notes, parent_id FROM peer_review "
                       "ORDER BY created")
        reviews = []
        for row in cursor:
            review = cls(env)
            review._init_from_row(row)
            reviews.append(review)
        return reviews

    @classmethod
    def select_by_reviewer(cls, env, reviewer):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT cr.review_id, cr.owner, cr.status, cr.created, cr.name, cr.notes, cr.parent_id  FROM "
                       "peer_review AS cr JOIN peer_reviewer AS r ON cr.review_id = r.review_id "
                       "WHERE r.reviewer=%s"
                       "ORDER BY cr.created", (reviewer,))
        reviews = []
        for row in cursor:
            review = cls(env)
            review._init_from_row(row)
            reviews.append(review)
        return reviews


class ReviewFile(object):
    def __init__(self, env, file_id=None):
        self.env = env

        if file_id:
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT file_id, review_id, path, line_start, line_end, revision FROM peer_review_file WHERE file_id=%s
                """, (file_id,))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_('File %(name)s does not exist.',
                                         name=file_id), _('Peer Review Error'))
            self._init_from_row(row)
        else:
            self._init_from_row((None,)*6)

    def _init_from_row(self, row):
        file_id, rev_id, fpath, start, end, ver = row
        self.file_id = file_id
        self.review_id = rev_id
        self.path = fpath
        self.start = start
        self.end = end
        self.version = ver

    def insert(self):
        @self.env.with_transaction()
        def do_insert(db):
            cursor = db.cursor()
            self.env.log.debug("Creating new file for review '%s'" % self.review_id)
            cursor.execute("""INSERT INTO peer_review_file (review_id, path, line_start,
                            line_end, revision)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (self.review_id, self.path, self.start, self.end, self.version))

    def delete(self):
        @self.env.with_transaction()
        def do_delete(db):
            cursor = db.cursor()
            self.env.log.debug("Deleting file '%s' for review '%s'" % (self.file_id, self.review_id))
            cursor.execute("""DELETE FROM peer_review_file  WHERE file_id=%s""",
                           (self.file_id,))

    @classmethod
    def select_by_review(cls, env, review_id):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT f.file_id, f.review_id, f.path, f.line_start, f.line_end, f.revision FROM "
                       "peer_review_file AS f WHERE f.review_id=%s"
                       "ORDER BY f.path", (review_id,))
        files = []
        for row in cursor:
            rev_file = cls(env)
            rev_file._init_from_row(row)
            files.append(rev_file)
        return files


class Comment(object):

    def __init__(self, env, file_id=None):
        self.env = env
        self._init_from_row((None,)*8)

    def _init_from_row(self, row):
        comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created = row
        self.comment_id = comment_id
        self.file_id = file_id
        self.parent_id = parent_id
        self.line_num = line_num
        self.author = author
        self.comment = comment
        self.attachment_path = attachment_path
        self.created = created

    def insert(self):
        @self.env.with_transaction()
        def do_insert(db):
            created = self.created
            if not created:
                created = int(time())
            cursor = db.cursor()
            self.env.log.debug("Creating new comment for file '%s'" % self.file_id)
            cursor.execute("""INSERT INTO peer_review_comment (file_id, parent_id, line_num,
                            author, comment, attachment_path, created)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (self.file_id, self.parent_id, self.line_num, self.author, self.comment,
                                  self.attachment_path, created))

    @classmethod
    def select_by_file_id(cls, env, file_id):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created FROM "
                       "peer_review_comment WHERE file_id=%s ORDER BY line_num", (file_id,))
        comments = []
        for row in cursor:
            c = cls(env)
            c._init_from_row(row)
            comments.append(c)
        return comments