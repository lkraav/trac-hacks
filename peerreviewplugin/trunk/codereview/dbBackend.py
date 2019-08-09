#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

import string
from ReviewCommentStruct import *


class dbBackend(object):
    db = None

    def __init__(self, tdb):
        self.db = tdb

    #Returns the requested comment
    def getCommentByID(self, id):
        query = "SELECT comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created " \
                "FROM peerreviewcomment WHERE comment_id = '%s'" % (id)
        return self.execReviewCommentQuery(query, True)

    #Returns all the comments for the given file on the given line
    def getCommentsByFileIDAndLine(self, id, line):
        query = "SELECT comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created " \
                "FROM peerreviewcomment WHERE file_id = '%s' AND line_num = '%s' ORDER BY created" % (id, line)
        return self.execReviewCommentQuery(query, False)

    #A generic method for executing queries that return Comment structures
    #query: the query to execute
    #single: true if this query will always return only one result, false otherwise
    def execReviewCommentQuery(self, query, single):
        cursor = self.db.cursor()
        cursor.execute(query)
        if single:
            row = cursor.fetchone()
            if not row:
                return None
            return ReviewCommentStruct(row)

        rows = cursor.fetchall()
        if not rows:
            return {}

        comments = {}
        for row in rows:
            comment = ReviewCommentStruct(row)
            if comment.IDComment != "-1":
                comments[comment.IDComment] = comment

        for key in comments.keys():
            comment = comments[key]
            if comment.IDParent != "-1" and comment.IDParent in comments and comment.IDParent != comment.IDComment:
                comments[comment.IDParent].Children[comment.IDComment] = comment

        return comments
