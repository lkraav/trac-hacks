# -*- coding: utf-8 -*-

from trac.resource import ResourceNotFound
from trac.util.text import _
from trac.util import format_date
__author__ = 'Cinc'

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
            rev_id, author, status, creation_date, name, notes = row
            self.name = self._old_name = name
            self.review_id = rev_id
            self.author = author
            self.status = status
            self.creation_date = creation_date
            self.notes = notes or ''
        else:
            self.name = self._old_name = None
            self.review_id = None
            self.author = None
            self.status = None
            self.creation_date = None
            self.notes = None

    exists = property(lambda self: self._old_name is not None)

    @classmethod
    def select(cls, env):
        db = env.get_read_db()
        cursor = db.cursor()
        # TODO: change query when database schema is adjusted
        cursor.execute("SELECT IDReview, Author, Status, DateCreate, Name, Notes FROM CodeReviews")
        reviews = []
        for rev_id, author, status, creation_date, name, notes in cursor:
            review = cls(env)
            review.name = review._old_name = name
            review.review_id = rev_id
            review.author = author
            review.status = status
            review.raw_date = creation_date
            review.creation_date = format_date(creation_date)
            review.notes = notes or ''
            reviews.append(review)
        # TODO: should this be sorted in any way?
        return reviews
