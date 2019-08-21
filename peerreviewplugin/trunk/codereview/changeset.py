# -*- coding: utf-8 -*-
import itertools

from codereview.model import get_users, PeerReviewModel, PeerReviewerModel, \
    ReviewDataModel, ReviewFileModel
from codereview.peerReviewCommentCallback import writeJSONResponse, writeResponse
from codereview.repo import hash_from_file_node
from codereview.repobrowser import get_node_from_repo
from genshi.template import MarkupTemplate
from trac.core import Component, implements
from trac.resource import get_resource_url, Resource
from trac.util.text import _
from trac.versioncontrol.api import RepositoryManager
from trac.web.chrome import Chrome
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import add_script, add_script_data, add_stylesheet


class PeerChangeset(Component):
    implements(IRequestFilter, IRequestHandler)

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
        # We only handle the changeset page
        if req.path_info.startswith('/changeset/'):
            if data and 'changes' in data and data['changes']:
                add_stylesheet(req, 'hw/css/peerreview.css')
                add_script_data(req,
                                {'peer_repo': data.get('reponame', ''),
                                 'peer_rev': data.get('new_rev', ''),
                                 'peer_changeset_url': req.href.peerreviewchangeset(),
                                 'tacUrl': req.href.chrome('/hw/images/thumbtac11x11.gif')})
                add_script(req, "hw/js/peer_trac_changeset.js")
                add_script(req, "hw/js/peer_user_list.js")
                Chrome(self.env).add_jquery_ui(req)
                add_script(req, 'common/js/folding.js')

        return template, data, content_type

    # IRequestHandler methods

    def create_review_form(self, req):
        _form = """
<form id="create-peerreview-form" action="">
  <input type="hidden" name="peer_repo" value="{reponame}" />
  <input type="hidden" name="peer_rev" value="{rev}" />
  <input type="hidden" name="Name" value="Changeset {rev} in repository '{reponame}'" />
  <input type="hidden" name="__FORM_TOKEN" value="{form-token}" />
  <fieldset>
    <legend>Select reviewers for your review.</legend>
    %s
    <div class="buttons">
      <input id="create-review-submit" type="submit" name="create" value="Create Code Review"/>
    </div>
  </fieldset>
</form>
<div id="user-rem-confirm" title="Remove user?">
    <p>
    <span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>
    Really remove the user <strong id="user-rem-name"></strong> from the list?</p>
</div>
"""

        if 'CODE_REVIEW_DEV' not in req.perm:
            res = '<div id="peer-msg" class="system-message warning">%s</div>' % \
                  _("You don't have permission to create a code review.")
            return self.review_tmpl % res

        users = get_users(self.env)
        data = {
            'form-token': req.form_token,
            'reponame': req.args.get('peer_repo', ''),
            'rev': req.args.get('peer_rev', ''),
            'new': 'yes',
            'users': users,
            'cycle': itertools.cycle
        }
        chrome = Chrome(self.env)
        template = chrome.load_template('user_list.html')

        peerreview_div = '<div class="collapsed"><h3 class="foldable">%s</h3>' \
                         '<div id="peer-codereview">' \
                         '%s' \
                         '</div>' \
                         '</div>' % \
                         (_('Codereview'), _form.format(**data) % template.generate(**data).render())

        return peerreview_div

    review_tmpl = """
<div class="collapsed">
  <h3 class="foldable">{title}</h3>
  <div id="peer-codereview">%s</div>
</div>
""".format(title=_('Codereview'))

    def create_review_info(self, req, review):
        _rev_info = """
        <dl xmlns:py="http://genshi.edgewall.org/" id="peer-review-info">
            <dt class="property" style="margin-top: 1em">Review ID:</dt>
            <dd style="margin-top: 1em"><a href="{review_url}" title="Open Review #{review_id}">#{review_id}</a>
              <small><em>(click to open review)</em></small>
            </dd>
            <dt class="property">Status:</dt>
            <dd>${review['status']}</dd>
            <dt class="property">Reviewers</dt>
            <dd>
            <ul id="userlist">
                    <li py:if="not reviewer" class="even">
                        There are no users included in this code review.
                    </li>
                    <li py:if="reviewer" py:for="item in reviewer">
                        ${item['reviewer']}
                    </li>
            </ul>
            </dd>
        </dl>
        """

        if 'CODE_REVIEW_VIEW' not in req.perm:
            return ""

        res = Resource('peerreview', review['review_id'])

        data = {
            'reponame': req.args.get('peer_repo', ''),
            'rev': req.args.get('peer_rev', ''),
            'new': 'no',
            'review': review,
            'reviewer': list(PeerReviewerModel.select_by_review_id(self.env, review['review_id'])),
            'cycle': itertools.cycle
        }

        format_data = {'review_url': get_resource_url(self.env, res, req.href),
                       'review_id': review['review_id']
                       }
        template = MarkupTemplate(_rev_info)
        if req.args.get('peer_create'):
            return self.review_tmpl % template.generate(**data).render().format(**format_data)
        else:
            return template.generate(**data).render().format(**format_data)

    def match_request(self, req):
        return req.path_info == '/peerreviewchangeset'

    def process_request(self, req):

        if req.method == 'POST':
            req.perm.require('CODE_REVIEW_DEV')

            review = create_changeset_review(self, req)
            if not review:
                writeResponse(req, '<div id="peer-msg" class="system-message warning">%s</div>' %
                              _('Error while creating Review.'))
            else:
                writeResponse(req, self.create_review_info(req, review))
            return

        dm = ReviewDataModel(self.env)
        dm['type'] = 'changeset'
        dm['data'] = "%s:%s" % (req.args.get('peer_repo', ''), req.args.get('peer_rev', ''))
        rev_data = list(dm.list_matching_objects())

        # Permission handling is done in the called methods so the proper message is created there.
        if not rev_data:
            data = {'action': 'create',
                    'html': self.create_review_form(req)}
            writeJSONResponse(req, data)
        else:
            review = PeerReviewModel(self.env, rev_data[-1]['review_id'])
            data = {'action': 'info',
                    'html': self.create_review_info(req, review)}
            writeJSONResponse(req, data)


