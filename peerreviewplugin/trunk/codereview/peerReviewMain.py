#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016-2021 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#
# Provides functionality for main page
# Works with peerreview_main.html

import itertools
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.resource import get_resource_url, IResourceManager, resource_exists, Resource, ResourceNotFound
from trac.util import as_int
from trac.util.datefmt import format_date, to_datetime, user_time
from trac.util.html import Markup, html as tag
from trac.util.translation import _
from trac.web.chrome import add_ctxtnav, add_stylesheet, Chrome,\
    INavigationContributor, ITemplateProvider, web_context
from trac.web.main import IRequestHandler
from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.formatter import format_to
from .model import ReviewCommentModel, ReviewDataModel, ReviewFileModel, PeerReviewModel, PeerReviewerModel
from .util import review_is_finished


def add_ctxt_nav_items(req):
    add_ctxtnav(req, _("My Code Reviews"), req.href.peerReviewMain(), title=_("My Code Reviews"))
    add_ctxtnav(req, _("Create a Code Review"), req.href.peerReviewNew(), title=_("Create a Code review"))
    add_ctxtnav(req, _("Report"), req.href.peerreviewreport(), title=_("Show Codereview Reports"))
    add_ctxtnav(req, _("Search Code Reviews"), req.href.peerReviewSearch(), _("Search Code Reviews"))


class PeerReviewMain(Component):
    """Main component for code reviews providing basic features. Show overview page for code reviews.

    [[BR]]
    === Permissions
    There are three additional permissions for code reviews:
    * CODE_REVIEW_VIEW
    * CODE_REVIEW_DEV
    * CODE_REVIEW_MGR

    === Wiki syntax
    Two new trac links are available with this plugin:
    * {{{review:<xxx>}}} with <xxx> being a review id
    * {{{rfile:<xxx>}}} with <xxx> being a file id

    These links open the review page or file page.
    """
    implements(INavigationContributor, IPermissionRequestor, IRequestHandler,
               IResourceManager, ITemplateProvider, IWikiSyntaxProvider)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            yield ('mainnav', 'peerReviewMain',
                   Markup('<a href="%s">Codereview</a>') % req.href.peerReviewMain())

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
            options['escape_newlines'] = bool(int(req.args['escape_newlines'] or 0))
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
                rev.date = user_time(req, format_date, to_datetime(rev['created']))
                if rev['closed']:
                    rev.finish_date = user_time(req, format_date, to_datetime(rev['closed']))
                else:
                    rev.finish_date = ''
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
                rev.date = user_time(req, format_date, to_datetime(rev['created']))
                if rev['closed']:
                    rev.finish_date = user_time(req, format_date, to_datetime(rev['closed']))
                else:
                    rev.finish_date = ''
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

        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_ctxt_nav_items(req)

        if hasattr(Chrome, 'jenv'):
            return 'peerreview_main_jinja.html', data
        else:
            return 'peerreview_main.html', data, None

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
            return href.peerreviewview(resource.id)

        return href('peerReviewMain')

    def get_resource_realms(self):
        yield 'peerreview'
        yield 'peerreviewfile'

    def get_resource_description(self, resource, format=None, context=None,
                                 **kwargs):
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
        with self.env.db_query as db:
            cursor = db.cursor()
            if resource.realm == 'peerreview':
                cursor.execute("SELECT * FROM peerreview WHERE review_id = %s", (resource.id,))
                if cursor.fetchone():
                    return True
                else:
                    return False
            elif resource.realm == 'peerreviewfile':
                # Only files associated with a review are real peerreviewfiles
                cursor.execute("SELECT * FROM peerreviewfile WHERE file_id = %s AND review_id != 0", (resource.id,))
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

    # IWikiSyntaxProvider

    def get_link_resolvers(self):
        return [('review', self._format_review_link),
                ('rfile', self._format_file_link)]

    def get_wiki_syntax(self):
        return []

    def _format_review_link(self, formatter, ns, target, label):
        res = Resource('peerreview', target)
        if resource_exists(self.env, res):
            review = PeerReviewModel(self.env, target)
            if review['status'] == 'closed':
                cls = 'peer-wiki closed'
            else:
                cls = 'peer-wiki'
            status_map = {'approved': tag.span(u" \u2713", class_='approved'),
                          'disapproved': tag.span(u" \u2717", class_='disapproved')}
            try:
                span = status_map[review['status']]
            except KeyError:
                span = ''

            return tag.a([label, span],
                         href=get_resource_url(self.env, res, formatter.href),
                         title=_(u"Review #%s (%s)") % (target, review['status']),
                         class_=cls
                        )

        return tag.span(label + '?',
                        title=_(u"Review #%s doesn't exist") % target,
                        class_='missing')

    def _format_file_link(self, formatter, ns, target, label):
        def rfile_is_finished(config, rfile):
            """A finished review may only be reopened by a manager or admisnistrator

            :param config: Trac config object
            :param rfile: review file object

            :return True if review is in one of the terminal states
            """
            finish_states = config.getlist("peerreview", "terminal_review_states")
            return rfile['status'] in finish_states

        res = Resource('peerreviewfile', target)
        if resource_exists(self.env, res):
            rfile = ReviewFileModel(self.env, target)
            if rfile_is_finished(self.env.config, rfile):
                cls = 'closed'
            else:
                cls = None

            return tag.a(label,
                         href=get_resource_url(self.env, res, formatter.href),
                         title=_(u"File #%s (%s)") % (target, rfile['status']),
                         class_=cls
                         )

        return tag.span(label + '?',
                        title=_(u"File #%s doesn't exist") % target,
                        class_='missing')
