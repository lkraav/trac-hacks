# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Radu Gasler <miezuit@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import datetime

from trac.util.datefmt import to_utimestamp, utc


def wiki_text_replace(env, oldtext, newtext, wikipages, user):
    """Replace oldtext with newtext in all wiki pages in wikipages list
    using env as the environment. Wikipages should be a list of wiki
    pages with optional * and ? wildcards (unix file globbing syntax).
    """
    ip = '127.0.0.1'
    with env.db_transaction as db:
        for wikipage in wikipages:
            for row in db("""
                    SELECT w1.version, w1.name, w1.text, w1.readonly
                    FROM wiki w1, (SELECT name, MAX(version) AS max_version
                                   FROM wiki GROUP BY name) w2
                    WHERE w1.version = w2.max_version
                     AND w1.name = w2.name
                     AND w1.name %s AND w1.text %s
                    """ % (db.like(), db.like()),
                    (wikipage, '%' + db.like_escape(oldtext) + '%')):
                env.log.debug("Found a page with searched text in it: %s "
                              "(v%s)", row[1], row[0])
                newcontent = row[2].replace(oldtext, newtext)

                # name, version, now, user, ip, newcontent, replace comment
                new_wiki_page = (row[1], row[0] + 1,
                                 to_utimestamp(datetime.datetime.now(utc)),
                                 user, ip, newcontent,
                                 'Replaced "%s" with "%s".'
                                 % (oldtext, newtext),
                                 row[3])

                # Create a new page with the needed comment
                db("""
                    INSERT INTO wiki (name,version,time,author,ipnr,
                                      text,comment,readonly)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """, new_wiki_page)
