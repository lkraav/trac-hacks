#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

from __future__ import generators
import re

from trac import util
from trac.core import *
from trac.mimeview import *
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.resource import ResourceNotFound
from trac.util import embedded_numbers
from trac.util.html import html as tag
from trac.util.translation import _
from trac.versioncontrol.api import NoSuchChangeset, NoSuchNode, RepositoryManager
from trac.versioncontrol.web_ui.util import *
from trac.web import IRequestHandler, RequestDone
from trac.web.chrome import add_link, add_warning
from trac.wiki import wiki_to_html

IMG_RE = re.compile(r"\.(gif|jpg|jpeg|png)(\?.*)?$", re.IGNORECASE)
CHUNK_SIZE = 4096
DIGITS = re.compile(r'[0-9]+')


def _natural_order(x, y):
    """Comparison function for natural order sorting based on
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/214202."""
    nx = ny = 0
    while True:
        a = DIGITS.search(x, nx)
        b = DIGITS.search(y, ny)
        if None in (a, b):
            return cmp(x[nx:], y[ny:])
        r = (cmp(x[nx:a.start()], y[ny:b.start()]) or
             cmp(int(x[a.start():a.end()]), int(y[b.start():b.end()])))
        if r:
            return r
        nx, ny = a.end(), b.end()


