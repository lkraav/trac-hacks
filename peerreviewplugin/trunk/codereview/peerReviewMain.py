#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016 Cinc-th
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#
# Provides functionality for main page
# Works with peerReviewMain.html

import itertools
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.resource import IResourceManager, Resource, ResourceNotFound
from trac.util import as_int, format_date
from trac.util.html import Markup, html as tag
from trac.util.translation import _
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_ctxtnav
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to
from model import ReviewCommentModel, ReviewDataModel, ReviewFileModel, PeerReviewModel, PeerReviewerModel
from util import review_is_finished


def web_context_compat(req, resource=None, id=False, version=False, parent=False,
                absurls=False):
    """Create a rendering context from a request.

    The `perm` and `href` properties of the context will be initialized
    from the corresponding properties of the request object.

    >>> from trac.test import Mock, MockPerm
    >>> req = Mock(href=Mock(), perm=MockPerm())
    >>> context = web_context(req)
    >>> context.href is req.href
    True
    >>> context.perm is req.perm
    True

    :param      req: the HTTP request object
    :param resource: the `Resource` object or realm
    :param       id: the resource identifier
    :param  version: the resource version
    :param  absurls: whether URLs generated by the ``href`` object should
                     be absolute (including the protocol scheme and host
                     name)
    :return: a new rendering context
    :rtype: `RenderingContext`

    :since: version 1.0
    """
    from trac.mimeview.api import Context
    if req:
        href = req.abs_href if absurls else req.href
        perm = req.perm
    else:
        href = None
        perm = None
    self = Context(Resource(resource, id=id, version=version,
                            parent=parent), href=href, perm=perm)
    self.req = req
    return self

try:
    from trac.web.chrome import web_context
except ImportError:
    web_context = web_context_compat

def add_ctxt_nav_items(req):
    add_ctxtnav(req, _("My Code Reviews"), "peerReviewMain", title=_("My Code Reviews"))
    add_ctxtnav(req, _("Create a Code Review"), "peerReviewNew", title=_("Create a Code review"))
    add_ctxtnav(req, _("Report"), "peerreviewreport", title=_("Show Codereview Reports"))
    add_ctxtnav(req, _("Search Code Reviews"), "peerReviewSearch", _("Search Code Reviews"))


