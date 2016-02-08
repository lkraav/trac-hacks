# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Team5 
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.


class ReviewCommentStruct(object):
    """Stores a ReviewComment Entry"""

    #Individual comment ID number
    IDComment = "-1"

    #File ID to which the comment belongs
    IDFile = ""

    #Comment ID of the comment's hierarchically parent
    IDParent = "-1"

    #Line number the ID refers to
    LineNum = ""

    #Author of the comment
    Author = ""

    #Comment's text
    Text = ""

    #Attachment name and path
    AttachmentPath = ""

    #Date comment created
    DateCreate = -1

    #Collection of comment IDs belonging to the comment's hierarchically children
    Children = {}

    def __init__(self, row):
        if row is not None:
            #initialize variables
            self.IDComment = row[0]
            self.IDFile = row[1]
            self.IDParent = row[2]
            self.LineNum = row[3]
            self.Author = row[4]
            self.Text = row[5]
            self.AttachmentPath = row[6]
            self.DateCreate = row[7]
            self.Children = {}
            if not self.AttachmentPath:
                self.AttachmentPath = ""

    def save(self, db):
        if self.IDComment == "-1":
            #Add information to a new database entry
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO peer_review_comment (file_id, parent_id, line_num,
                author, comment, attachment_path, created)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (self.IDFile, self.IDParent, self.LineNum, self.Author,
                      self.Text, self.AttachmentPath, self.DateCreate))
            self.IDComment = db.get_last_id(cursor, 'peer_review_comment', 'comment_id')
            db.commit()
        else:
            #Update information in existing database entry
            cursor = db.cursor()
            cursor.execute("""
                UPDATE peer_review_comment SET file_id=%s, IDParent=%s, line_num=%s,
                  author=%s, comment=%s, attachment_path=%s, created=%s
                WHERE comment_id=%s
                """, (self.IDFile, self.IDParent, self.LineNum, self.Author,
                      self.Text, self.AttachmentPath, self.DateCreate,
                      self.IDComment))
            db.commit()
        return self.IDComment
