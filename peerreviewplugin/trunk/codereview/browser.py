# -*- coding: utf-8 -*-

from model import ReviewFileModel
from peerReviewCommentCallback import writeResponse
from peerReviewPerform import CommentAnnotator
from string import Template
from trac.core import Component, implements
from trac.util.html import tag
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.util.translation import _
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import add_ctxtnav, add_script, add_script_data, add_stylesheet

__author__ = 'Cinc'


# Not used
def files_with_comments(env, path, rev):
    """Return a dict with file_id as key and a comment id list as value."""
    db = env.get_read_db()
    cursor = db.cursor()
    cursor.execute("""SELECT f.file_id,
    f.revision, f.changerevision, f.review_id , c.comment_id, c.line_num 
    FROM peerreviewfile AS f 
    JOIN peerreviewcomment as c ON c.file_id = f.file_id
    WHERE f.path = %s 
    AND f.changerevision = %s
    """, (path, rev))

    for row in cursor:
        env.log.info('### %s', row)

# Not used
def select_by_path(env, path):
    """Returns a generator."""
    rf = ReviewFileModel(env)
    rf.clear_props()
    rf['path'] = path
    return rf.list_matching_objects()


class PeerReviewBrowser(Component):
    """Show information about file review status in Trac source code browser.

    [[BR]]
    The file review status is only shown when displaying a source file.

    '''Note''': This plugin may be disabled without sideeffects.
    """
    implements(IHTMLPreviewAnnotator, IRequestFilter, IRequestHandler)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.

        Always returns the request handler, even if unchanged.
        """
        return handler

    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing the Genshi
        template or mime type.

        `data` may be updated in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result
        """
        # Note that data is already filled with information about the source file, repo and what not
        path = req.args.get('path')
        rev = req.args.get('rev')

        def is_file_with_comments(env, path, rev):
            """Return a dict with file_id as key and a comment id list as value."""
            db = env.get_read_db()
            cursor = db.cursor()
            cursor.execute("""SELECT COUNT(f.file_id) 
            FROM peerreviewfile AS f 
            JOIN peerreviewcomment as c ON c.file_id = f.file_id
            WHERE f.path = %s 
            AND f.changerevision = %s
            """, (path, rev))
            return cursor.fetchone()[0] != 0

        #  We only handle the browser
        if path and req.path_info.startswith('/browser/'):
            if rev:
                is_head = 'HEAD'
            else:
                is_head = rev
            add_stylesheet(req, 'hw/css/peerreview.css')
            add_script_data(req,
                            {'peer_repo': data.get('reponame'),
                             'peer_rev': data.get('created_rev'),
                             'peer_is_head': is_head,
                             'peer_path': path,
                             'peer_status_url': req.href.peerreviewstatus(),
                             'peer_is_dir': data.get('dir', None) != None})
            add_script(req, "hw/js/peer_trac_browser.js")

        if path and req.path_info.startswith('/browser_/'):  # Deactivate code comments in browser view for now
            if is_file_with_comments(self.env, '/' + data['path'], rev):
                add_ctxtnav(req, _("Code Comments"), req.href(req.path_info, annotate='prcomment', rev=rev),
                        title=_("Show Code Comments"))
            else:
                add_ctxtnav(req, tag.span(_("Code Comments"), class_="missing"))
        return template, data, content_type

    # IRequestHandler methods

    def _create_status_tbl(self, req):
        tr_tmpl = """<tr${bg_color}>
        <td><a href="${review_href}">${review_id}</a></td><td>${chg_rev}</td><td>${hash}</td><td>${status}</td>
        </tr>
        """
        tbl_tmpl = """<h2>%s</h2><p>%s</p>
        <table class="listing peer-status-tbl">
        <thead>
            <tr>
                <th>Review</th><th>Change Revision</th><th>Hash</th><th>Status</th>
            </tr>
        </thead>
        <tbody>
            %%s
        </tbody>
        </table>
        """ % (_('Status Codereview'), _('Reviews:'))
        not_head_tmpl = "<h2>%s</h2><p>%s</p>" %\
                        (_('Status Codereview'), _('Codereview status is only available for HEAD revision.'))

        if req.args.get('peer_is_dir') == 'true':
            return ''

        if req.args.get('peer_is_head') == 'HEAD':
            return not_head_tmpl

        repo = req.args.get('peer_repo')
        path = req.args.get('peer_path', '')

        if repo:
            path = path[len(repo) + 1:]  # path starts with slash and reponame
        rev = req.args.get('peer_rev')

        res = '<div id="peer-msg" class="system-message warning">%s</div>' % _('No review for this file revision yet.')
        trows = ''
        with self.env.db_query as db:
            for row in db("SELECT review_id, changerevision, hash, status FROM peerreviewfile "
                          "WHERE path = %s AND repo = %s AND review_id != 0 "
                          "ORDER BY review_id", (path, repo)):
                #  Colorize row with current file revision. Last review wins...
                if row[1] == rev and row[3] == 'approved':
                    bg = ' style="background-color: #dfd"'
                    res = '<div id="peer-msg" class="system-message notice">' \
                          '%s</div>' % _('File is <strong>approved</strong>.')
                elif row[1] == rev and row[3] == 'disapproved':
                    bg = ' style="background-color: #ffb"'
                    res = '<div id="peer-msg" class="system-message warning">%s' \
                          '</div>' % _('File is not <strong>approved</strong>.')
                else:
                    bg = ''

                data = {'review_id': row[0],
                        'chg_rev': row[1],
                        'hash': row[2],
                        'status': row[3],
                        'review_href': req.href.peerReviewView(Review=row[0]),
                        'bg_color': bg}
                trows += Template(tr_tmpl).safe_substitute(data)
        if trows:
            return tbl_tmpl % trows + res
        else:
            return "<h2>%s</h2>" % _('Status Codereview') + res

    def match_request(self, req):
        return req.path_info == '/peerreviewstatus'

    def process_request(self, req):
        writeResponse(req, self._create_status_tbl(req))

    # IHTMLPreviewAnnotator methods

    def get_annotation_type(self):
        # Disable annotator in browser view for now
        return 'prcomment_', 'Comment', 'Review Coment'

    def get_annotation_data(self, context):


        self.log.info(context)
        self.log.info('parent: %s %s', context.parent, context.parent.resource)
        self.log.info('%s %s', context.resource, context.resource.realm)
        self.log.info('parent: %s %s', context.resource.parent, context.resource.parent.realm)
        self.log.info(context.resource.id)

        return CommentAnnotator(self.env, context, 'chrome/hw/images/thumbtac11x11.gif', 'prcomment')

    def annotate_row(self, context, row, lineno, line, comment_annotator):
        """line annotator for Perform Code Review page.

        If line has a comment, places an icon to indicate comment.
        If line is not in the rage of reviewed lines, it makes the color a light gray
        """
        # self.log.info(lineno)
        #comment_col = tag.th(style='color: red', class_='prcomment')
        #row.append(comment_col)
        comment_annotator.annotate_browser(row, lineno)
