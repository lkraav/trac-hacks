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
from trac.util.text import _
from trac.web.chrome import INavigationContributor, ITemplateStreamFilter, \
                            add_link, add_stylesheet, add_script_data, add_javascript
from trac.web.main import IRequestHandler
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol.api import RepositoryManager, NoSuchChangeset
from trac.versioncontrol.diff import diff_blocks, get_diff_options
from peerReviewMain import add_ctxt_nav_items
from model import ReviewFile, Comment, PeerReviewModel
from genshi.filters.transform import Transformer

class PeerReviewPerform(Component):
    implements(INavigationContributor, IRequestHandler, IHTMLPreviewAnnotator, ITemplateStreamFilter)

    imagePath = ''

    # ITextAnnotator methods
    def get_annotation_type(self):
        return 'performCodeReview', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        rfile = context.get_hint('reviewfile')
        review = PeerReviewModel(self.env, rfile.review_id)
        data = [[c.line_num for c in Comment.select_by_file_id(self.env, rfile.file_id)],
                review]
        return data

    #line annotator for Perform Code Review page
    #if line has a comment, places an icon to indicate comment
    #if line is not in the rage of reviewed lines, it makes
    #the color a light gray
    def annotate_row(self, context, row, lineno, line, data):
        rfile = context.get_hint('reviewfile')
        if (lineno <= int(rfile.end) and lineno >= int(rfile.start)) or int(rfile.start) == 0:
            #if there is a comment on this line
            lines = data[0]
            review = data[1]
            if lineno in lines:
                return row.append(tag.th(id='L%s' % lineno)(tag.a(tag.img(src='%s' % self.imagePath) + ' ' + str(lineno),
                                                                  href='javascript:getComments(%s, %s)' %
                                                                       (lineno, rfile.file_id))))
            if review['status'] != 'closed':
                return row.append(tag.th(id='L%s' % lineno)(tag.a(lineno, href='javascript:addComment(%s, %s, -1)'
                                                                           % (lineno, rfile.file_id))))
            else:
                return row.append(tag.th(str(lineno), id='L%s' % lineno))

        #color line numbers outside range light gray
        return row.append(tag.th(id='L%s' % lineno)(tag.font(lineno, color='#CCCCCC')))

    # ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        def repl_jquery(name, event):
            """ Replace Trac jquery.js with jquery.js coming with plugin. """
            attrs = event[1][1]
            #match=re.match(self.PATH_REGEX, req.path_info)
            #if match and attrs.get(name) and attrs.get(name).endswith("common/js/jquery.js"):
            if attrs.get(name):
                if attrs.get(name).endswith("common/js/jquery.js"):
                    return attrs.get(name) .replace("common/js/jquery.js", 'req/js/jquery-1.11.2.min.js')
                elif attrs.get(name) and attrs.get(name).endswith("common/js/keyboard_nav.js"):
                    #keyboard_nav.js uses function live() which was removed with jQuery 1.9. Use a fixed script here
                    return attrs.get(name) .replace("common/js/keyboard_nav.js", 'req/js/keyboard_nav.js')
            return attrs.get(name) #.replace('#trac-add-comment', '?minview')

        # The post action URL must be changed to include '?minview' otherwise any action like
        # 'preview' would result in a new full page instead of the minimal page
        stream = stream | Transformer('//head/script').attr('src', repl_jquery)
        add_javascript(req, 'hw/js/jquery-ui-1.11.4.min.js')
        add_stylesheet(req, 'hw/css/jquery-ui-1.11.4.min.css')
        return stream

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

        #get the fileID from the request arguments
        fileid = req.args.get('IDFile')
        if not fileid:
            raise TracError("No file ID given - unable to load page.", "File ID Error")

        repos = RepositoryManager(self.env).get_repository('')
        if not repos:
            raise TracError("Unable to acquire subversion repository.", "Subversion Repository Error")

        #make the thumbtac image global so the line annotator has access to it
        self.imagePath = self.env.href.chrome() + '/hw/images/thumbtac11x11.gif'

        data = {'file_id': fileid}

        rfile = ReviewFile(self.env, fileid)  # Raises 'ResourceNotFound' on error
        review = PeerReviewModel(self.env, rfile.review_id)
        data['review_file'] = rfile
        data['review'] = review

        # The following may raise an exception if revision can't be found
        rev = rfile.version
        if rev:
            rev = repos.normalize_rev(rev)
        rev_or_latest = rev or repos.youngest_rev
        node = get_existing_node(self.env, repos, rfile.path, rev_or_latest)

        # Data for parent review if any
        if review['parent_id'] != 0:
            par_review = PeerReviewModel(self.env, review['parent_id'])  # Raises 'ResourceNotFound' on error
            parfile = ReviewFile(self.env, get_parent_file_id(self.env, rfile, review['parent_id']))

            lines = [c.line_num for c in Comment.select_by_file_id(self.env, parfile.file_id)]
            parfile.comments = list(set(lines))  # remove duplicates
            par_revision = parfile.version
            if par_revision:
                par_revision = repos.normalize_rev(par_revision)
            rev_or_latest = par_revision or repos.youngest_rev
            par_node = get_existing_node(self.env, repos, parfile.path, rev_or_latest)
        else:
            par_review = None
            parfile = None  # TODO: there may be some error handling missing for this. Create a dummy here?
        data['par_file'] = parfile
        data['parent_review'] = par_review

        # Wether to show the full file in the browser.
        if int(rfile.start) == 0:
            data['fullrange'] = True
        else:
            data['fullrange'] = False

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
        rev = None  # IS this correct? Seems to work with the call 'rev=rev or node.rev' further down
        content = node.get_content().read(mimeview.max_preview_size)
        if not is_binary(content):
            if mime_type != 'text/plain':
                plain_href = self.env.href.peerReviewBrowser(node.path, rev=rev or node.rev, format='txt')
                add_link(req, 'alternate', plain_href, 'Plain Text', 'text/plain')

        if par_review:
            # A followup review with diff viewer
            create_diff_data(req, data, node, par_node)
        else:
            context = Context.from_request(req, 'source', node.path, node.created_rev)
            context.set_hints(reviewfile=rfile)

            preview_data = mimeview.preview_data(context, content, len(content),
                                                 mime_type, node.created_path,
                                                 None,
                                                 annotations=['performCodeReview'])
            data['file_rendered'] = preview_data['rendered']

        scr_data = {'peer_comments': [c.line_num for c in Comment.select_by_file_id(self.env, rfile.file_id)],
                    'peer_file_id': fileid}
        if par_review:
            scr_data['peer_parent_file_id'] = parfile.file_id
            scr_data['peer_parent_comments'] = [c.line_num for c in Comment.select_by_file_id(self.env, parfile.file_id)]
        else:
            scr_data['peer_parent_comments'] = []
        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/diff.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_script_data(req, scr_data)
        add_javascript(req, "hw/js/peer_review_perform.js")
        add_ctxt_nav_items(req)

        return 'peerReviewPerform.html', data, None


