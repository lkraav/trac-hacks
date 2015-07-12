# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Armin Ronacher <armin.ronacher@active-4.com>
# Copyright (C) 2008 Michael Renzmann <mrenzmann@otaku42.de>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

"""
TracPastePlugin: entity model for pastes, including:
 * CRUD (create, read, update, delete)
 * various helpers to retrieve pastes
"""

from datetime import datetime

from trac.core import TracError
from trac.resource import Resource, ResourceNotFound
from trac.util.datefmt import to_timestamp, utc
from trac.util.translation import _


def get_pastes(env, number=None, offset=None, from_dt=None, to_dt=None):
    """Returns a list of pastes as dicts without data.

    One or more filters need to be set:
     * number - maximum number of items that may be returned
     * offset - number of items to skip in returned results
     * from_dt - pasted on or after the given time (datetime object)
     * to_dt - pasted before or on the given time (datetime object)

    Returns dictionary of the form:
        (id, title, author, time)
    where time is in UTC.

    To get the paste data, use id to instantiate a Paste object."""

    sql = "SELECT id, title, author, time FROM pastes"
    order_clause = " ORDER BY id DESC"
    limit_clause = ""
    if number:
        limit_clause += " LIMIT %s" % number
    if offset:
        limit_clause += " OFFSET %s" % offset

    where_clause = ""
    where_values = None
    args = [from_dt and ("time>%s", to_timestamp(from_dt)) or None,
            to_dt and ("time<%s", to_timestamp(to_dt)) or None]
    args = [arg for arg in args if arg]  # Get rid of the None values
    if args:
        where_clause = " WHERE " + " AND ".join([arg[0] for arg in args])
        where_values = tuple([arg[1] for arg in args])

    sql += where_clause + order_clause + limit_clause

    result = []
    for row in env.db_query(sql, where_values):
        result.append({
            'id': row[0],
            'title': row[1],
            'author': row[2],
            'time': datetime.fromtimestamp(row[3], utc)
        })
    return result


class Paste(object):
    """
    A class representing a paste.
    """

    id_is_valid = staticmethod(lambda num: 0 < int(num) <= (1L << 31))

    def __init__(self, env, id=None, title=u'', author=u'',
                 mimetype='text/plain', data=u'', time=None):
        self.env = env
        self.id = None
        self.title = title
        self.author = author
        self.mimetype = mimetype
        self.data = data
        self.time = time
        self.resource = Resource('pastebin', self.id)

        if id is not None and self.id_is_valid(id):
            for row in self.env.db_query("""
                    SELECT title, author, mimetype, data, time
                    FROM pastes WHERE id=%s
                    """, (id,)):
                self.id = id
                self.title, self.author, self.mimetype, self.data, time = row
                self.time = datetime.fromtimestamp(time, utc)
                break
            else:
                raise ResourceNotFound(
                    _("Paste %(id)s does not exist.", id=id),
                    _("Invalid Paste Number"))

    def __repr__(self):
        return '<%s %r: %s>' % (
            self.__class__.__name__,
            self.title,
            self.id
        )

    def __nonzero__(self):
        return self.id is not None

    exists = property(__nonzero__)

    def delete(self):
        """Delete a paste."""
        if self.id is None:
            raise TracError(_("Cannot delete non-existent paste"))
        self.env.db_transaction('DELETE FROM pastes WHERE id=%s', (self.id,))

    def save(self):
        """Save changes or add a new paste."""
        if self.time is None:
            self.time = datetime.now(utc)

        with self.env.db_transaction as db:
            if self.id is None:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO pastes (title, author, mimetype, data, time)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (self.title, self.author, self.mimetype,
                          self.data, to_timestamp(self.time)))
                self.id = db.get_last_id(cursor, 'pastes')
            else:
                db("""UPDATE pastes
                   SET title=%s, author=%s, mimetype=%s, data=%s, time=%s
                   WHERE id=%s
                   """, (self.title, self.author, self.mimetype, self.data,
                         to_timestamp(self.time), self.id))

    def render(self, req):
        """Render the data."""
        from trac.mimeview.api import Mimeview
        from trac.web.chrome import web_context
        context = web_context(req)
        mimeview = Mimeview(self.env)
        return mimeview.render(context, self.mimetype, self.data,
                               annotations=['lineno'])