class PeerReviewMain(Component):
    """Show overview page for code reviews."""
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
               IPermissionRequestor, IResourceManager)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            yield ('mainnav', 'peerReviewMain',
                   Markup('<a href="%s">Peer Review</a>') % req.href.peerReviewMain())

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return [
            ('CODE_REVIEW_VIEW',['PEERREVIEWFILE_VIEW', 'PEERREVIEW_VIEW']),  # Allow viewing of realm so reports show
            ('CODE_REVIEW_DEV', ['CODE_REVIEW_VIEW']),                        # results.
            ('CODE_REVIEW_MGR', ['CODE_REVIEW_DEV', 'PEERREVIEWFILE_VIEW'])
        ]

    # IRequestHandler methods

    def send_preview(self, req):
        # Taken from WikiRender component in wiki/web_api.py
        # Allow all POST requests (with a valid __FORM_TOKEN, ensuring that
        # the client has at least some permission). Additionally, allow GET
        # requests from TRAC_ADMIN for testing purposes.
        if req.method != 'POST':
            req.perm.require('TRAC_ADMIN')
        realm = req.args.get('realm', 'wiki')
        id = req.args.get('id')
        version = as_int(req.args.get('version'), None)
        text = req.args.get('text', '')
        flavor = req.args.get('flavor')
        options = {}
        if 'escape_newlines' in req.args:
            options['escape_newlines'] = bool(int(req.args['escape_newlines']
                                                  or 0))
        if 'shorten' in req.args:
            options['shorten'] = bool(int(req.args['shorten'] or 0))
        resource = Resource(realm, id=id, version=version)
        context = web_context(req, resource)
        rendered = format_to(self.env, flavor, context, text, **options)
        req.send(rendered.encode('utf-8'))


    def match_request(self, req):
        return req.path_info == '/peerReviewMain' or req.path_info == "/preview_render"

    def process_request(self, req):
        req.perm.require('CODE_REVIEW_DEV')

        if req.path_info == "/preview_render":
            self.send_preview(req)

        data = {}
        # test whether this user is a manager or not
        if 'CODE_REVIEW_MGR' in req.perm:
            data['manager'] = True
        else:
            data['manager'] = False

        # User requests an update
        data['allassigned'] = req.args.get('allassigned')
        data['allcreated'] = req.args.get('allcreated')

        r_tmpl = PeerReviewModel(self.env)
        r_tmpl.clear_props()
        if data['allcreated']:
            all_reviews = list(r_tmpl.list_matching_objects())
        else:
            all_reviews = [rev for rev in r_tmpl.list_matching_objects() if rev['status'] != "closed"]

        # We need this for displaying information about comments
        comments = ReviewCommentModel.comments_by_file_id(self.env)
        my_comment_data = ReviewDataModel.comments_for_owner(self.env, req.authname)

        # Add files
        files = ReviewFileModel.file_dict_by_review(self.env)

        # fill the table of currently open reviews
        myreviews = []
        assigned_to_me =[]
        manager_reviews = []

        for rev in all_reviews:
            # Reviews created by me
            if rev['owner'] == req.authname:
                rev.date = format_date(rev['created'])
                rev.rev_files = files[rev['review_id']]
                # Prepare number of comments for a review
                rev.num_comments = 0
                for f in rev.rev_files:
                    if f['file_id'] in comments:
                        rev.num_comments += len(comments[f['file_id']])
                rev.num_notread = rev.num_comments - len([c_id for c_id, r, t, dat in my_comment_data if t == 'read'
                                                          and r == rev['review_id']])
                myreviews.append(rev)

        r_tmpl = PeerReviewerModel(self.env)
        r_tmpl.clear_props()
        r_tmpl['reviewer'] = req.authname

        if data['allassigned']:
            # Don't filter list here
            reviewer = list(r_tmpl.list_matching_objects())
        else:
            reviewer = [rev for rev in r_tmpl.list_matching_objects() if rev['status'] != "reviewed"]

        # All reviews assigned to me
        for item in reviewer:
            rev = PeerReviewModel(self.env, item['review_id'])
            if not review_is_finished(self.env.config, rev):
                rev.reviewer = item
                rev.date = format_date(rev['created'])
                rev.rev_files = files[rev['review_id']]
                # Prepare number of comments for a review
                rev.num_comments = 0
                for f in rev.rev_files:
                    if f['file_id'] in comments:
                        rev.num_comments += len(comments[f['file_id']])
                rev.num_notread = rev.num_comments - len([c_id for c_id, r, t, dat in my_comment_data if t == 'read'
                                                          and r == rev['review_id']])
                assigned_to_me.append(rev)

        data['myreviews'] = myreviews
        data['manager_reviews'] = manager_reviews
        data['assigned_reviews'] = assigned_to_me
        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'hw/css/peerreview.css')
        add_ctxt_nav_items(req)

        return 'peerReviewMain.html', data, None

    # IResourceManager methods

    def get_resource_url(self, resource, href, **kwargs):
        """Return the canonical URL for displaying the given resource.

        :param resource: a `Resource`
        :param href: an `Href` used for creating the URL

        Note that if there's no special rule associated to this realm for
        creating URLs (i.e. the standard convention of using realm/id applies),
        then it's OK to not define this method.
        """
        if resource.realm == 'peerreviewfile':
            return href('peerReviewPerform', IDFile=resource.id)
        elif resource.realm == 'peerreview':
            return href('peerReviewView', Review=resource.id)

        return href('peerReviewMain')

    def get_resource_realms(self):
        yield 'peerreview'
        yield 'peerreviewfile'

    def get_resource_description(self, resource, format=None, context=None,
                                 **kwargs):
        desc = unicode(resource.id)
        if resource.realm == 'peerreview':
            if format == 'compact':
                return 'review:%s' % resource.id  # Will be used as id in reports when 'realm' is used
            else:
                return 'Review %s' % resource.id
        elif resource.realm == 'peerreviewfile':
            if format == 'compact':
                return 'rfile:%s' % resource.id
            else:
                return 'ReviewFile %s' % resource.id
        return ""


    def resource_exists(self, resource):
        db = self.env.get_read_db()
        cursor = db.cursor()
        if resource.realm == 'peerreview':
            cursor.execute("SELECT * FROM peerreview WHERE review_id = %s", (resource.id,))
            if cursor.fetchone():
                return True
            else:
                return False
        elif resource.realm == 'peerreviewfile':
            cursor.execute("SELECT * FROM peerreviewfile WHERE file_id = %s", (resource.id,))
            if cursor.fetchone():
                return True
            else:
                return False

        raise ResourceNotFound('Resource %s not found.' % resource.realm)

    # ITemplateProvider methods

    def get_templates_dirs(self):
        """Return the path of the directory containing the provided templates."""
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]
