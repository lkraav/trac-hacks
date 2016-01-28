#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

# Code Review plugin
# This class handles the display for the perform code review page
# The file contents are taken from the respository and converted to
# an HTML friendly format.  The line annotator customizes the
# repository browser's line number to indicate what lines are being
# reviewed and if there are any comments on a particular line.

from genshi.builder import tag
from trac.core import *
from trac.mimeview import *
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.web.chrome import INavigationContributor, \
                            add_link, add_stylesheet
from trac.web.main import IRequestHandler
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol.api import RepositoryManager
from dbBackend import *
from peerReviewMain import add_ctxt_nav_items
from model import ReviewFile


class UserbaseModule(Component):
    implements(INavigationContributor, IRequestHandler, IHTMLPreviewAnnotator)

    #global variables for the line annotator
    comments = {}
    fileID = -1
    imagePath = ''
    lineStart = -1
    lineEnd = -1
    
    # ITextAnnotator methods
    def get_annotation_type(self):
        return 'performCodeReview', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        return None

    #line annotator for Perform Code Review page
    #if line has a comment, places an icon to indicate comment
    #if line is not in the rage of reviewed lines, it makes
    #the color a light gray
    def annotate_row(self, context, row, lineno, line, data):
        htmlImageString = '<img src="' + self.imagePath + '">'
        #make line number light gray
        if (lineno <= self.lineEnd and lineno >= self.lineStart) or self.lineStart == 0:
            #if there is a comment on this line
            if self.comments.has_key(lineno):
                #if there is more than 0 comments
                if self.comments[lineno] > 0:
                    return row.append(tag.th(id='L%s' % lineno)(tag.a(tag.img(src='%s' % self.imagePath) + ' ' + str(lineno), href='javascript:getComments(%s, %s)' % (lineno, self.fileID))))
            return row.append(tag.th(id='L%s' % lineno)(tag.a(lineno, href='javascript:addComment(%s, %s, -1)' % (lineno, self.fileID))))
        return row.append(tag.th(id='L%s' % lineno)(tag.font(lineno, color='#CCCCCC')))

    #def annotate_line(self, number, content):
    #    htmlImageString = '<img src="' + self.imagePath + '">'
    #    #make line number light gray
    #    if(number <= self.lineEnd and number >= self.lineStart):
    #        #if there is a comment on this line
    #        if(self.comments.has_key(number)):
    #            #if there is more than 0 comments
    #            if(self.comments[number] > 0):
    #                return ('<th id="L%s"><a href="javascript:getComments(%s, %s)">' % (number, number, self.fileID)) + htmlImageString + ('&nbsp;%s</a></th>' % (number))
    #        return '<th id="L%s"><a href="javascript:addComment(%s, %s, -1)">%s</a></th>' % (number, number, self.fileID, number)
    #    return '<th id="L%s"><font color="#CCCCCC">%s</font></th>' % (number, number)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return []
        
    # IRequestHandler methods
    def match_request(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            return req.path_info == '/peerReviewPerform'

    def process_request(self, req):

        req.perm.require('CODE_REVIEW_DEV')
        data = {}

        if 'CODE_REVIEW_MGR' in req.perm:
            data['manager'] = 1
        else:
            data['manager'] = 0

        #get the fileID from the request arguments
        idFile = req.args.get('IDFile')
        self.fileID = idFile
        #if the file id is not set - display an error message
        if idFile is None:
            TracError("No file ID given - unable to load page.", "File ID Error")

        #get the database
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        #get all the comments for this file
        self.comments = dbBack.getCommentDictForFile(idFile)
        #get the file properties from the database
        rfile = ReviewFile(self.env, idFile)
        #make the thumbtac image global so the line annotator has access to it
        self.imagePath = self.env.href.chrome() + '/hw/images/thumbtac11x11.gif'

        #if the file is not found in the database - display an error message
        if not rfile:
            TracError("Unable to locate given file ID in database.", "File ID Error")

        #get the respository
        repos = RepositoryManager(self.env).get_repository('')
        #get the file attributes
        data['review_file'] = rfile

        #make these global for the line annotator
        self.lineEnd = int(rfile.end)
        self.lineStart = int(rfile.start)
        # Wther to show the full file in the browser.
        if self.lineStart == 0:
            data['fullrange'] = True
        else:
            data['fullrange'] = False
        #if the repository can't be found - display an error message
        if repos is None:
            TracError("Unable to acquire subversion repository.", "Subversion Repository Error")

        #get the correct location - using revision number and repository path
        try:
            node = get_existing_node(self.env, repos, rfile.path, rfile.version)
        except:
            youngest_rev = repos.get_youngest_rev()
            node = get_existing_node(self.env, repos, rfile.Path, youngest_rev)

        #if the node can't be found - display error message
        if node is None:
            TracError("Unable to locate subversion node for this file.", "Subversion Node Error")

        # Generate HTML preview - this code take from Trac - refer to their documentation
        mime_type = node.content_type
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = get_mimetype(node.name) or mime_type or 'text/plain'

        ctpos = mime_type.find('charset=')
        if ctpos >= 0:
            charset = mime_type[ctpos + 8:]
        else:
            charset = None

        mimeview = Mimeview(self.env)
        path = req.args.get('path', '/')
        rev = None
        content = node.get_content().read(mimeview.max_preview_size)
        if not is_binary(content):
            if mime_type != 'text/plain':
                plain_href = self.env.href.peerReviewBrowser(node.path, rev=rev and node.rev, format='txt')
                add_link(req, 'alternate', plain_href, 'Plain Text', 'text/plain')

        context = Context.from_request(req, 'source', path, node.created_rev)
        preview_data = mimeview.preview_data(context, content, len(content),
                                             mime_type, node.created_path,
                                             None,
                                             annotations=['performCodeReview'])

        data['file'] = preview_data['rendered']
        
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'common/css/code.css')
        add_ctxt_nav_items(req)
        return 'peerReviewPerform.html', data, None
