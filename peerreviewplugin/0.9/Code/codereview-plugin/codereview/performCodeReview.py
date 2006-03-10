# Copyright (C) 2006 Brandon Cannaday <cannadbt@rose-hulman.edu>
# Copyright (C) 2006 Michael Kuehl <mkuehl@telaranrhiod.com>
# All rights reserved.
#
# This file is part of The Trac Peer Review Plugin
#
# The Trac Peer Review Plugin is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# The Trac Peer Review Plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with The Trac Peer Review Plugin; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#


# Code Review plugin
# This class handles the display for the perform code review page
# The file contents are taken from the respository and converted to
# an HTML friendly format.  The line annotator customizes the
# repository browser's line number to indicate what lines are being
# reviewed and if there are any comments on a particular line.

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.mimeview import *
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac import util
from trac.util import escape
from codereview.dbBackend import *
from trac.web.chrome import add_stylesheet
from trac.versioncontrol.web_ui.util import *
from trac.web.chrome import add_link, add_stylesheet
import string

class UserbaseModule(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IHTMLPreviewAnnotator)

    #global variables for the line annotator
    comments = {}
    fileID = -1
    imagePath = ''
    lineStart = -1
    lineEnd = -1
    
    # ITextAnnotator methods
    def get_annotation_type(self):
    	return 'performCodeReview', 'Line', 'Line numbers'

    #line annotator for Perform Code Review page
    #if line has a comment, places an icon to indicate comment
    #if line is not in the rage of reviewed lines, it makes
    #the color a light gray
    def annotate_line(self, number, content):
        htmlImageString = '<img src="' + self.imagePath + '">'
        #make line number light gray
        if(number <= self.lineEnd and number >= self.lineStart):
            #if there is a comment on this line
            if(self.comments.has_key(number)):
                #if there is more than 0 comments
                if(self.comments[number] > 0):
                    return ('<th id="L%s"><a href="javascript:getComments(%s, %s)">' % (number, number, self.fileID)) + htmlImageString + ('&nbsp;%s</a></th>' % (number))
            return '<th id="L%s"><a href="javascript:addComment(%s, %s, -1)">%s</a></th>' % (number, number, self.fileID, number)
        return '<th id="L%s"><font color="#CCCCCC">%s</font></th>' % (number, number)
        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'codereview'
                
    def get_navigation_items(self, req):
        return []
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/performCodeReview'
                                        
    def process_request(self, req):
        if req.perm.has_permission('CODE_REVIEW_MGR'):
            req.hdf['manager'] = 1
        else:
            req.perm.assert_permission('CODE_REVIEW_DEV')
            req.hdf['manager'] = 0

        #get some link locations for the template
        req.hdf['trac.href.codeReview'] = self.env.href.codereview()
        req.hdf['trac.href.newCodeReview'] = self.env.href.newCodeReview()
        req.hdf['trac.href.peerReviewSearch'] = self.env.href.peerReviewSearch()
        req.hdf['trac.href.options'] = self.env.href.options()

        #for top-right navigation links
        req.hdf['main'] = "no"
        req.hdf['create'] = "no"
        req.hdf['search'] = "no"

        #get the fileID from the request arguments
        idFile = req.args.get('IDFile')
        self.fileID = idFile
        #if the file id is not set - display an error message
	if idFile == None:
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "File ID Error"
            req.hdf['error.message'] = "No file ID given - unable to load page."
            return 'error.cs', None

        #get the database
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        #get all the comments for this file
        self.comments = dbBack.getCommentDictForFile(idFile)
        #get the file properties from the database
        resultFile = dbBack.getReviewFile(idFile)
        #make the thumbtac image global so the line annotator has access to it
        self.imagePath = self.env.href.chrome() + '/hw/images/thumbtac11x11.gif'
        #get image and link locations
        req.hdf['trac.href.commentCallback'] = self.env.href.commentCallback()
        req.hdf['trac.href.viewCodeReview'] = self.env.href.viewCodeReview()
        req.hdf['trac.htdocs.thumbtac'] = self.imagePath
        req.hdf['trac.htdocs.plus'] = self.env.href.chrome() + '/hw/images/plus.gif'
        req.hdf['trac.htdocs.minus'] = self.env.href.chrome() + '/hw/images/minus.gif'

        #if the file is not found in the database - display an error message
        if resultFile == None:
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "File ID Error"
            req.hdf['error.message'] = "Unable to locate given file ID in database."
            return 'error.cs', None

        #get the respository
        repos = self.env.get_repository(req.authname)
        #get the file attributes
        req.hdf['review.path'] = resultFile.Path
        req.hdf['review.version'] = resultFile.Version
        req.hdf['review.lineStart'] = resultFile.LineStart
        req.hdf['review.lineEnd'] = resultFile.LineEnd
        req.hdf['review.reviewID'] = resultFile.IDReview
        #make these global for the line annotator
        self.lineEnd = string.atoi(resultFile.LineEnd)
        self.lineStart = string.atoi(resultFile.LineStart)

        #if the repository can't be found - display an error message
        if(repos == None):
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "Subversion Repository Error"
            req.hdf['error.message'] = "Unable to acquire subversion repository."
            return 'error.cs', None
        
        #get the correct location - using revision number and repository path
        node = get_existing_node(self.env, repos, resultFile.Path, resultFile.Version)
        #if the node can't be found - display error message
        if(node == None):
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "Subversion Node Error"
            req.hdf['error.message'] = "Unable to locate subversion node for this file."
            return 'error.cs', None

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
        content = node.get_content().read(mimeview.max_preview_size())
        if not is_binary(content):
            if mime_type != 'text/plain':
                plain_href = self.env.href.codeReviewBrowser(node.path, rev=rev and node.rev, format='txt')
                add_link(req, 'alternate', plain_href, 'Plain Text', 'text/plain')
                
        #assign the preview to a variable for clearsilver
        req.hdf['file'] = mimeview.preview_to_hdf(req, mime_type, charset, content, node.name, node.rev, annotations=['performCodeReview'])
        
	add_stylesheet(req, 'common/css/code.css')
	add_stylesheet(req, 'common/css/browser.css')	
        return 'performCodeReview.cs', None
                
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    #gets the directory where the htdocs are stored - images, etc.
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]
