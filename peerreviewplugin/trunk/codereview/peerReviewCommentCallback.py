#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#


import os
import shutil
import sys
import time
import unicodedata
import urllib
import json
from trac import util
from trac.core import *
from trac.util import Markup
from trac.web.main import IRequestHandler

from dbBackend import *
from model import ReviewFile, Review, Comment

def writeJSONResponse(rq, data, httperror=200):
    writeResponse(rq, json.dumps(data), httperror)


def writeResponse(req, data, httperror=200):
    data=data.encode('utf-8')
    req.send_response(httperror)
    req.send_header('Content-Type', 'text/plain; charset=utf-8')
    req.send_header('Content-Length', len(data))
    req.end_headers()
    req.write(data)

class PeerReviewCommentHandler(Component):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewCommentCallback'

    #This page should never be called directly.  It should only be called
    #by JavaScript HTTPRequest calls.
    def process_request(self, req):

        data = {}

        if not (req.perm.has_permission('CODE_REVIEW_MGR') or
                req.perm.has_permission('CODE_REVIEW_DEV')):

            data['invalid'] = 4
            return 'peerReviewCommentCallback.html', data, None

        data['invalid'] = 0
        data['trac.href.peerReviewCommentCallback'] = \
            self.env.href.peerReviewCommentCallback()

        if req.method == 'POST':
            if req.args.get('addcomment'):
                # TODO: This is not really nice but at least it prevents creation of comments for now...
                if self.review_is_closed(req):
                    data['invalid'] = 'closed'
                    return 'peerReviewCommentCallback.html', data, None

                comment = Comment(self.env)
                comment.file_id = data['fileid'] = req.args.get('fileid')
                comment.parent_id = data['parentid'] = req.args.get('parentid')
                comment.comment = req.args.get('comment')
                comment.line_num = data['line'] = req.args.get('line')
                comment.author = req.authname
                comment.insert()
                writeJSONResponse(req, data)

        actionType = req.args.get('actionType')

        if actionType == 'getCommentTree':
            self.getCommentTree(req, data)

        elif actionType == 'getCommentFile':
            self.getCommentFile(req, data)

        else:
            data['invalid'] = 5

        return 'peerReviewCommentCallback.html', data, None

    def review_is_closed(self, req):
        fileid = req.args.get('IDFile')
        if not fileid:
            fileid = req.args.get('fileid')
        rfile = ReviewFile(self.env, fileid)
        review = Review(self.env, rfile.review_id)
        if review.status == 'closed':
            return True
        return False

    #Used to send a file that is attached to a comment
    def getCommentFile(self, req, data):
        data['invalid'] = 6
        shortPath = req.args.get('fileName')
        idFile = req.args.get('IDFile')
        if idFile is None or shortPath is None:
            return

        shortPath = urllib.unquote(shortPath)
        self.path = os.path.join(self.env.path, 'attachments', 'CodeReview',
                                 urllib.quote(idFile))
        self.path = os.path.normpath(self.path)
        attachments_dir = os.path.join(os.path.normpath(self.env.path),
                                       'attachments')
        commonprefix = os.path.commonprefix([attachments_dir, self.path])
        assert commonprefix == attachments_dir
        fullPath = os.path.join(self.path, shortPath)
        req.send_header('Content-Disposition', 'attachment; filename=' + shortPath)
        req.send_file(fullPath)

    #Creates a comment based on the values from the request
    def createComment(self, req, data):
        data['invalid'] = 5
        struct = ReviewCommentStruct(None)
        struct.IDParent = req.args.get('IDParent')
        struct.IDFile = req.args.get('IDFile')
        struct.LineNum = req.args.get('LineNum')
        struct.Author = util.get_reporter_id(req)
        struct.Text = req.args.get('Text')
        struct.DateCreate = int(time.time())

        if struct.IDFile is None or struct.LineNum is None or \
                struct.Author is None or struct.Text is None:
            return

        if struct.IDFile == "" or struct.LineNum == "" or struct.Author == "":
            return

        if struct.Text == "":
            return

        if struct.IDParent is None or struct.IDParent == "":
            struct.IDParent = "-1"

        #If there was a file uploaded with the comment, place it in the correct spot
        #The basic parts of this code were taken from the file upload portion of
        #the trac wiki code

        if 'FileUp' in req.args:
            upload = req.args['FileUp']
            if upload and upload.filename:
                self.path = \
                    os.path.join(self.env.path, 'attachments',
                                 'CodeReview', urllib.quote(struct.IDFile))
                self.path = os.path.normpath(self.path)
                if hasattr(upload.file, 'fileno'):
                    size = os.fstat(upload.file.fileno())[6]
                else:
                    size = upload.file.len
                if size != 0:
                    filename = urllib.unquote(upload.filename)
                    filename = filename.replace('\\', '/').replace(':', '/')
                    filename = os.path.basename(filename)
                    if sys.version_info[0] > 2 or (sys.version_info[0] == 2 and sys.version_info[1] >= 3):
                        filename = unicodedata.normalize('NFC', unicode(filename, 'utf-8')).encode('utf-8')
                    attachments_dir = os.path.join(os.path.normpath(self.env.path), 'attachments')
                    commonprefix = os.path.commonprefix([attachments_dir, self.path])
                    assert commonprefix == attachments_dir
                    if not os.access(self.path, os.F_OK):
                        os.makedirs(self.path)
                    path, targetfile = util.create_unique_file(os.path.join(self.path, filename))
                    try:
                        shutil.copyfileobj(upload.file, targetfile)
                        struct.AttachmentPath = os.path.basename(path)
                    finally:
                        targetfile.close()
        struct.save(self.env.get_db_cnx())

    #Returns a comment tree for the requested line number
    #in the requested file
    def getCommentTree(self, req, data):
        IDFile = req.args.get('IDFile')
        LineNum = req.args.get('LineNum')
        if IDFile is None or LineNum is None:
            data['invalid'] = 1
            return
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        comments = dbBack.getCommentsByFileIDAndLine(IDFile, LineNum)
        commentHtml = ""
        first = True
        keys = comments.keys()
        keys.sort()
        for key in keys:
            if comments[key].IDParent not in comments:
                commentHtml += self.buildCommentHTML(comments[key], 0, LineNum, IDFile, first)
                first = False
        if commentHtml == "":
            commentHtml = "No Comments on this Line"
        data['lineNum'] = LineNum
        data['fileID'] = IDFile
        data['commentHTML'] = Markup(commentHtml)

    #Recursively builds the comment html to send back.
    def buildCommentHTML(self, comment, nodesIn, LineNum, IDFile, first):
        if nodesIn > 50:
            return ""

        childrenHTML = ""
        keys = comment.Children.keys()
        keys.sort()
        for key in keys:
            child = comment.Children[key]
            childrenHTML += self.buildCommentHTML(child, nodesIn + 1, LineNum, IDFile, False)

        factor = 15
        width = 5 + nodesIn * factor

        html = "<table width=\"400px\" style=\"border-collapse: collapse; display: block;\" id=\"" + str(comment.IDParent) + ":" + str(comment.IDComment) + "\">"
        if not first:
            html += "<tr><td width=\"" + `width` + "px\"></td>"
            html += "<td colspan=\"3\" width=\"" + `(400-width)` + "px\" style=\"border-top: 1px solid #C0C0C0;\"></td></tr>"
        html += "<tr><td width=\"" + `width` + "px\"></td>"
        html += "<td colspan=\"2\" align=\"left\" width=\"" + `(400-100-width)` + "px\">Author: " + comment.Author + "</td>"
        html += "<td width=\"100px\" align=\"right\">" + util.format_date(comment.DateCreate) + "</td></tr>"
        html += "<tr><td width=\"" + `width` + "px\"></td><td valign=\"top\" width=\"" + `factor` + "px\" id=\"" + str(comment.IDComment) + "TreeButton\">"
        if not childrenHTML == "":
            html += "<img src=\"" + self.env.href.chrome() + "/hw/images/minus.gif\" onclick=\"collapseComments(" + str(comment.IDComment) + ");\">"
        html += "</td>"
        html += "<td colspan=\"2\" align=\"left\" width=\"" + `(400-width-factor)` + "px\" bgcolor=\"#F7F7F0\" style=\"border: 1px solid #999999\">" + comment.Text + "</td></tr>"
        html += "<tr><td width=\"" + `width` + "px\"></td><td width=\"" + `factor` + "px\"></td>"
        html += "<td width=\"" + `(400-100-factor-width)` + "px\" align=\"left\">"
        if comment.AttachmentPath != "":
            html += "<a border=0 alt=\"Code Attachment\"  href=\"" + self.env.href.peerReviewCommentCallback() + "?actionType=getCommentFile&fileName=" + comment.AttachmentPath + "&IDFile=" + str(IDFile) + "\"><img src=\"" + self.env.href.chrome() + "/hw/images/paper_clip.gif\"> " +  comment.AttachmentPath + "</a>"
        html += "</td>"
        html += "<td width=\"100px\" align=\"right\">"
        html += "<a href=\"javascript:addComment(" + str(LineNum) + ", " + str(IDFile) + ", " +  str(comment.IDComment) + ")\">Reply</a></td></tr>"
        html += "<tr height=\"3\"><td width=\"" + `width` + "px\"></td><td width=\"" + `factor` + "px\"></td><td width=\"" + `(400-width-factor)` + "px\" colspan=\"2\"></td></tr>"
        html += "</table>"

        html += childrenHTML
        return html
