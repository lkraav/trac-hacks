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

tables = [
    Table('peer_review', key='review_id')[
        Column('review_id', auto_increment=True, type='int'),
        Column('owner'),
        Column('status'),
        Column('created', type='int'),
        Column('name'),
        Column('notes'),
        Column('parent_id', type='int'),
        Column('keywords'),
    ],
    Table('peer_reviewer', key=('review_id', 'reviewer'))[
        Column('review_id', type='int'),
        Column('reviewer'),
        Column('status', type='int'),
        Column('vote', type='int'),
    ],
    Table('peer_review_file', key='file_id')[
        Column('file_id', auto_increment=True, type='int'),
        Column('review_id', type='int'),
        Column('path'),
        Column('line_start', type='int'),
        Column('line_end', type='int'),
        Column('repo'),
        Column('revision'),
    ],
    Table('peer_review_comment', key='comment_id')[
        Column('comment_id', auto_increment=True, type='int'),
        Column('file_id', type='int'),
        Column('parent_id', type='int'),
        Column('line_num', type='int'),
        Column('author'),
        Column('comment'),
        Column('attachment_path'),
        Column('created', type='int'),
    ],
]

def do_upgrade(env, ver, cursor):
    """Add tables with new names."""

    db_connector, _ = DatabaseManager(env).get_connector()
    for tbl in tables:
        for stmt in db_connector.to_sql(tbl):
            cursor.execute(stmt)

    cursor.execute("""INSERT INTO peer_review(review_id,owner,status, created, name, notes)
    SELECT IDReview, Author, Status, DateCreate, Name, Notes FROM CodeReviews""")
    cursor.execute("""INSERT INTO peer_reviewer(review_id,reviewer,status, vote)
    SELECT IDReview, Reviewer, Status, Vote FROM Reviewers""")
    cursor.execute("""INSERT INTO peer_review_file(file_id,review_id,path,line_start,line_end, revision)
    SELECT IDFile, IDReview, Path, LineStart, LineEnd, Version FROM ReviewFiles""")
    cursor.execute("""INSERT INTO peer_review_comment(comment_id,file_id,parent_id,line_num,author,comment,
    attachment_path, created)
    SELECT IDComment, IDFile, IDParent, LineNum, Author, Text, AttachmentPath, DateCreate FROM ReviewComments""")

    cursor.execute("SELECT value FROM system WHERE name = %s", ('CodeReviewVoteThreshold',))
    row = cursor.fetchone()
    env.config.set('peer-review', 'vote_threshold', row[0])
    env.config.save()

    cursor.execute("DELETE FROM system WHERE name = %s", ('CodeReviewVoteThreshold',))
    cursor.execute("DELETE FROM system WHERE name = %s", ('codereview_version',))
    cursor.execute("DROP TABLE CodeReviews")
    cursor.execute("DROP TABLE Reviewers")
    cursor.execute("DROP TABLE ReviewFiles")
    cursor.execute("DROP TABLE ReviewComments")
