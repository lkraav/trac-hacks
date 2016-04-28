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
from genshi.core import QName
from trac.core import *
from trac.mimeview import *
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.util import format_date
from trac.util.text import _
from trac.web.chrome import INavigationContributor, ITemplateStreamFilter, Chrome, \
                            add_link, add_stylesheet, add_script_data, add_javascript
from trac.web.main import IRequestHandler
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol.api import RepositoryManager, NoSuchChangeset
from trac.versioncontrol.diff import diff_blocks, get_diff_options
from peerReviewMain import add_ctxt_nav_items
from model import Comment, PeerReviewModel, ReviewFileModel
from genshi.filters.transform import Transformer
from peerReviewView import review_is_locked, review_is_finished
from pkg_resources import get_distribution, parse_version

class PeerReviewPerform(Component):
    """Perform a code review.

    Trac 0.12 comes with a very ancient version of jQuery. This plugin replaces that version with 1.11.2 on the
    fly. Similar to Trac 1.0 you may specify your own jQuery in your config file.

    {{{#!ini
    [trac]
    jquery_location = https://path/to/jquery.js
    }}}
    If not set the bundled version will be used.

    The same can be done for the jQuery UI package and the theme to use.
    {{{#!ini
    [trac]
    jquery_ui_location = https://path/to/jquery-ui.js
    jquery_ui_theme_location = https://path/to/jquery-ui-theme.css
    }}}
    jQuery-ui 1.11.4 is bundled with this plugin.
    """
    implements(INavigationContributor, IRequestHandler, IHTMLPreviewAnnotator, ITemplateStreamFilter)

    imagePath = ''
    trac_version = get_distribution('trac').version
    legacy_trac = parse_version(trac_version) < parse_version('1.0.0')  # True if Trac V0.12.x

    # ITextAnnotator methods
    def get_annotation_type(self):
        return 'performCodeReview', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        r_file = context.get_hint('reviewfile')
        authname = context.get_hint('authname')
        review = PeerReviewModel(self.env, r_file['review_id'])

        # Is it allowed to comment on the file?
        if review_is_finished(self.env.config, review):
            is_locked = True
        else:
            is_locked = review_is_locked(self.env.config, review, authname)

        data = [[c.line_num for c in Comment.select_by_file_id(self.env, r_file['file_id'])],
                review, is_locked]
        return data

    #line annotator for Perform Code Review page
    #if line has a comment, places an icon to indicate comment
    #if line is not in the rage of reviewed lines, it makes
    #the color a light gray
    def annotate_row(self, context, row, lineno, line, data):
        r_file = context.get_hint('reviewfile')
        if (lineno <= int(r_file['line_end']) and lineno >= int(r_file['line_start'])) or int(r_file['line_start']) == 0:
            # If there is a comment on this line
            lines = data[0]
            # review = data[1]
            if lineno in lines:
                return row.append(tag.th(id='L%s' % lineno)(tag.a(tag.img(src='%s' % self.imagePath) + ' ' + str(lineno),
                                                                  href='javascript:getComments(%s, %s)' %
                                                                       (lineno, r_file['file_id']))))
            if not data[2]:
                return row.append(tag.th(id='L%s' % lineno)(tag.a(lineno, href='javascript:addComment(%s, %s, -1)'
                                                                           % (lineno, r_file['file_id']))))
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
                    jquery = self.env.config.get('trac', 'jquery_location')
                    if jquery:
                        attrs -= name
                        attrs |= [(QName(name), jquery)]
                    else:
                        return attrs.get(name).replace("common/js/jquery.js", 'hw/js/jquery-1.11.2.min.js')
                elif attrs.get(name) and attrs.get(name).endswith("common/js/keyboard_nav.js"):
                    #keyboard_nav.js uses function live() which was removed with jQuery 1.9. Use a fixed script here
                    return attrs.get(name) .replace("common/js/keyboard_nav.js", 'req/js/keyboard_nav.js')
            return attrs.get(name) #.replace('#trac-add-comment', '?minview')

        # Replace jQuery with a more recent version when using Trac 0.12
        if self.legacy_trac:
            stream = stream | Transformer('//head/script').attr('src', repl_jquery)
        return stream

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
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
        self.imagePath = 'chrome/hw/images/thumbtac11x11.gif'

        data = {'file_id': fileid}

        r_file = ReviewFileModel(self.env, fileid)  # This will replace rfile
        review = PeerReviewModel(self.env, r_file['review_id'])
        review.date = format_date(review['created'])
        data['review_file'] = r_file
        data['review'] = review

        # The following may raise an exception if revision can't be found
        rev = r_file['revision']
        if rev:
            rev = repos.normalize_rev(rev)
        rev_or_latest = rev or repos.youngest_rev
        node = get_existing_node(self.env, repos, r_file['path'], rev_or_latest)

        # Data for parent review if any
        if review['parent_id'] != 0:
            par_review = PeerReviewModel(self.env, review['parent_id'])  # Raises 'ResourceNotFound' on error
            par_review.date = format_date(par_review['created'])
            par_file = ReviewFileModel(self.env, get_parent_file_id(self.env, r_file, review['parent_id']))
            lines = [c.line_num for c in Comment.select_by_file_id(self.env, par_file['file_id'])]
            par_file.comments = list(set(lines))  # remove duplicates
            par_revision = par_file['revision']
            if par_revision:
                par_revision = repos.normalize_rev(par_revision)
            rev_or_latest = par_revision or repos.youngest_rev
            par_node = get_existing_node(self.env, repos, par_file['path'], rev_or_latest)
        else:
            par_review = None
            par_file = None  # TODO: there may be some error handling missing for this. Create a dummy here?
        data['par_file'] = par_file
        data['parent_review'] = par_review

        # Wether to show the full file in the browser.
        if int(r_file['line_start']) == 0:
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
            context.set_hints(reviewfile=r_file)
            context.set_hints(authname=req.authname)

            preview_data = mimeview.preview_data(context, content, len(content),
                                                 mime_type, node.created_path,
                                                 None,
                                                 annotations=['performCodeReview'])
            data['file_rendered'] = preview_data['rendered']

        # A finished review can't be changed anymore except by a manager
        data['is_finished'] = review_is_finished(self.env.config, review)
        # A user can't chnage his voting for a reviewed review
        data['review_locked'] = review_is_locked(self.env.config, review, req.authname)

        scr_data = {'peer_comments': sorted(list(set([c.line_num for c in
                                               Comment.select_by_file_id(self.env, r_file['file_id'])]))),
                    'peer_file_id': fileid,
                    'peer_review_id': r_file['review_id'],
                    'auto_preview_timeout': self.env.config.get('trac', 'auto_preview_timeout', '2.0'),
                    'form_token': req.form_token,
                    'peer_diff_style': data['style'] if 'style' in data else 'no_diff'}
        if par_review:
            scr_data['peer_parent_file_id'] = par_file['file_id']
            scr_data['peer_parent_comments'] = sorted(list(set([c.line_num for c in
                                                         Comment.select_by_file_id(self.env, par_file['file_id'])])))
        else:
            scr_data['peer_parent_file_id'] = 0  # Mark that we don't have a parent
            scr_data['peer_parent_comments'] = []

        # For comment dialogs when using Trac 0.12. Otherwise use jQuery coming with Trac
        if self.legacy_trac:
            add_javascript(req, self.env.config.get('trac', 'jquery_ui_location') or
                           'hw/js/jquery-ui-1.11.4.min.js')
            add_stylesheet(req, self.env.config.get('trac', 'jquery_ui_theme_location') or
                           'hw/css/jquery-ui-1.11.4.min.css')
        else:
            Chrome(self.env).add_jquery_ui(req)

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/diff.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_script_data(req, scr_data)
        add_javascript(req, 'common/js/auto_preview.js')
        add_javascript(req, "hw/js/peer_review_perform.js")
        add_ctxt_nav_items(req)

        return 'peerReviewPerform.html', data, None


def get_parent_file_id(env, r_file, par_review_id):

    fid = u"%s%s%s" % (r_file['path'], r_file['line_start'], r_file['line_end'])

    rfiles = ReviewFileModel.select_by_review(env, par_review_id)
    for f in rfiles:
        tmp = u"%s%s%s" % (f['path'], f['line_start'], f['line_end'])
        if tmp == fid:
            return f['file_id']
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
    data['style'] = style


def file_data_from_repo(node):

    dat = ''
    content = node.get_content()
    res = content.read()
    while res:
        dat += res
        res = content.read()
    return dat.splitlines()