def create_changeset_review(self, req):
    """Create a new code review from the data in the request object req.

    Takes the information given when the page is posted and creates a
    new code review in the database and populates it with the
    information. Also creates new reviewer and file data for
    the review.
    """
    rev = req.args.get('peer_rev')
    reponame = req.args.get('peer_repo')
    repo = RepositoryManager(self.env).get_repository(reponame)
    if not repo:
        return None

    changeset = repo.get_changeset(rev)
    if not changeset:
        return None

    review = PeerReviewModel(self.env)
    review['owner'] = req.authname
    review['name'] = req.args.get('Name')
    review['notes'] = req.args.get('Notes')
    if req.args.get('project'):
        review['project'] = req.args.get('project')
    review.insert()
    id_ = review['review_id']

    # Create reviewer entries
    user = req.args.get('user', [])
    if not type(user) is list:
        user = [user]
    for name in user:
        if name != "":
            reviewer = PeerReviewerModel(self.env)
            reviewer['review_id'] = id_
            reviewer['reviewer'] = name
            reviewer['vote'] = -1
            reviewer.insert()

    # Create file entries
    path, kind, change, base_path, base_rev = range(0, 5)
    for item in changeset.get_changes():
        rfile = ReviewFileModel(self.env)
        rfile['review_id'] = id_
        rfile['path'] = item[path]
        rfile['revision'] = rev
        rfile['line_start'] = 0
        rfile['line_end'] = 0
        rfile['repo'] = reponame
        node, display_rev, context = get_node_from_repo(req, repo, rfile['path'], rfile['revision'])
        rfile['changerevision'] = rev
        rfile['hash'] = hash_from_file_node(node)
        rfile.insert()

    # MArk that this is a changeset review
    dm = ReviewDataModel(self.env)
    dm['review_id'] = id_
    dm['type'] = 'changeset'
    dm['data'] = "%s:%s" % (reponame, rev)
    dm.insert()
    return review
