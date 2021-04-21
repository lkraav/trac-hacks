#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016-2019 Cinc
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
import os
from codereview.changeset import get_changeset_data
from codereview.model import Comment, ReviewCommentModel, PeerReviewModel, ReviewFileModel
from codereview.repo import file_data_from_repo
from codereview.util import get_review_for_file, not_allowed_to_comment, review_is_finished, review_is_locked
from trac.core import *
from trac.mimeview import *
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.resource import ResourceNotFound
from trac.util.datefmt import format_date, to_datetime, user_time
from trac.util.html import html as tag
from trac.util.translation import _
from trac.web.chrome import add_ctxtnav, INavigationContributor, Chrome, \
                            add_link, add_stylesheet, add_script_data, add_script, web_context
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to_html
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol.api import InvalidRepository, RepositoryManager
from trac.versioncontrol.diff import diff_blocks, get_diff_options


class PeerReviewPerform(Component):
    """Perform a code review.

    [[BR]]
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
    implements(INavigationContributor, IRequestHandler, IHTMLPreviewAnnotator)

    # IHTMLPreviewAnnotator methods

    def get_annotation_type(self):
        return 'performCodeReview', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        return CommentAnnotator(self.env, context, 'chrome/hw/images/thumbtac11x11.gif')

    def annotate_row(self, context, row, lineno, line, comment_annotator):
        """line annotator for Perform Code Review page.

        If line has a comment, places an icon to indicate comment.
        If line is not in the rage of reviewed lines, it makes the color a light gray
        """
        comment_annotator.annotate(row, lineno)

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

        fileid = req.args.get('IDFile')
        if not fileid:
            raise TracError("No file ID given - unable to load page.", "File ID Error")

        r_file = ReviewFileModel(self.env, fileid)
        if not r_file.exists:
            raise ResourceNotFound("File not found.", "File ID Error")

        repos = RepositoryManager(self.env).get_repository(r_file['repo'])
        if not repos:
            raise InvalidRepository("Unable to acquire repository.", "Repository Error")

        review = PeerReviewModel(self.env, r_file['review_id'])

        review.date = user_time(req, format_date, to_datetime(review['created']))
        review.html_notes = format_to_html(self.env, web_context(req), review['notes'])

        data = {'file_id': fileid,
                'review_file': r_file,
                'review': review,
                'fullrange': True if int(r_file['line_start']) == 0 else False,
                'node': self.get_current_file_node(r_file, repos)
                }

        # Add parent data if any
        data.update(self.parent_data(req, review, r_file, repos))

        # Mark if this is a changeset review
        changeset = get_changeset_data(self.env, review['review_id'])
        data.update({'changeset': changeset[1],
                     'repo': changeset[0]})

        if data['changeset']:
            # This simulates a parent review by creating some temporary data
            # not backed by the database. If it's a new file, parent information is omitted
            data.update(self.changeset_data(data, r_file, repos))

        if data['parent_review']:
            # A followup review with diff viewer
            data.update(create_diff_data(req, data))
        else:
            data.update(self.preview_for_file(req, r_file, data['node']))

        # A finished review can't be changed anymore except by a manager
        data['is_finished'] = review_is_finished(self.env.config, review)
        # A user can't chnage his voting for a reviewed review
        data['review_locked'] = review_is_locked(self.env.config, review, req.authname)
        data['not_allowed'] = not_allowed_to_comment(self.env, review, req.perm, req.authname)

        Chrome(self.env).add_jquery_ui(req)

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/diff.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_script_data(req, self.create_script_data(req, data))
        add_script(req, 'common/js/auto_preview.js')
        add_script(req, "hw/js/peer_review_perform.js")
        self.add_ctxt_nav_items(req, review, r_file)

        if hasattr(Chrome, 'jenv'):
            return 'peerreview_perform_jinja.html', data
        else:
            return 'peerreview_perform.html', data, None

    def add_ctxt_nav_items(self, req, review, r_file):
        rev_files = ["%s:%s" % (item['path'], item['file_id'])
                     for item in ReviewFileModel.select_by_review(self.env, review['review_id'])]
        idx = rev_files.index("%s:%s" % (r_file['path'], r_file['file_id']))
        if not idx:
            add_ctxtnav(req, _("Previous File"))
        else:
            path, file_id = rev_files[idx - 1].split(':')
            path = os.path.basename(path)
            add_ctxtnav(req, _("Previous File"), req.href.peerReviewPerform(IDFile=file_id), title=_("File %s") % path)
        if idx == len(rev_files)-1:
            add_ctxtnav(req, _("Next File"))
        else:
            path, file_id = rev_files[idx + 1].split(':')
            path = os.path.basename(path)
            add_ctxtnav(req, _("Next File"), req.href.peerReviewPerform(IDFile=file_id), title=_("File %s") % path)

    def create_script_data(self, req, data):
        r_file = data['review_file']
        scr_data = {'peer_comments': sorted(list(set([c.line_num for c in
                                                      Comment.select_by_file_id(self.env, r_file['file_id'])]))),
                    'peer_file_id': r_file['file_id'],
                    'peer_review_id': r_file['review_id'],
                    'auto_preview_timeout': self.env.config.get('trac', 'auto_preview_timeout', '2.0'),
                    'form_token': req.form_token,
                    'peer_diff_style': data['style'] if 'style' in data else 'no_diff'}
        if data['parent_review']:
            scr_data['peer_parent_file_id'] = data['par_file']['file_id']
            scr_data['peer_parent_comments'] = sorted(list(set([c.line_num for c in
                                                                Comment.select_by_file_id(self.env, data['par_file']['file_id'])])))
        else:
            scr_data['peer_parent_file_id'] = 0  # Mark that we don't have a parent
            scr_data['peer_parent_comments'] = []
        return scr_data

    def preview_for_file(self, req, r_file, node):
        # Generate HTML preview - this code take from Trac - refer to their documentation
        mime_type = node.content_type
        self.env.log.debug("mime_type taken from node.content_type: %s" % (mime_type,))
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = get_mimetype(node.name) or mime_type or 'text/plain'

        mimeview = Mimeview(self.env)
        content = node.get_content().read(mimeview.max_preview_size)  # We get the raw data without keyword substitution

        context = web_context(req, 'rfile', r_file['file_id'])
        context.set_hints(reviewfile=r_file)

        self.env.log.debug("Creating preview data for %s with mime_type = %s" % (node.created_path, mime_type))
        preview_data = mimeview.preview_data(context, content, len(content),
                                             mime_type, node.created_path,
                                             None,
                                             annotations=['performCodeReview'])

        # TODO: use in template 'preview.rendered' instead similar to preview_file.html
        return {'file_rendered': preview_data['rendered'],
                'preview': preview_data
                }

    def get_current_file_node(self, r_file, repos):
        # The following may raise an exception if revision can't be found
        rev = r_file['changerevision']  # last change for the given file
        if rev:
            rev = repos.normalize_rev(rev)
        rev_or_latest = rev or repos.youngest_rev

        if repos.has_node(r_file['path'], rev_or_latest):
            node = get_existing_node(self.env, repos, r_file['path'], rev_or_latest)
        else:
            self.log.info("No Node for file '%s' in revision %s. Using repository revision %s instead.",
                          r_file['path'], rev_or_latest, repos.youngest_rev)
            node = get_existing_node(self.env, repos, r_file['path'], repos.youngest_rev)
        return node

    def parent_data(self, req, review, r_file, repos):
        """Create a dictionary with data about parent review.

        The dictionary is used to update the 'data' dict.

        @param review: PeerReviewModel object representing the current review
        @param r_file: ReviewFileModel object representing the current file
        @param repos: Trac Repository holding the file
        @return: dict with additional data for the 'data' dict
        """
        par_review = None
        par_file = None
        par_node = None
        if review['parent_id'] != 0:
            par_file_id = get_parent_file_id(self.env, r_file, review['parent_id'])
            # If this is a file added to the review we don't have a parent file
            if par_file_id:
                par_review = PeerReviewModel(self.env, review['parent_id'])  # Raises 'ResourceNotFound' on error
                par_review.date = user_time(req, format_date, to_datetime(par_review['created']))
                par_file = ReviewFileModel(self.env, par_file_id)
                lines = [c.line_num for c in Comment.select_by_file_id(self.env, par_file['file_id'])]
                par_file.comments = list(set(lines))  # remove duplicates
                par_revision = par_file['revision']
                if par_revision:
                    par_revision = repos.normalize_rev(par_revision)
                rev_or_latest = par_revision or repos.youngest_rev
                par_node = get_existing_node(self.env, repos, par_file['path'], rev_or_latest)

        return {'par_file': par_file,
                'parent_review': par_review,
                'par_node': par_node
                }

    def changeset_data(self, data, r_file, repos):
        """Create a dictionary with data about previous file revision for changeset review.

        The dictionary is used to update the 'data' dict.

        @param review: PeerReviewModel object representing the current review
        @param r_file: ReviewFileModel object representing the current file
        @param repos: Trac Repository holding the file
        @return: dict with additional data for the 'data' dict
        """
        # Just to keep the template happy. May possibly be removed later
        par_review = PeerReviewModel(self.env)

        prev = data['node'].get_previous()

        if not prev:
            # This file was added
            return {'par_file': None,
                    'parent_review': None,
                    'par_node': None
                    }

        # Create a temp file object for holding the data for the template
        par_file = ReviewFileModel(self.env)
        rev = str(prev[1])
        rev_or_latest = prev[1] or repos.youngest_rev
        par_file['path'] = prev[0]
        par_file['changerevision'] = rev
        par_file['revision'] = rev
        par_file['line_start'] = 0
        par_file['repo'] = r_file['repo']
        par_file.comments = []
        par_node = get_existing_node(self.env, repos, par_file['path'], rev_or_latest)

        return {'par_file': par_file,
                'parent_review': par_review,
                'par_node': par_node
                }


class CommentAnnotator(object):
    """Annotator object which handles comments in source view."""
    def __init__(self, env, context, imagepath, name=None):
        self.env = env
        self.context = context
        self.imagepath = imagepath

        # We use the annotator on the browser page
        if name == 'prcomment':
            self.prep_browser(context)
        else:
            self. prep_peer(context)

    def prep_peer(self, context):
        authname = context.req.authname
        perm = context.req.perm
        fresource = context.resource  # This is an 'peerreviewfile' realm
        review = get_review_for_file(self.env, fresource.id)
        # Is it allowed to comment on the file?
        if review_is_finished(self.env.config, review):
            is_locked = True
        else:
            is_locked = review_is_locked(self.env.config, review, authname)

        # Don't let users comment who are not part of this review
        if not_allowed_to_comment(self.env, review, perm, authname):
            is_locked = True

        self.data = [[c['line_num'] for c in ReviewCommentModel.select_by_file_id(self.env, fresource.id)], review, is_locked]

    def prep_browser(self, context):
        def comments_for_file(env, path, rev):
            with env.db_query as db:
                cursor = db.cursor()
                cursor.execute("""SELECT c.line_num, c.comment_id, f.file_id,
                f.review_id
                FROM peerreviewfile AS f
                JOIN peerreviewcomment as c ON c.file_id = f.file_id
                WHERE f.path = %s
                AND f.changerevision = %s
                """, (path, rev))

                d = {}
                file_id = 0
                for row in cursor:
                    d[row[0]] = row[2]
                    file_id = row[2]
                return d, file_id

        self.path = '/' + context.resource.id
        self.rev = context.resource.version
        self.data, fileid = comments_for_file(self.env, self.path, self.rev)

        scr_data = {'peer_comments': [],  # sorted(list(set([c.line_num for c in
                    #                                  Comment.select_by_file_id(self.env, r_file['file_id'])]))),
                    'peer_file_id': fileid,
                    #'peer_review_id': r_file['review_id'],
                    'auto_preview_timeout': self.env.config.get('trac', 'auto_preview_timeout', '2.0'),
                    'form_token': context.req.form_token,
                    'baseUrl': context.req.href.peerReviewCommentCallback(),
                    'peer_diff_style': 'no_diff'}  # data['style'] if 'style' in data else 'no_diff'}

        scr_data['peer_parent_file_id'] = 0  # Mark that we don't have a parent
        scr_data['peer_parent_comments'] = []

        add_script_data(context.req, scr_data)
        #add_stylesheet(context.req, 'common/css/code.css')
        #add_stylesheet(context.req, 'common/css/diff.css')
        chrome = Chrome(self.env)
        chrome.add_auto_preview(context.req)
        chrome.add_jquery_ui(context.req)
        add_stylesheet(context.req, 'hw/css/peerreview.css')
        add_script(context.req, "hw/js/peer_review_perform.js")

    def annotate(self, row, lineno):
        """line annotator for Perform Code Review page.

        If line has a comment, places an icon to indicate comment.
        If line is not in the rage of reviewed lines, it makes the color a light gray
        """
        r_file = self.context.get_hint('reviewfile')
        file_id = self.context.resource.id
        data = self.data
        if (lineno <= int(r_file['line_end']) and lineno >= int(r_file['line_start'])) or int(r_file['line_start']) == 0:
            # If there is a comment on this line
            lines = data[0]
            # review = data[1]
            if lineno in lines:
                return row.append(tag.th(id='L%s' % lineno)(tag.a(tag.img(src='%s' % self.imagepath) + ' ' + str(lineno),
                                                                  href='javascript:getComments(%s, %s)' %
                                                                       (lineno, file_id))))
            if not data[2]:
                return row.append(tag.th(id='L%s' % lineno)(tag.a(lineno, href='javascript:addComment(%s, %s, -1)'
                                                                               % (lineno, file_id))))
            else:
                return row.append(tag.th(str(lineno), id='L%s' % lineno))

        # color line numbers outside range light gray
        row.append(tag.th(id='L%s' % lineno)(tag.font(lineno, color='#CCCCCC')))

    def annotate_browser(self, row, lineno):
        if lineno in self.data:
            row.append(tag.th(id='C%s' % lineno)(tag.a(tag.img(src=self.context.req.href(self.imagepath)),
                                                               href='javascript:getComments(%s, %s)' %
                                                                    (lineno, self.data[lineno]))))
        else:
            comment_col = tag.th(class_='prcomment')
            row.append(comment_col)


def get_parent_file_id(env, r_file, par_review_id):

    fid = u"%s%s%s" % (r_file['path'], r_file['line_start'], r_file['line_end'])

    rfiles = ReviewFileModel.select_by_review(env, par_review_id)
    for f in rfiles:
        tmp = u"%s%s%s" % (f['path'], f['line_start'], f['line_end'])
        if tmp == fid:
            return f['file_id']
    return 0


def create_diff_data(req, data):
    style, options, diff_data = get_diff_options(req)

    node = data['node']
    par_node = data['par_node']

    old = file_data_from_repo(par_node)
    new = file_data_from_repo(node)

    if diff_data['options']['contextall']:
        context = None
    else:
        context = diff_data['options']['contextlines']

    diff = diff_blocks(old, new, context=context,
                       ignore_blank_lines=diff_data['options']['ignoreblanklines'],
                       ignore_case=diff_data['options']['ignorecase'],
                       ignore_space_changes=diff_data['options']['ignorewhitespace'])

    changes = []
    file_href = req.href.browser(data['review_file']['repo'],
                                 data['review_file']['path'],
                                 rev=data['review_file']['changerevision'])
    par_rev = par_node.rev if par_node else ''
    # This is shown in the header of the table
    par_rev_info = " (Review #%s)" % data['parent_review']['review_id'] \
        if data['parent_review'].exists else ''
    par_href = req.href.browser(data['par_file']['repo'],
                                data['par_file']['path'],
                                rev=data['par_file']['changerevision'])
    info = {'diffs': diff,
            'new': {'path': node.path,
                    'rev': "%s (Review #%s)" % (node.rev, data['review']['review_id']),
                    'shortrev': node.rev,
                    'href': file_href
                    },
            'old': {'path': par_node.path if par_node else '',
                    'rev': "%s%s" % (par_rev, par_rev_info),
                    'shortrev': par_rev,
                    'href': par_href
                    },
            'props': []}
    changes.append(info)
    return {'changes': changes,
            'diff': diff_data,  # {'style': 'inline', 'options': []},
            'longcol': 'Revision',
            'shortcol': 'r',
            'style': style,
            'nochanges': True if old == new else False
            }
