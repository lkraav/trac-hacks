# -*- coding: utf-8 -*-
from time import time
from trac.resource import ResourceNotFound
from trac.util.text import _
from trac.util import format_date
__author__ = 'Cinc'


class Reviewer(object):
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
            cursor.execute("""INSERT INTO Reviewers (IDReview, Reviewer, Status, Vote)
                              VALUES (%s, %s, %s, %s)
                           """, (self.review_id, self.reviewer, self.status, self.vote))

    @classmethod
    def select_by_review_id(cls, env, review_id, rev_name=None):
        db = env.get_read_db()
        cursor = db.cursor()
        # TODO: change query when database schema is adjusted
        if rev_name:
            sql = "SELECT IDReview, Reviewer, Status, Vote FROM Reviewers WHERE IDReview = %s " \
                  "AND Reviewer = %s"
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
            sql = "SELECT IDReview, Reviewer, Status, Vote FROM Reviewers WHERE IDReview = %s"
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
                SELECT IDReview, Author, Status, DateCreate, Name, Notes FROM CodeReviews WHERE IDReview=%s
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
            cursor.execute("""INSERT INTO CodeReviews (Author, Status, DateCreate, Name, Notes)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (self.author, self.status, self.raw_date, self.name, self.notes))
            self.review_id = db.get_last_id(cursor, 'CodeReviews', 'IDReview')

    def update(self):
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            self.env.log.debug("Updating review '%s'" % self.review_id)
            cursor.execute("""UPDATE CodeReviews
                            SET Author=%s, Status=%s, DateCreate=%s, Name=%s, Notes=%s
                            WHERE IDReview=%s
                            """, (self.author, self.status, self.raw_date, self.name, self.notes, self.review_id))

    @classmethod
    def select(cls, env):
        db = env.get_read_db()
        cursor = db.cursor()
        # TODO: change query when database schema is adjusted
        cursor.execute("SELECT IDReview, Author, Status, DateCreate, Name, Notes FROM CodeReviews "
                       "ORDER BY DateCreate")
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
        cursor.execute("SELECT cr.IDReview, cr.Author, cr.Status, cr.DateCreate, cr.Name, cr.Notes FROM "
                       "CodeReviews AS cr JOIN Reviewers AS r ON cr.IDReview = r.IDReview "
                       "WHERE r.Reviewer=%s"
                       "ORDER BY DateCreate", (reviewer,))
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
                SELECT IDFile, IDReview, Path, LineStart, LineEnd, Version FROM ReviewFiles WHERE IDFile=%s
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
            cursor.execute("""INSERT INTO ReviewFiles (IDReview, Path, LineStart,
                            LineEnd, Version)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (self.review_id, self.path, self.start, self.end, self.version))

    @classmethod
    def select_by_review(cls, env, review_id):
        db = env.get_read_db()
        cursor = db.cursor()
        # TODO: change query when database schema is adjusted
        cursor.execute("SELECT f.IDFile, f.IDReview, f.Path, f.LineStart, f.LineEnd, f.version FROM "
                       "ReviewFiles AS f WHERE f.IDReview=%s"
                       "ORDER BY f.Path", (review_id,))
        files = []
        for row in cursor:
            rev_file = cls(env)
            rev_file._init_from_row(row)
            files.append(rev_file)
        return files