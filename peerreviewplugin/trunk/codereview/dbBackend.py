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
        query = "SELECT review_id, owner, status, created, name, notes FROM peer_review " \
                "WHERE created >= '%s' AND created <= '%s' ORDER BY created" % (date_from, date_to)
        return self.execCodeReviewQuery(query, False)

    #Returns an array of code reviews which have a namwe like any of the
    #names given in the 'name' string
    def searchCodeReviewsByName(self, name):
        queryPart = self.createORLoop(name, "Name")
        if len(queryPart) == 0:
            query = "SELECT review_id, owner, status, created, name, notes FROM peer_review"
        else:
            query = "SELECT review_id, owner, status, created, name, notes FROM peer_review WHERE %s" % (queryPart)
        return self.execCodeReviewQuery(query, True)

    #Returns an array of code reviews that match the values in the given
    #code review structure.  The 'name' part is treated as a keyword list
    def searchCodeReviews(self, crStruct):
        query = "SELECT review_id, owner, status, created, name, notes FROM peer_review WHERE "
        queryPart = self.createORLoop(crStruct.Name, "name")
        if len(queryPart) != 0:
            query = query + "(%s) AND " % (queryPart)
        query = query + "owner LIKE '%s%s%s' AND status LIKE '%s%s%s' AND created >= '%s'" % \
                        ('%', crStruct.Author, '%', '%', crStruct.Status, '%', crStruct.DateCreate)
        return self.execCodeReviewQuery(query, False)

    #Returns the requested comment
    def getCommentByID(self, id):
        query = "SELECT comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created " \
                "FROM peer_review_comment WHERE comment_id = '%s'" % (id)
        return self.execReviewCommentQuery(query, True)

    #Returns an array of comments for the given file
    def getCommentsByFileID(self, id):
        query = "SELECT comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created " \
                "FROM peer_review_comment WHERE file_id = '%s' ORDER BY created" % (id)
        return self.execReviewCommentQuery(query, False)

    #Returns all the comments for the given file on the given line
    def getCommentsByFileIDAndLine(self, id, line):
        query = "SELECT comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created " \
                "FROM peer_review_comment WHERE file_id = '%s' AND line_num = '%s' ORDER BY created" % (id, line)
        return self.execReviewCommentQuery(query, False)

    #Returns a dictionary where the key is the line number and the value is the number of comments on that line
    #for the given file id.
    def getCommentDictForFile(self, id):
        query = "SELECT line_num, Count(comment_id) FROM peer_review_comment WHERE file_id = '%s' GROUP BY line_num" % (id)
        cursor = self.db.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        d = {}
        if not rows:
            return d
        for row in rows:
            d[row[0]] = row[1]
        return d

    #Returns all the possible users who can review a code review
    def getPossibleUsers(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT DISTINCT p1.username as username FROM permission p1 left join permission p2 on p1.action = p2.username WHERE p1.action = 'CODE_REVIEW_DEV' OR p2.action = 'CODE_REVIEW_DEV' OR p1.action = 'CODE_REVIEW_MGR' OR p2.action = 'CODE_REVIEW_MGR'")
        rows = cursor.fetchall()
        if not rows:
            return []

        users = []
        for row in rows:
            users.append(row[0])
        return users

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
