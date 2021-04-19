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
from trac.db import Table, Column, DatabaseManager

#The tables for the Code Review Plugin database version 1

tables = [
    Table('CodeReviews', key='IDReview')[
        Column('IDReview', auto_increment=True, type='int'),
        Column('Author'),
        Column('Status'),
        Column('DateCreate', type='int'),
        Column('Name'),
        Column('Notes'),
    ],
    Table('Reviewers', key=('IDReview', 'Reviewer'))[
        Column('IDReview', type='int'),
        Column('Reviewer'),
        Column('Status', type='int'),
        Column('Vote', type='int'),
    ],
    Table('ReviewFiles', key='IDFile')[
        Column('IDFile', auto_increment=True, type='int'),
        Column('IDReview', type='int'),
        Column('Path'),
        Column('LineStart', type='int'),
        Column('LineEnd', type='int'),
        Column('Version', type='int'),
    ],
    Table('ReviewComments', key='IDComment')[
        Column('IDComment', auto_increment=True, type='int'),
        Column('IDFile', type='int'),
        Column('IDParent', type='int'),
        Column('LineNum', type='int'),
        Column('Author'),
        Column('Text'),
        Column('AttachmentPath'),
        Column('DateCreate', type='int'),
    ],
]

def do_upgrade(env, ver, cursor):
    """Add tables."""
    db_connector, _ = DatabaseManager(env).get_connector()
    for tbl in tables:
        for stmt in db_connector.to_sql(tbl):
            cursor.execute(stmt)

    cursor.execute("INSERT INTO system VALUES (%s, %s)", ('CodeReviewVoteThreshold', 0))
