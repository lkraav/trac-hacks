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

from CodeReviewStruct import *
from ReviewCommentStruct import *


class dbBackend(object):
    db = None

    def __init__(self, tdb):
        self.db = tdb

    #Creates a set of SQL ORs from a string of keywords
    def createORLoop(self, keyword, colName):
        array = keyword.split()
        newStr = ""
        for str in array:
            if len(newStr) != 0:
                newStr = newStr + "OR "
            newStr = newStr + colName + " LIKE '%s%s%s' " % ('%', str, '%')
        return newStr

    def getCodeReviewsInPeriod(self, date_from, date_to):
        query = "SELECT review_id, owner, status, created, name, notes FROM peerreview " \
                "WHERE created >= '%s' AND created <= '%s' ORDER BY created" % (date_from, date_to)
        return self.execCodeReviewQuery(query, False)

    #Returns an array of code reviews which have a namwe like any of the
    #names given in the 'name' string
    def searchCodeReviewsByName(self, name):
        queryPart = self.createORLoop(name, "Name")
        if len(queryPart) == 0:
            query = "SELECT review_id, owner, status, created, name, notes FROM peerreview"
        else:
            query = "SELECT review_id, owner, status, created, name, notes FROM peerreview WHERE %s" % (queryPart)
        return self.execCodeReviewQuery(query, True)

    #Returns an array of code reviews that match the values in the given
    #code review structure.  The 'name' part is treated as a keyword list
    def searchCodeReviews(self, crStruct):
        query = "SELECT review_id, owner, status, created, name, notes FROM peerreview WHERE "
        queryPart = self.createORLoop(crStruct.Name, "name")
        if len(queryPart) != 0:
            query = query + "(%s) AND " % (queryPart)
        query = query + "owner LIKE '%s%s%s' AND status LIKE '%s%s%s' AND created >= '%s'" % \
                        ('%', crStruct.Author, '%', '%', crStruct.Status, '%', crStruct.DateCreate)
        return self.execCodeReviewQuery(query, False)

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

    #A generic method for executing queries that return CodeReview structures
    #query: the query to execute
    #single: true if this query will always return only one result, false otherwise
    def execCodeReviewQuery(self, query, single):
        cursor = self.db.cursor()
        cursor.execute(query)
        if single:
            row = cursor.fetchone()
            if not row:
                return None
            return CodeReviewStruct(row)

        rows = cursor.fetchall()
        if not rows:
            return []

        codeReviews = []
        for row in rows:
            codeReviews.append(CodeReviewStruct(row))
        return codeReviews

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
