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
from genshi.template.markup import MarkupTemplate
from dbBackend import *
from model import ReviewFile, Comment, PeerReviewModel
from trac.wiki import format_to_html
from trac.mimeview import Context

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
        data['trac.href.peerReviewCommentCallback'] = self.env.href.peerReviewCommentCallback()

        if req.method == 'POST':
            if req.args.get('addcomment'):
                # We shouldn't end here but in case just drop out.
                if self.review_is_closed(req):
                    data['invalid'] = 'closed'
                    return 'peerReviewCommentCallback.html', data, None
                txt = req.args.get('comment')
                comment = Comment(self.env)
                comment.file_id = data['fileid'] = req.args.get('fileid')
                comment.parent_id = data['parentid'] = req.args.get('parentid')
                comment.comment = txt
                comment.line_num = data['line'] = req.args.get('line')
                comment.author = req.authname
                if txt and txt.strip():
                    comment.insert()
                writeJSONResponse(req, data)
                return

        actionType = req.args.get('actionType')

        if actionType == 'getCommentTree':
            self.get_comment_tree(req, data)

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
        review = PeerReviewModel(self.env, rfile.review_id)
        if review['status'] == 'closed':
            return True
        return False

    #Used to send a file that is attached to a comment
    def getCommentFile(self, req, data):
        data['invalid'] = 6
        short_path = req.args.get('fileName')
        fileid = req.args.get('IDFile')
        if not fileid or not short_path:
            return

        short_path = urllib.unquote(short_path)
        self.path = os.path.join(self.env.path, 'attachments', 'CodeReview',
                                 urllib.quote(fileid))
        self.path = os.path.normpath(self.path)
        attachments_dir = os.path.join(os.path.normpath(self.env.path),
                                       'attachments')
        commonprefix = os.path.commonprefix([attachments_dir, self.path])
        assert commonprefix == attachments_dir
        full_path = os.path.join(self.path, short_path)
        req.send_header('Content-Disposition', 'attachment; filename=' + short_path)
        req.send_file(full_path)

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
    def get_comment_tree(self, req, data):
        fileid = req.args.get('IDFile')
        linenum = req.args.get('LineNum')

        if not fileid or not linenum:
            data['invalid'] = 1
            return

        db = self.env.get_read_db()
        dbBack = dbBackend(db)
        comments = dbBack.getCommentsByFileIDAndLine(fileid, linenum)

        rfile = ReviewFile(self.env, fileid)
        review = PeerReviewModel(self.env, rfile.review_id)
        data['review'] = review
        data['context'] = Context.from_request(req)

        comment_html = ""
        first = True
        keys = comments.keys()
        keys.sort()
        for key in keys:
            if comments[key].IDParent not in comments:
                comment_html += self.build_comment_html(comments[key], 0, linenum, fileid, first, data)
                first = False
        comment_html = comment_html.strip()
        if not comment_html:
            comment_html = "No Comments on this Line"
        data['lineNum'] = linenum
        data['fileID'] = fileid
        data['commentHTML'] = Markup(comment_html)


    comment_template = u"""
            <table xmlns:py="http://genshi.edgewall.org/"
                   width="400px" class="comment-table"
                   id="${comment.IDParent}:${comment.IDComment}" data-child-of="$comment.IDParent">
            <tbody>
            <tr py:if="not first">
                <td width="${width}px"></td>
                <td colspan="3" width="${400-width}px" class="border-col"></td>
            </tr>
            <tr>
                <td width="${width}px"></td>
                <td colspan="2" class="comment-author" width="${400-100-width}px">Author: $comment.Author</td>
                <td width="100px" class="comment-date">$date</td>
            </tr>
            <tr>
                <td width="${width}px"></td>
                <td valign="top" width="${factor}px" id="${comment.IDComment}TreeButton">
                    <img py:if="childrenHTML" src="$chrome/hw/images/minus.gif" id="${comment.IDComment}collapse"
                         onclick="collapseComments($comment.IDComment);" style="cursor: pointer;" />
                    <img py:if="childrenHTML" src="$chrome/hw/images/plus.gif" style="display: none;cursor:pointer;"
                         id="${comment.IDComment}expand"
                         onclick="expandComments($comment.IDComment);" />
                </td>
                <td colspan="2" width="${400-width-factor}px" class="comment-text">
                    $text
                </td>
            </tr>
            <tr>
                <td width="${width}px"></td>
                <td width="${factor}px"></td>
                <td width="${400-100-factor-width}px" align="left">
                    <!--! Attachment -->
                    <a py:if="comment.AttachmentPath" border="0" alt="Code Attachment"
                       href="${callback}?actionType=getCommentFile&amp;fileName=${comment.AttachmentPath}&amp;IDFile=$fileid">
                        <img src="$chrome/hw/images/paper_clip.gif" /> $comment.AttachmentPath
                    </a>
                </td>
                <td width="100px" class="comment-reply">
                   <a py:if="review['status'] != 'closed'" href="javascript:addComment($line, $fileid, $comment.IDComment)">Reply</a>
                </td>
            </tr>
            </tbody>
            </table>
        """

    #Recursively builds the comment html to send back.
    def build_comment_html(self, comment, nodesIn, linenum, fiileid, first, data):
        if nodesIn > 50:
            return ""

        children_html = ""
        keys = comment.Children.keys()
        keys.sort()
        for key in keys:
            child = comment.Children[key]
            children_html += self.build_comment_html(child, nodesIn + 1, linenum, fiileid, False, data)

        factor = 15
        width = 5 + nodesIn * factor

        tdata = {'width': width,
                 'text': format_to_html(self.env, data['context'], comment.Text,
                                        escape_newlines=True),
                 'comment': comment,
                 'first': first,
                 'date': util.format_date(comment.DateCreate),
                 'factor': factor,
                 'childrenHTML': children_html != '' or False,
                 'chrome': self.env.href.chrome(),
                 'line': linenum,
                 'fileid': fiileid,
                 'callback': self.env.href.peerReviewCommentCallback(),
                 'review': data['review']
                 }

        tbl = MarkupTemplate(self.comment_template, lookup='lenient')
        return tbl.generate(**tdata).render(encoding=None) + children_html
