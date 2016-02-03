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
from trac.resource import ResourceNotFound
from trac.util.text import _
from trac.web.chrome import INavigationContributor, \
                            add_link, add_stylesheet
from trac.web.main import IRequestHandler
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol.api import RepositoryManager, NoSuchChangeset, NoSuchNode
from peerReviewMain import add_ctxt_nav_items
from model import ReviewFile, Review, Comment


class PeerReviewPerform(Component):
    implements(INavigationContributor, IRequestHandler, IHTMLPreviewAnnotator)

    imagePath = ''
    
    # ITextAnnotator methods
    def get_annotation_type(self):
        return 'performCodeReview', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        rfile = context.get_hint('reviewfile')
        return [c.line_num for c in Comment.select_by_file_id(self.env, rfile.file_id)]

    #line annotator for Perform Code Review page
    #if line has a comment, places an icon to indicate comment
    #if line is not in the rage of reviewed lines, it makes
    #the color a light gray
    def annotate_row(self, context, row, lineno, line, data):
        rfile = context.get_hint('reviewfile')
        if (lineno <= int(rfile.end) and lineno >= int(rfile.start)) or int(rfile.start) == 0:
            #if there is a comment on this line
            if lineno in data:
                return row.append(tag.th(id='L%s' % lineno)(tag.a(tag.img(src='%s' % self.imagePath) + ' ' + str(lineno),
                                                                  href='javascript:getComments(%s, %s)' %
                                                                       (lineno, rfile.file_id))))
            return row.append(tag.th(id='L%s' % lineno)(tag.a(lineno, href='javascript:addComment(%s, %s, -1)'
                                                                           % (lineno, rfile.file_id))))
        #color line numbers outside range light gray
        return row.append(tag.th(id='L%s' % lineno)(tag.font(lineno, color='#CCCCCC')))

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

        #get the fileID from the request arguments
        idFile = req.args.get('IDFile')
        if not idFile:
            raise TracError("No file ID given - unable to load page.", "File ID Error")

        data['file_id'] = idFile

        #make the thumbtac image global so the line annotator has access to it
        self.imagePath = self.env.href.chrome() + '/hw/images/thumbtac11x11.gif'
        #get the file properties from the database
        rfile = ReviewFile(self.env, idFile)
        if not rfile:
            raise TracError("Unable to locate given file ID in database.", "File ID Error")

        #get the respository
        repos = RepositoryManager(self.env).get_repository('')
        data['review_file'] = rfile
        data['review'] = Review(self.env, rfile.review_id)

        # Wether to show the full file in the browser.
        if int(rfile.start) == 0:
            data['fullrange'] = True
        else:
            data['fullrange'] = False
        #if the repository can't be found - display an error message
        if repos is None:
            raise TracError("Unable to acquire subversion repository.", "Subversion Repository Error")

        #get the correct location - using revision number and repository path
        rev = rfile.version
        try:
            if rev:
                rev = repos.normalize_rev(rev)
            rev_or_latest = rev or repos.youngest_rev
            node = get_existing_node(self.env, repos, rfile.path, rev_or_latest)
        except NoSuchChangeset, e:
            raise ResourceNotFound(e.message,
                                   _('Invalid changeset number'))
        except BaseException, e:
            raise TracError(e.message)

        #if the node can't be found - display error message
        if not node:
            raise TracError("Unable to locate subversion node for this file.", "Subversion Node Error")

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
        rev = None
        content = node.get_content().read(mimeview.max_preview_size)
        if not is_binary(content):
            if mime_type != 'text/plain':
                plain_href = self.env.href.peerReviewBrowser(node.path, rev=rev or node.rev, format='txt')
                add_link(req, 'alternate', plain_href, 'Plain Text', 'text/plain')

        context = Context.from_request(req, 'source', node.path, node.created_rev)
        context.set_hints(reviewfile=rfile)

        preview_data = mimeview.preview_data(context, content, len(content),
                                             mime_type, node.created_path,
                                             None,
                                             annotations=['performCodeReview'])

        data['file'] = preview_data['rendered']
        
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/diff.css')

        add_ctxt_nav_items(req)
        return 'peerReviewPerform.html', data, None
