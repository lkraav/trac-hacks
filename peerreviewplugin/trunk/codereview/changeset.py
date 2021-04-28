# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2021 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
import itertools

from codereview.model import get_users, PeerReviewModel, PeerReviewerModel, \
    ReviewDataModel, ReviewFileModel
from codereview.peerReviewCommentCallback import writeJSONResponse, writeResponse
from codereview.repo import hash_from_file_node
from codereview.repobrowser import get_node_from_repo
from codereview.util import get_files_for_review_id
from trac.core import Component, implements
from trac.resource import get_resource_url, Resource
from trac.util.translation import _
from trac.versioncontrol.api import Node, RepositoryManager
from trac.web.chrome import Chrome
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import add_script, add_script_data, add_stylesheet, web_context
from trac.wiki.formatter import format_to_oneliner


class PeerChangeset(Component):
    """Create review for a changeset from the changeset page.

    The created review holds the files from the changeset.

    '''Note''': This plugin may be disabled without side effects.
    """
    implements(IRequestFilter, IRequestHandler)

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
        # We only handle the changeset page
        if req.path_info.startswith('/changeset/'):
            if data and 'changes' in data and data['changes']:
                cset = data.get('new_rev', '')
                f_data = {}
                if cset:
                    review = get_review_for_changeset(self.env, cset, data.get('reponame', ''))
                    if review:
                        rfiles = get_files_for_review_id(self.env, req, review['review_id'], True)
                        for rfile in rfiles:
                            lines = set([comment['line_num'] for comment in rfile.comment_data])
                            if lines:
                                f_data[rfile['path']] = [rfile['file_id'], list(lines)]
                            else:
                                f_data[rfile['path']] = [rfile['file_id'], []]

                add_stylesheet(req, 'hw/css/peerreview.css')
                add_script_data(req,
                                {'peer_repo': data.get('reponame', ''),
                                 'peer_rev': cset,
                                 'peer_changeset_url': req.href.peerreviewchangeset(),
                                 'peer_comment_url': req.href.peercomment(),
                                 'tacUrl': req.href.chrome('/hw/images/thumbtac11x11.gif'),
                                 'peer_file_comments': f_data})
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
        tmpl_permission = """
        <div class="collapsed">
          <h3 class="foldable">{title}</h3>
          <div id="peer-codereview">
             %s
          </div>
        </div>
        """.format(title=_('Codereview'))

        if 'CODE_REVIEW_DEV' in req.perm:
            res = '<div id="peer-msg" class="system-message warning">%s</div>' % \
                  _("You don't have permission to create a code review.")
            return tmpl_permission % res

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
        if hasattr(Chrome, 'jenv'):
            template = chrome.load_template('peerreviewuser_jinja.html')
            rendered = chrome.render_template_string(template, data)
        else:
            template = chrome.load_template('user_list.html', None)
            rendered = template.generate(**data).render()

        peerreview_div = '<div class="collapsed"><h3 class="foldable">%s</h3>' \
                         '<div id="peer-codereview">%s</div>' \
                         '</div><div><p class="help">%s</p></div>' % \
                         (_('Codereview'), _form.format(**data) % rendered,
                          _("You need to create a review if you want to comment on files."))
        return peerreview_div

    def create_review_info(self, req, review, create=False):
        """Create html with inforamtion about the current changeset review.
        :param req: Request object
        :param review: Review object associated with this review
        :param create: True if the review was just created and the page is updated,
                       False if the page is normally loaded. There may be some
                       presentation differences.
        """
        _rev_info = u"""
            <dt class="property review">{review_id_label}</dt>
            <dd class="review">{review_wiki}
              <small><em>{reviewer_id_help}</em></small>
            </dd>
            <dt class="property">{status_label}</dt>
            <dd>{status}</dd>
            <dt class="property">{reviewers_label}</dt>
            <dd>{user_list}</dd>
        """
        review_tmpl = """
        <div>
            <dl id="peer-review-info">
              %s
            </dl>
        </div>
        """.format(title=_('Codereview'))
        def create_user_list():
            chrome = Chrome(self.env)
            if reviewer:
                usr = [u'<tr><td class="user-icon"><span class="ui-icon ui-icon-person"></span></td><td>%s</td></tr>' % chrome.authorinfo(req,
                                                                                                      item['reviewer'])
                       for item in reviewer]
                li = u"".join(usr)
            else:
                li = '<tr><td>{msg}</td></tr>'.format(msg=_("There are no users included in this code review."))
            return u'<table id="userlist">{li}</table>'.format(li=li)

        if 'CODE_REVIEW_VIEW' not in req.perm:
            no_perm_tmpl = """<dl id="peer-review-info"><dt class="property" style="margin-top: 1em">Review:</dt>
            <dd style="margin-top: 1em"><p>{msg}</p></dd></dl>"""
            return no_perm_tmpl.format(msg=_("You don't have permission to view code review information."))

        res = Resource('peerreview', review['review_id'])
        reviewer = list(PeerReviewerModel.select_by_review_id(self.env, review['review_id']))
        data = {
            'status': review['status'],
            'user_list': create_user_list(),
            'review_url': get_resource_url(self.env, res, req.href),
            'review_id': review['review_id'],
            'status_label': _("Status:"),
            'review_id_label': _("Review:"),
            'reviewers_label': _("Reviewers:"),
            'reviewer_id_help': _("(click to open review page)"),
            'review_wiki': format_to_oneliner(self.env, web_context(req),
                                              "[review:{r_id} Review {r_id}]".format(r_id=review['review_id']))
        }

        if create:
            return review_tmpl % _rev_info.format(**data)
        else:
            return _rev_info.format(**data)

    def match_request(self, req):
        return req.path_info == '/peerreviewchangeset'

    def process_request(self, req):

        if req.method == 'POST':
            req.perm.require('CODE_REVIEW_DEV')

            review = create_changeset_review(self, req)
            if not review:
                data = {'html': '<div id="peer-msg" class="system-message warning">%s</div>' %
                                _('Error while creating Review.')}
                writeJSONResponse(req, data)
            else:
                data = {'html': self.create_review_info(req, review, True)}
                writeJSONResponse(req, data)
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
                    'html': self.create_review_info(req, review, False)}
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
    user = req.args.getlist('user')
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
        # Changeset changes are without leading '/'. A Node path includes it.
        rfile['path'] = u'/' + item[path] if item[path][0] != '/' else item[path]
        rfile['revision'] = rev
        rfile['line_start'] = 0
        rfile['line_end'] = 0
        rfile['repo'] = reponame
        node, display_rev, context = get_node_from_repo(req, repo, rfile['path'], rfile['revision'])
        if node and node.kind == Node.FILE:
            rfile['changerevision'] = rev
            rfile['hash'] = hash_from_file_node(node)
            rfile.insert()

    # Mark that this is a changeset review
    dm = ReviewDataModel(self.env)
    dm['review_id'] = id_
    dm['type'] = 'changeset'
    dm['data'] = "%s:%s" % (reponame, rev)
    dm.insert()
    return review


def get_review_for_changeset(env, cs_num, repo_name):
    """Get a PeerReview from the given repo:changset combination.
     Return None if not found."""
    dm = ReviewDataModel(env)
    dm['type'] = 'changeset'
    dm['data'] = "%s:%s" % (repo_name, cs_num)
    rev_data = list(dm.list_matching_objects())

    # Permission handling is done in the called methods so the proper message is created there.
    if rev_data:
        return PeerReviewModel(env, rev_data[-1]['review_id'])
    else:
        return None


def get_changeset_data(env, review_id):
    """Return changeset information for the given review id if any.

    Checks the table 'peerreviewdata' for a changeset entry for this
    review id.

    @param review_id: numeric id of a review
    @return: list [reponame, changeset] or ['', ''] if no changeset review
    """
    dm = ReviewDataModel(env)
    dm['type'] = 'changeset'
    dm['review_id'] = review_id
    rev_data = list(dm.list_matching_objects())
    if not rev_data:
        return ['', '']
    return rev_data[-1]['data'].split(':')