def get_parent_file_id(env, rfile, par_review_id):

    fid = u"%s%s%s" % (rfile.path, rfile.start, rfile.end)

    rfiles = ReviewFile.select_by_review(env, par_review_id)
    for f in rfiles:
        tmp = u"%s%s%s" % (f.path, f.start, f.end)
        if tmp == fid:
            return f.file_id
    return 0


def create_diff_data(req, data, node, par_node):
    style, options, diff_data = get_diff_options(req)

    old = file_data_from_repo(par_node)
    new = file_data_from_repo(node)

    if old == new:
        data['nochanges'] = True

    if diff_data['options']['contextall']:
        context = None
    else:
        context = diff_data['options']['contextlines']

    diff = diff_blocks(old, new, context=context,
                       ignore_blank_lines=diff_data['options']['ignoreblanklines'],
                       ignore_case=diff_data['options']['ignorecase'],
                       ignore_space_changes=diff_data['options']['ignorewhitespace'])

    review = data['review']
    par_review = data['parent_review']
    changes = []
    info = {# 'title': '',
            # 'comments': 'Ein Kommentar',
            'diffs': diff,
            'new': {'path': node.path, 'rev': "%s (Review #%s)" % (node.rev, review['review_id']), 'shortrev': node.rev},
            'old': {'path': par_node.path, 'rev': "%s (Review #%s)" % (par_node.rev, par_review['review_id']),
                    'shortrev': par_node.rev},
            'props': []}
    changes.append(info)
    data['changes'] = changes

    data['diff'] = diff_data  # {'style': 'inline', 'options': []},
    data['longcol'] = 'Revision',
    data['shortcol'] = 'r'


def file_data_from_repo(node):

    dat = ''
    content = node.get_content()
    res = content.read()
    while res:
        dat += res
        res = content.read()
    return dat.splitlines()
