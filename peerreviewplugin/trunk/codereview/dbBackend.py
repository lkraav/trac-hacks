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
from ReviewerStruct import *
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
        query = "SELECT IDReview, Author, Status, DateCreate, Name, Notes FROM CodeReviews WHERE DateCreate >= '%s' AND DateCreate <= '%s' ORDER BY DateCreate" % (date_from, date_to)
        return self.execCodeReviewQuery(query, False)

    #Returns the number of votes of type 'type' for the given code review
    def getVotesByID(self, type, id):
        query = "SELECT Count(Reviewer) FROM Reviewers WHERE IDReview = '%s' AND Vote = '%s'" % (id, type)
        cursor = self.db.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        if not row:
            return 0
        return row[0]

    #Returns an array of code reviews which have a namwe like any of the
    #names given in the 'name' string
    def searchCodeReviewsByName(self, name):
        queryPart = self.createORLoop(name, "Name")
        if len(queryPart) == 0:
            query = "SELECT IDReview, Author, Status, DateCreate, Name, Notes FROM CodeReviews"
        else:
            query = "SELECT IDReview, Author, Status, DateCreate, Name, Notes FROM CodeReviews WHERE %s" % (queryPart)
        return self.execCodeReviewQuery(query, True)

    #Returns an array of code reviews that match the values in the given
    #code review structure.  The 'name' part is treated as a keyword list
    def searchCodeReviews(self, crStruct):
        query = "SELECT IDReview, Author, Status, DateCreate, Name, Notes FROM CodeReviews WHERE "
        queryPart = self.createORLoop(crStruct.Name, "Name")
        if len(queryPart) != 0:
            query = query + "(%s) AND " % (queryPart)
        query = query + "Author LIKE '%s%s%s' AND Status LIKE '%s%s%s' AND DateCreate >= '%s'" % ('%', crStruct.Author, '%', '%', crStruct.Status, '%', crStruct.DateCreate)
        return self.execCodeReviewQuery(query, False)

    #Returns an array of all the reviewers for a code review
    def getReviewers(self, id):
        query = "SELECT IDReview, Reviewer, Status, Vote FROM Reviewers WHERE IDReview = '%s'" % (id)
        return self.execReviewerQuery(query, False)

    #Returns a specific reviewer entry for the given code review and name
    def getReviewerEntry(self, id, name):
        query = "SELECT IDReview, Reviewer, Status, Vote FROM Reviewers WHERE IDReview = '%s' AND Reviewer = '%s'" % (id, name)
        return self.execReviewerQuery(query, True)

    #Returns the requested comment
    def getCommentByID(self, id):
        query = "SELECT IDComment, IDFile, IDParent, LineNum, Author, Text, AttachmentPath, DateCreate FROM ReviewComments WHERE IDComment = '%s'" % (id)
        return self.execReviewCommentQuery(query, True)

    #Returns an array of comments for the given file
    def getCommentsByFileID(self, id):
        query = "SELECT IDComment, IDFile, IDParent, LineNum, Author, Text, AttachmentPath, DateCreate FROM ReviewComments WHERE IDFile = '%s' ORDER BY DateCreate" % (id)
        return self.execReviewCommentQuery(query, False)

    #Returns all the comments for the given file on the given line
    def getCommentsByFileIDAndLine(self, id, line):
        query = "SELECT IDComment, IDFile, IDParent, LineNum, Author, Text, AttachmentPath, DateCreate FROM ReviewComments WHERE IDFile = '%s' AND LineNum = '%s' ORDER BY DateCreate" % (id, line)
        return self.execReviewCommentQuery(query, False)

    #Returns the current "Threshold" for code to be ready for inclusion
    def getThreshold(self):
        query = "SELECT value FROM system WHERE name = 'CodeReviewVoteThreshold'"
        cursor = self.db.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        if not row:
            return 0
        numVal = 0
        try:
            numVal = string.atoi(row[0])
        except:
            return 0
        return numVal

    #Sets the "Threshold" to the given value
    def setThreshold(self, val):
        query = "UPDATE system SET value = '%s' WHERE name = 'CodeReviewVoteThreshold'" % (val)
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()

    #Returns a dictionary where the key is the line number and the value is the number of comments on that line
    #for the given file id.
    def getCommentDictForFile(self, id):
        query = "SELECT LineNum, Count(IDComment) FROM ReviewComments WHERE IDFile = '%s' GROUP BY LineNum" % (id)
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

    #A generic method for executing queries that return Reviewer structures
    #query: the query to execute
    #single: true if this query will always return only one result, false otherwise
    def execReviewerQuery(self, query, single):
        cursor = self.db.cursor()
        cursor.execute(query)
        if single:
            row = cursor.fetchone()
            if not row:
                return None
            return ReviewerStruct(row)

        rows = cursor.fetchall()
        if not rows:
            return []

        reviewers = []
        for row in rows:
            reviewers.append(ReviewerStruct(row))
        return reviewers

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