class PeerReviewBrowser(Component):
    """Provide a repository browser for file selection for code reviews.

    [[BR]]
    Component used for browsing the repository for files.

    '''Note:''' do not disable otherwise no files may be selected for a review.
    """

    implements(IRequestHandler, IHTMLPreviewAnnotator)

    # ITextAnnotator methods
    def get_annotation_type(self):
        return 'lineno', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        return None

    def annotate_row(self, context, row, lineno, line, data):
        row.append(tag.th(id='L%s' % lineno)(
            tag.a(lineno, href='javascript:setLineNum(%s)' % lineno)
        ))

    # IRequestHandler methods

    def match_request(self, req):
        import re
        match = re.match(r'/(peerReviewBrowser|file|adminrepobrowser)(?:(/.*))?', req.path_info)
        if match:
            req.args['path'] = match.group(2) or '/'
            if match.group(1) == 'file':
                # FIXME: This should be a permanent redirect
                req.redirect(self.env.href.peerReviewBrowser(req.args.get('path'),
                                                   rev=req.args.get('rev'),
                                                   format=req.args.get('format')))
            elif match.group(1) == 'adminrepobrowser':
                # This one is for the browser on admin pages
                req.args['is_admin_browser'] = True
            return True

    def process_request(self, req):

        path = req.args.get('path', '/')
        rev = req.args.get('rev')
        cur_repo = req.args.get('repo', '')
        is_admin_browser = req.args.get('is_admin_browser', False)  # Set when we come from the file admin page
        context = Context.from_request(req)
        # Depending on from where we are coming we have to preprocess in match_request() thus use different paths
        browse_url_base = 'adminrepobrowser' if is_admin_browser else 'peerReviewBrowser'
        template_file = 'admin_repobrowser.html' if is_admin_browser else 'repobrowser.html'

        # display_rev = lambda rev: rev

        data = {'browse_url': self.env.href(browse_url_base),
                'is_admin_browser': is_admin_browser
                }

        repoman = RepositoryManager(self.env)

        all_repos = repoman.get_all_repositories()
        if not all_repos:
            data['norepo'] = _("No source repository available.")
            return 'repobrowser.html', data, None

        # Repositories may be hidden
        filtered_repos = {}
        for rname, info in all_repos.iteritems():
            try:
                if not info['hidden'] == u'1':
                    filtered_repos[rname] = info
            except KeyError:
                # This is the default repo
                filtered_repos[rname] = info

        if not filtered_repos:
            data['norepo'] = _("No source repository available.")
            return 'repobrowser.html', data, None

        data['all_repos'] = filtered_repos

        # if not req.args.get('repo', None): won't work here because of default repo name ''
        if req.args.get('repo', None) == None:
            # We open the page for the first time
            data['show_repo_idx'] = True
            return template_file, data, None

        if cur_repo not in data['all_repos']:
            data['repo_gone'] = cur_repo if cur_repo else '(default)'
            data['show_repo_idx'] = True
            return template_file, data, None

        # Find node for the requested repo/path/rev
        repo = repoman.get_repository(cur_repo)
        if repo:
            try:
                node, display_rev, context = get_node_from_repo(req, repo, path, rev)
            except NoSuchChangeset as e:
                data['norepo'] = _(e.message)
                return template_file, data, None
            except ResourceNotFound as e:  # NoSuchNode is converted to this exception by Trac
                data['nonode'] = e.message
                node = None
                display_rev = rev
        else:
            data['norepo'] = _("No source repository available.")
            return template_file, data, None

        hidden_properties = [p.strip() for p
                             in self.config.get('browser', 'hide_properties',
                                                'svk:merge').split(',')]

        path_links = self.get_path_links_CRB(self.env.href, browse_url_base, path, rev, cur_repo)
        if len(path_links) > 1:
            add_link(req, 'up', path_links[-2]['href'], 'Parent directory')

        if node:
            props = [{'name': util.escape(name), 'value': util.escape(value)}
                     for name, value in node.get_properties().items()
                     if name not in hidden_properties]
        else:
            props = []
        data.update({
            'path': path,
            'rev': node.rev if node else rev,
            'stickyrev': rev,
            'context': context,
            'repo': repo,
            'reponame': repo.reponame,  # for included path_links.html
            'revision': rev or repo.get_youngest_rev(),
            'props': props,
            'log_href': util.escape(self.env.href.log(path, rev=rev or None)),
            'path_links': path_links,
            'dir': node and node.isdir and self._render_directory(req, repo, node, rev, cur_repo),
            'file': node and node.isfile and self._render_file(req, context, repo, node, rev, cur_repo),
            'display_rev': display_rev,
            'wiki_format_messages': self.config['changeset'].getbool('wiki_format_messages'),
        })
        return template_file, data, None

    # Internal methods

    def get_path_links_CRB(self, href, browse_url_base, fullpath, rev, repo):
        path = '/'
        links = [{'name': 'Repository Index',
                  'href': href(browse_url_base, path, rev=rev)}]

        for part in [p for p in fullpath.split('/') if p]:
            path += part + '/'
            links.append({
                'name': part,
                'href': href(browse_url_base, path, rev=rev, repo=repo)
                })
        return links

    def _render_directory(self, req, repos, node, rev=None, repo=''):
        req.perm.assert_permission('BROWSER_VIEW')

        order = req.args.get('order', 'name').lower()
        desc = req.args.has_key('desc')

        info = []

        if order == 'date':
            def file_order(a):
                return changes[a.rev].date
        elif order == 'size':
            def file_order(a):
                return (a.content_length,
                        embedded_numbers(a.name.lower()))
        else:
            def file_order(a):
                return embedded_numbers(a.name.lower())

        dir_order = desc and 1 or -1

        def browse_order(a):
            return a.isdir and dir_order or 0, file_order(a)

        browse_url = "peerReviewBrowser" if not req.args.get('is_admin_browser', False) else "adminrepobrowser"
        for entry in node.get_entries():
            if entry.can_view(req.perm):
                info.append({
                    'name': entry.name,
                    'fullpath': entry.path,
                    'is_dir': int(entry.isdir),
                    'content_length': entry.content_length,
                    'size': util.pretty_size(entry.content_length),
                    'rev': entry.created_rev,
                    'permission': 1,  # FIXME
                    'log_href': util.escape(self.env.href.log(repo, entry.path, rev=rev)),
                    'browser_href': self.env.href(browse_url, entry.path, rev=rev, repo=repo)
                    })

        changes = get_changes(repos, [i['rev'] for i in info])

        def cmp_func(a, b):
            dir_cmp = (a['is_dir'] and -1 or 0) + (b['is_dir'] and 1 or 0)
            if dir_cmp:
                return dir_cmp
            neg = desc and -1 or 1
            if order == 'date':
                return neg * cmp(changes[b['rev']]['date_seconds'],
                                 changes[a['rev']]['date_seconds'])
            elif order == 'size':
                return neg * cmp(a['content_length'], b['content_length'])
            else:
                return neg * _natural_order(a['name'].lower(),
                                            b['name'].lower())
        info.sort(cmp_func)

        return {'order': order, 'desc': desc and 1 or None,
                'items': info, 'changes': changes}

    def _render_file(self, req, context, repos, node, rev=None, repo=''):
        req.perm(context.resource).require('FILE_VIEW')

        changeset = repos.get_changeset(node.rev)

        mime_type = node.content_type
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = get_mimetype(node.name) or mime_type or 'text/plain'

        # We don't have to guess if the charset is specified in the
        # svn:mime-type property
        ctpos = mime_type.find('charset=')
        if ctpos >= 0:
            charset = mime_type[ctpos + 8:]
        else:
            charset = None

        content = node.get_content()
        chunk = content.read(CHUNK_SIZE)

        format = req.args.get('format')
        if format in ('raw', 'txt'):
            req.send_response(200)
            req.send_header('Content-Type',
                            format == 'txt' and 'text/plain' or mime_type)
            req.send_header('Content-Length', node.content_length)
            req.send_header('Last-Modified', util.http_date(node.last_modified))
            req.end_headers()

            while 1:
                if not chunk:
                    raise RequestDone
                req.write(chunk)
                chunk = content.read(CHUNK_SIZE)
        else:
            # Generate HTML preview
            mimeview = Mimeview(self.env)

            # The changeset corresponding to the last change on `node`
            # is more interesting than the `rev` changeset.
            changeset = repos.get_changeset(node.rev)

            # add ''Plain Text'' alternate link if needed
            if not is_binary(chunk) and mime_type != 'text/plain':
                plain_href = req.href.browser(node.path, rev=rev, format='txt')
                add_link(req, 'alternate', plain_href, 'Plain Text',
                         'text/plain')

            raw_href = self.env.href.peerReviewBrowser(node.path, rev=rev and node.rev, repo=repo,
                                             format='raw')
            preview_data = mimeview.preview_data(context, node.get_content(),
                                                    node.get_content_length(),
                                                    mime_type, node.created_path,
                                                    raw_href,
                                                    annotations=['lineno'])

            add_link(req, 'alternate', raw_href, 'Original Format', mime_type)

            return {
                'changeset': changeset,
                'size': node.content_length,
                'preview': preview_data['rendered'],
                'max_file_size_reached': preview_data['max_file_size_reached'],
                'max_file_size': preview_data['max_file_size'],
                'annotate': False,
                'rev': node.rev,
                'changeset_href': util.escape(self.env.href.changeset(node.rev)),
                'date': util.format_datetime(changeset.date),
                'age': util.pretty_timedelta(changeset.date),
                'author': changeset.author or 'anonymous',
                'message': wiki_to_html(changeset.message or '--', self.env, req,
                                        escape_newlines=True)
            }


def get_node_from_repo(req, repos, path, rev):

    context = Context.from_request(req)

    if rev:
        rev = repos.normalize_rev(rev)
    # If `rev` is `None`, we'll try to reuse `None` consistently,
    # as a special shortcut to the latest revision.
    rev_or_latest = rev or repos.youngest_rev
    node = get_existing_node(req, repos, path, rev_or_latest)

    context = context(repos.resource.child('source', path,
                                           version=rev_or_latest))
    display_rev = repos.display_rev

    return node, display_rev, context
