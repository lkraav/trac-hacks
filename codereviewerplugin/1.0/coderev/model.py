# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import datetime

from trac.resource import ResourceNotFound
from trac.util.datefmt import to_utimestamp, utc
from trac.util.translation import _


class CodeReview(object):
    """A review for a single changeset."""

    # default status choices - configurable but must always be exactly three
    STATUSES = ['FAILED', 'PENDING', 'PASSED']
    DEFAULT_STATUS = STATUSES[1]
    NOT_PASSED = "(not %s)" % STATUSES[2]

    def __init__(self, env, repo, changeset):
        self.env = env
        self.repo = repo or ''
        self.changeset = str(changeset)
        self.status = self.decode(self.DEFAULT_STATUS)
        self.reviewer, self.when, self.summary = '', 0, ''
        for status, reviewer, time, summary in self.env.db_query("""
                SELECT status, reviewer, time, summary FROM codereviewer
                WHERE repo=%s AND changeset=%s
                ORDER BY time DESC LIMIT 1
                """, (self.repo, self.changeset)):
            self.status = self.decode(status)
            self.reviewer = reviewer
            self.when = time
            self.summary = summary
            break
        else:
            for status, in self.env.db_query("""
                    SELECT status FROM codereviewer
                    WHERE repo=%s AND changeset=%s AND status IS NOT NULL
                    ORDER BY time DESC LIMIT 1
                    """, (self.repo, self.changeset)):
                self.status = self.decode(status)

        self.tickets = []
        self.changeset_when = 0
        for ticket, when in self.env.db_query("""
                SELECT ticket, time
                FROM codereviewer_map
                WHERE repo=%s AND changeset=%s
                """, (self.repo, self.changeset)):
            if ticket:
                self.tickets.append(ticket)
            self.changeset_when = when

    def __getitem__(self, name):
        return getattr(self, name)

    @property
    def statuses(self):
        return self.env.config.getlist('codereviewer', 'status_choices')

    def save(self, reviewer, status, summary):
        status = self.encode(status)
        when = to_utimestamp(datetime.datetime.now(utc))
        if status == self.status:
            status = None  # Status saved only if changed.
        if not (status or summary):
            return False  # Nothing worthwhile to save.
        self.env.db_transaction("""
            INSERT INTO codereviewer
             (repo,changeset,status,reviewer,summary,time)
            VALUES (%s,%s,%s,%s,%s,%s)
            """, (self.repo, self.changeset, status, reviewer, summary, when))
        if status:
            self.status = status
        self.summary = summary
        self.when = when
        return True

    def decode(self, status):
        if status:
            try:
                # convert from canonical to configured
                i = self.STATUSES.index(status)
                status = self.statuses[i]
            except Exception:
                pass
        return status

    def encode(self, status):
        if status:
            try:
                # convert from configured to canonical
                i = self.statuses.index(status)
                status = self.STATUSES[i]
            except Exception:
                pass
        return status

    @classmethod
    def select(cls, env, repo, changeset):
        """Returns all review for the given changeset."""
        reviews = []
        changeset = str(changeset)
        for status, reviewer, summary, when in env.db_query("""
                SELECT status, reviewer, summary, time FROM codereviewer
                WHERE repo=%s AND changeset=%s ORDER BY time ASC
                """, (repo, changeset)):
            review = CodeReview(env, repo, changeset)
            review.status = review.decode(status) or ''
            review.reviewer = reviewer
            review.summary = summary
            review.when = when
            reviews.append(review)
        return reviews


def get_reviews_for_ticket(env, ticket_id):
    """Returns all reviews for the specified ticket, in changeset order."""
    reviews = []
    for repo, changeset in env.db_query("""
            SELECT repo, changeset FROM codereviewer_map
            WHERE ticket=%s ORDER BY time ASC
            """, (ticket_id,)):
        reviews.append(CodeReview(env, repo, changeset))
    return reviews
