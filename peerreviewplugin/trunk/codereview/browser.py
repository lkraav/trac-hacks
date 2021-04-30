# -*- coding: utf-8 -*-

from .model import ReviewFileModel
from .peerReviewCommentCallback import writeJSONResponse, writeResponse
from .peerReviewPerform import CommentAnnotator
from .repo import hash_from_file_node
from string import Template
from trac.core import Component, implements
from trac.util.html import tag
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.util.translation import _
from trac.versioncontrol import RepositoryManager, ResourceNotFound
from trac.versioncontrol.web_ui.util import get_existing_node
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import add_ctxtnav, add_script, add_script_data, add_stylesheet

__author__ = 'Cinc'


# Not used
def files_with_comments(env, path, rev):
    """Return a dict with file_id as key and a comment id list as value."""
    with env.sb_query as db:
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

    The file review status is only shown when displaying a source file.

    '''Note''': This plugin may be disabled without side effects.
    """
    implements(IHTMLPreviewAnnotator, IRequestFilter, IRequestHandler)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        """Always returns the request handler, even if unchanged."""
        return handler

    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need;
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
            with env.db_query as db:
                cursor = db.cursor()
                cursor.execute("""SELECT COUNT(f.file_id)
                FROM peerreviewfile AS f
                JOIN peerreviewcomment as c ON c.file_id = f.file_id
                WHERE f.path = %s
                AND f.changerevision = %s
                """, (path, rev))
                return cursor.fetchone()[0] != 0

        #  We only handle the browser
        split_path = req.path_info.split('/')
        if path and req.path_info.startswith('/browser/') and data:
            add_stylesheet(req, 'hw/css/peerreview.css')
            add_script_data(req,
                            {'peer_repo': data.get('reponame', ''),
                             'peer_rev': data.get('created_rev', ''),
                             'peer_is_head': 0 if rev else 1,
                             'peer_path': path,
                             'peer_status_url': req.href.peerreviewstatus(),
                             # Index page has no data['dir'] if only the repoindex page is shown and
                             # no default repo is defined
                             'peer_is_dir': data.get('dir', None) != None or len(split_path) == 2,
                             'tacUrl': req.href.chrome('/hw/images/thumbtac11x11.gif')})
            add_script(req, "hw/js/peer_trac_browser.js")
            # add_script(req, "hw/js/peer_review_perform.js")

        # Deactivate code comments in browser view for now
        if path and req.path_info.startswith('/browser_/'):
            if is_file_with_comments(self.env, '/' + data['path'], data.get('created_rev')):
                add_ctxtnav(req, _("Code Comments"), req.href(req.path_info, annotate='prcomment', rev=rev),
                            title=_("Show Code Comments"))
            else:
                add_ctxtnav(req, tag.span(_("Code Comments"), class_="missing"))
        return template, data, content_type

    # IRequestHandler methods

    def _create_status_tbl(self, req):
        tr_tmpl = """<tr${bg_color}>
        <td><a href="${file_href}">${file_id}</a></td>
        <td><a href="${review_href}">${review_id}</a></td>
        <td>${chg_rev}</td><td>${hash}</td><td>${status}</td>
        </tr>
        """
        tbl_tmpl = """<h3>%s</h3>
        <table class="listing peer-status-tbl">
        <thead>
            <tr>
                <th>File ID</th><th>Review</th><th>Change Revision</th><th>Hash</th><th>Status</th>
            </tr>
        </thead>
        <tbody>
            %%s
        </tbody>
        </table>
        """ % (_('Status Codereview'),)
        not_head_tmpl = "<h3>%s</h3><p>%s</p>" %\
                        (_('Status Codereview'), _('Codereview status is only available for HEAD revision.'))

        if req.args.get('peer_is_dir') == 'true':
            return ''

        repo = req.args.get('peer_repo')
        path = req.args.get('peer_path', '')

        if repo:
            # path starts with slash and reponame, like /reponame/my/path/to/file.txt
            # All path information in the database is with leading '/'.
            path = path[len(repo) + 1:]
        rev = req.args.get('peer_rev')

        # if req.args.getint('peer_is_head') == 0:
        #     return not_head_tmpl

        res = '<div id="peer-msg" class="system-message warning">%s</div>' %\
              _('No review for this file revision yet.')
        trows = ''
        with self.env.db_query as db:
            for row in db("SELECT review_id, changerevision, hash, status, file_id FROM peerreviewfile "
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
                        'file_id': row[4],
                        'file_href': req.href.peerreviewperform(IDFile=row[4]),
                        'review_href': req.href.peerreviewview(row[0]),
                        'bg_color': bg}
                trows += Template(tr_tmpl).safe_substitute(data)
        if trows:
            return tbl_tmpl % trows  #  + res
        else:
            return "<h3>%s</h3>" % _('Status Codereview') + res

    def match_request(self, req):
        return req.path_info == '/peerreviewstatus'

    def process_request(self, req):
        tr = """<tr><td colspan="2"><strong>{label}</strong>&nbsp;{hash}</td></tr>"""
        data = {'statushtml': self._create_status_tbl(req),
                'hashhtml': tr.format(label="Hash:", hash=self.get_hash_for_file(req))}
        writeJSONResponse(req, data)

    def get_hash_for_file(self, req):
        """Return the hash for the currently viewed file.

        :param req: Request object. The arg dict holds file information like path, revision, ...
        :return file hash string or an empty string. The hash is in hex
        """
        if req.args.get('peer_dir') == 'true':
            return None

        reponame = req.args.get('peer_repo')
        path = req.args.get('peer_path', '')
        if reponame:
            # path starts with slash and reponame, like /reponame/my/path/to/file.txt
            # All path information in the database is with leading '/'.
            path = path[len(reponame) + 1:]
        rev = req.args.get('peer_rev')
        node = None
        repos = RepositoryManager(self.env).get_repository(reponame)

        try:
            node = get_existing_node(req, repos, path, rev)
        except ResourceNotFound:
            # The file may be a SVN copy. If so the revision is the one from the
            # source file, the path is the current (not source) path.
            # Search the history. This probably breaks when several copies are made.
            src_path, src_rev, chnge = range(3)
            for item in repos.get_path_history(path, limit=1):  # this is a generator
                if item[chnge] in ('copy', 'move'):
                    node = get_existing_node(req, repos, item[src_path], item[src_rev])
                    break
        if node:
            return hash_from_file_node(node)
        else:
            return ''

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
        """
        # self.log.info(lineno)
        #comment_col = tag.th(style='color: red', class_='prcomment')
        #row.append(comment_col)
        comment_annotator.annotate_browser(row, lineno)
