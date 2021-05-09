#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016-2021 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

import json
from codereview.model import ReviewCommentModel, PeerReviewModel, ReviewDataModel, ReviewFileModel
from codereview.util import get_review_for_file, not_allowed_to_comment, review_is_finished, review_is_locked
from functools import partial
try:
    from genshi.template.markup import MarkupTemplate
except ImportError:
    pass  # We are Trac 1.4 and use Jinja2
from trac.core import *
from trac.util.datefmt import format_date, to_datetime, user_time
from trac.util.html import Markup
from trac.web.chrome import Chrome, web_context
from trac.web.main import IRequestHandler
from trac.wiki import format_to_html


def writeJSONResponse(rq, data, httperror=200):
    writeResponse(rq, json.dumps(data), httperror, content_type='application/json; charset=utf-8')


def writeResponse(req, data, httperror=200, content_type='text/plain; charset=utf-8'):
    data = data.encode('utf-8')
    req.send_response(httperror)
    req.send_header('Content-Type', content_type)
    req.send_header('Content-Length', len(data))
    req.end_headers()
    req.write(data)


class PeerReviewCommentHandler(Component):
    """Handling of comments for reviews. This component is responsible for creating comments and
    building comment trees for display.
    """
    implements(IRequestHandler)

    # IRequestHandler methods

    def match_request(self, req):
        if req.path_info == '/peercomment':
            return True
        return req.path_info == '/peerReviewCommentCallback'

    # This page should never be called directly.  It should only be called
    # by JavaScript HTTPRequest calls.
    def process_request(self, req):
        data = {'invalid': 0}

        if not 'CODE_REVIEW_VIEW' in req.perm:
            writeResponse(req, "", 403)

        if req.method == 'POST':
            if not 'CODE_REVIEW_DEV' in req.perm:
                writeResponse(req, "", 403)
            if req.args.get('addcomment'):
                fileid = req.args.get('fileid')
                # This shouldn't happen but still...
                review = get_review_for_file(self.env, fileid)
                if not_allowed_to_comment(self.env, review, req.perm, req.authname):
                    writeResponse(req, "", 403)
                    return
                # We shouldn't end here but in case just drop out.
                if self.review_is_closed(req):
                    data['invalid'] = 'closed'
                    if hasattr(Chrome, 'jenv'):
                        return 'peerreview_comment_callback_jinja.html', data
                    else:
                        return 'peerreview_comment_callback.html', data, None

                rfile = ReviewFileModel(self.env, fileid)
                data['path'] = rfile['path'].lstrip('/')  # Trac path doesn't start with '/'. Db path does.
                txt = req.args.get('comment')
                comment = ReviewCommentModel(self.env)
                comment['file_id'] = data['fileid'] = req.args.get('fileid')
                comment['parent_id'] = data['parentid'] = req.args.get('parentid')
                comment['comment'] = txt
                comment['line_num'] = data['line'] = req.args.get('line')
                comment['author'] = req.authname
                if txt and txt.strip():
                    comment.insert()
                writeJSONResponse(req, data)
                return
            elif req.args.get('markread'):
                data['fileid'] = req.args.get('fileid')
                data['line'] = req.args.get('line')
                rfile = ReviewFileModel(self.env, data['fileid'])
                data['path'] = rfile['path']
                if req.args.get('markread') == 'read':
                    rev_dat = ReviewDataModel(self.env)
                    rev_dat['file_id'] = data['fileid']
                    rev_dat['comment_id'] = req.args.get('commentid')
                    rev_dat['review_id'] = req.args.get('reviewid')
                    rev_dat['owner'] = req.authname
                    rev_dat['type'] = 'read'
                    rev_dat['data'] = 'read'
                    rev_dat.insert()
                else:
                    rev_dat = ReviewDataModel(self.env)
                    rev_dat['file_id'] = data['fileid']
                    rev_dat['comment_id'] = req.args.get('commentid')
                    rev_dat['owner'] = req.authname
                    for rev in rev_dat.list_matching_objects():
                        rev.delete()
                writeJSONResponse(req, data)
                return

        if req.args.get('action') == 'commenttree':
            self.get_comment_tree(req, data)
            data['path'] = req.args.get('path', '')
            if hasattr(Chrome, 'jenv'):
                return 'peerreview_comment_jinja.html', data
            else:
                return 'peerreview_comment.html', data, None
        elif req.args.get('action') == 'addcommentdlg':
            data['create_add_comment_dlg'] = True
            data['form_token'] = req.form_token
            if hasattr(Chrome, 'jenv'):
                return 'peerreview_comment_jinja.html', data
            else:
                return 'peerreview_comment.html', data, None

        actionType = req.args.get('actionType')
        if actionType == 'getCommentFile':
            self.env.log.info("Trying to get comment file. Not implemented.")
            # self.getCommentFile_obsolete(req, data)
            data['invalid'] = 5
        else:
            data['invalid'] = 5
        if hasattr(Chrome, 'jenv'):
            return 'peerreview_comment_callback_jinja.html', data
        else:
            return 'peerreview_comment_callback.html', data, None

    def review_is_closed(self, req):
        fileid = req.args.get('IDFile')
        if not fileid:
            fileid = req.args.get('fileid')
        review = get_review_for_file(self.env, fileid)
        if review['status'] == 'closed':
            return True
        return False

    # Returns a comment tree for the requested line number
    # in the requested file
    def get_comment_tree(self, req, data):
        fileid = req.args.get('IDFile') or req.args.get('fileid')
        linenum = req.args.get('LineNum') or req.args.get('line')

        if not fileid or not linenum:
            data['invalid'] = 1
            return

        with self.env.db_query as db:
            comments = ReviewCommentModel.create_comment_tree(self.env, fileid, linenum)
        my_comment_data = ReviewDataModel.comments_for_file_and_owner(self.env, fileid, req.authname)
        data['read_comments'] = [c_id for c_id, t, dat in my_comment_data if t == 'read']

        rfile = ReviewFileModel(self.env, fileid)
        review = PeerReviewModel(self.env, rfile['review_id'])
        data['review'] = review
        # A finished review can't be changed anymore except by a manager
        data['is_finished'] = review_is_finished(self.env.config, review)
        # A user can't change his voting for a reviewed review
        data['review_locked'] = review_is_locked(self.env.config, review, req.authname)
        data['not_allowed'] = not_allowed_to_comment(self.env, review, req.perm, req.authname)

        comment_html = ""
        keys = sorted(comments.keys())
        for key in keys:
            if comments[key].parent_id == -1:
                comment_html += self.build_comment_html(req, comments[key], 0, linenum, fileid, data)
        comment_html = comment_html.strip()
        if not comment_html:
            comment_html = "No Comments on this Line"
        data['lineNum'] = linenum
        data['fileID'] = fileid
        data['commentHTML'] = Markup(comment_html)

    comment_template = u"""
            <table xmlns:py="http://genshi.edgewall.org/"
                   style="width:450px"
                   py:attrs="{'class': 'comment-table'} if comment.comment_id in read_comments else {'class': 'comment-table comment-notread'}"
                   id="c-${comment.comment_id}" data-child-of="$comment.parent_id">
            <tbody>
            <tr>
                <td style="width:${width}px"></td>
                <td colspan="3" style="width:${450-width}px"
                class="border-col"></td>
            </tr>
            <tr>
                <td style="width:${width}px"></td>
                <td colspan="2" class="comment-author">Author: ${authorinfo(comment.author)}
                <a py:if="comment.comment_id not in read_comments"
                   href="javascript:markCommentRead($line, $fileid, $comment.comment_ic, ${review['review_id']})">Mark read</a>
                <a py:if="comment.comment_ic in read_comments"
                   href="javascript:markCommentNotread($line, $fileid, $comment.comment_id, ${review['review_id']})">Mark unread</a>
                </td>
                <td style="width:100px" class="comment-date">$date</td>
            </tr>
            <tr>
                <td style="width:${width}px"></td>
                <td valign="top" style="width:${factor}px" id="${comment.comment_id}TreeButton">
                    <img py:if="childrenHTML" src="${href.chrome('hw/images/minus.gif')}" id="${comment.comment_id}collapse"
                         onclick="collapseComments(${comment.comment_id});" style="cursor: pointer;" />
                    <img py:if="childrenHTML" src="${href.chrome('hw/images/plus.gif')}" style="display: none;cursor:pointer;"
                         id="${comment.comment_id}expand"
                         onclick="expandComments(${comment.comment_id});" />
                </td>
                <td colspan="2">
                <div class="comment-text">
                    $text
                </div>
                </td>
            </tr>
            <tr>
                <td></td>
                <td></td>
                <td>
                    <!--! Attachment -->
                    <a py:if="comment.AttachmentPath" border="0" alt="Code Attachment"
                       href="${callback}?actionType=getCommentFile&amp;fileName=${comment.AttachmentPath}&amp;IDFile=$fileid">
                        <img src="${href.chrome('hw/images/paper_clip.gif')}" /> $comment.AttachmentPath
                    </a>
                </td>
                <td class="comment-reply">
                   <a py:if="not is_locked" href="javascript:addComment($line, $fileid, $comment.comment_id)">Reply</a>
                </td>
            </tr>
            </tbody>
            </table>
        """
    comment_template_jinja = u"""
            <table style="width:450px"
                   class="${'comment-table' if comment.comment_id in read_comments else 'comment-table comment-notread'}"
                   id="c-${comment.comment_id}" data-child-of="${comment.parent_id}">
            <tbody>
            <tr>
                <td style="width:${width}px"></td>
                <td colspan="3" style="width:${450-width}px"
                class="border-col"></td>
            </tr>
            <tr>
                <td style="width:${width}px"></td>
                <td colspan="2" class="comment-author">Author: ${authorinfo(comment.author)}
                # if comment.comment_id not in read_comments:
                <a href="javascript:markCommentRead(${line}, ${fileid}, ${comment.comment_id}, ${review['review_id']})">Mark read</a>
                # else:
                <a href="javascript:markCommentNotread(${line}, ${fileid}, ${comment.comment_id}, ${review['review_id']})">Mark unread</a>
                # endif
                </td>
                <td style="width:100px" class="comment-date">${date}</td>
            </tr>
            <tr>
                <td style="width:${width}px"></td>
                <td valign="top" style="width:${factor}px" id="${comment.comment_id}TreeButton">
                    # if childrenHTML:
                    <img src="${href.chrome('hw/images/minus.gif')}" id="${comment.comment_id}collapse"
                         onclick="collapseComments(${comment.comment_id});" style="cursor: pointer;" />
                    <img src="${href.chrome('hw/images/plus.gif')}" style="display: none;cursor:pointer;"
                         id="${comment.comment_id}expand"
                         onclick="expandComments(${comment.comment_id});" />
                    # endif
                </td>
                <td colspan="2">
                <div class="comment-text">
                    ${text}
                </div>
                </td>
            </tr>
            <tr>
                <td></td>
                <td></td>
                <td>
                    ## Attachment
                    # if comment.AttachmentPath:
                    <a border="0" alt="Code Attachment"
                       href="${callback}?actionType=getCommentFile&amp;fileName=${comment.AttachmentPath}&amp;IDFile=${fileid}">
                        <img src="${href.chrome('hw/images/paper_clip.gif')}" /> ${comment.AttachmentPath}
                    </a>
                    # endif
                </td>
                <td class="comment-reply">
                   # if not is_locked:
                   <a href="javascript:addComment(${line}, ${fileid}, ${comment.comment_id})">Reply</a>
                   # endif
                </td>
            </tr>
            </tbody>
            </table>
        """

    # Recursively builds the comment html to send back.
    def build_comment_html(self, req, comment, indent, linenum, fileid, data):
        if indent > 50:
            return ""

        children_html = ""
        keys = sorted(comment.children.keys())
        for key in keys:
            child = comment.children[key]
            children_html += self.build_comment_html(req, child, indent + 1, linenum, fileid, data)

        factor = 15
        width = 5 + indent * factor

        chrome = Chrome(self.env)
        context = web_context(req)
        tdata = {'width': width,
                 'text': format_to_html(self.env, context, comment.comment,
                                        escape_newlines=True),
                 'comment': comment,
                 'date': user_time(req, format_date, to_datetime(comment.created)),
                 'factor': factor,
                 'childrenHTML': children_html != '' or False,
                 'href': req.href,
                 'line': linenum,
                 'fileid': fileid,
                 'callback': req.href.peerReviewCommentCallback(),  # this is for attachments
                 'review': data['review'],
                 'is_locked': data['is_finished'] or data['review_locked'] or data.get('not_allowed', False),
                 'read_comments': data['read_comments'],
                 'authorinfo': partial(chrome.authorinfo, req)
                 }

        if hasattr(Chrome, 'jenv'):
            template = chrome.jenv.from_string(self.comment_template_jinja)
            return chrome.render_template_string(template, tdata, True) + children_html
        else:
            tbl = MarkupTemplate(self.comment_template, lookup='lenient')
            return tbl.generate(**tdata).render(encoding=None) + children_html
