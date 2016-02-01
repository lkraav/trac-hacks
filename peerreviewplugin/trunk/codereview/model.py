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
    def __init__(self, env, name=None):  # TODO: name or review_id here?
        self.env = env
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

    @classmethod
    def select_by_review_id(cls, env, review_id, rev_name=None):
        db = env.get_read_db()
        cursor = db.cursor()
        # TODO: change query when database schema is adjusted
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
            # TODO: change query when database schema is adjusted
            cursor.execute("""
                SELECT review_id, owner, status, created, name, notes FROM peer_review WHERE review_id=%s
                """, (review_id,))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_('Review %(name)s does not exist.',
                                         name=review_id))
            self._init_from_row(row)
        else:
            self._init_from_row((None,)*6)
            self.raw_date = int(time())

    def _init_from_row(self, row):
        rev_id, author, status, creation_date, name, notes = row
        self.name = self._old_name = name
        self.review_id = rev_id
        self.author = author
        self.status = status
        self.raw_date = creation_date
        self.creation_date = format_date(creation_date)
        self.notes = notes or ''

    exists = property(lambda self: self._old_name is not None)

    def insert(self):
        if not self.raw_date:
            self.raw_date = int(time())
        @self.env.with_transaction()
        def do_insert(db):
            cursor = db.cursor()
            self.env.log.debug("Creating new review '%s'" % self.review_id)
            cursor.execute("""INSERT INTO peer_review (owner, status, created, name, notes)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (self.author, self.status, self.raw_date, self.name, self.notes))
            self.review_id = db.get_last_id(cursor, 'peer_review', 'review_id')

    def update(self):
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            self.env.log.debug("Updating review '%s'" % self.review_id)
            cursor.execute("""UPDATE peer_review
                            SET owner=%s, status=%s, created=%s, name=%s, notes=%s
                            WHERE review_id=%s
                            """, (self.author, self.status, self.raw_date, self.name, self.notes, self.review_id))

    @classmethod
    def select(cls, env):
        db = env.get_read_db()
        cursor = db.cursor()
        # TODO: change query when database schema is adjusted
        cursor.execute("SELECT review_id, owner, status, created, name, notes FROM peer_review "
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
        # TODO: change query when database schema is adjusted
        cursor.execute("SELECT cr.review_id, cr.owner, cr.status, cr.created, cr.name, cr.notes FROM "
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
            # TODO: change query when database schema is adjusted
            cursor.execute("""
                SELECT file_id, review_id, path, line_start, line_end, revision FROM peer_review_file WHERE file_id=%s
                """, (file_id,))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_('File %(name)s does not exist.',
                                         name=file_id))
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

    @classmethod
    def select_by_review(cls, env, review_id):
        db = env.get_read_db()
        cursor = db.cursor()
        # TODO: change query when database schema is adjusted
        cursor.execute("SELECT f.file_id, f.review_id, f.path, f.line_start, f.line_end, f.revision FROM "
                       "peer_review_file AS f WHERE f.review_id=%s"
                       "ORDER BY f.path", (review_id,))
        files = []
        for row in cursor:
            rev_file = cls(env)
            rev_file._init_from_row(row)
            files.append(rev_file)
        return files