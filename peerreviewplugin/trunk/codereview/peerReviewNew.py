#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#

# Provides functionality to create a new code review.
# Works with peerReviewNew.html

import itertools
import time
from pkg_resources import get_distribution, parse_version
from trac import util
from trac.core import Component, implements, TracError
from trac.util.text import CRLF
from trac.web.chrome import INavigationContributor, add_script, add_script_data, \
    add_warning, add_notice, add_stylesheet, Chrome
from trac.web.main import IRequestHandler
from trac.versioncontrol.api import RepositoryManager
from model import Comment, get_users, \
    PeerReviewerModel, PeerReviewModel, ReviewFileModel
from peerReviewMain import add_ctxt_nav_items
from repobrowser import get_node_from_repo
from .repo import hash_from_file_node


def java_string_hashcode(s):
    # See: http://garage.pimentech.net/libcommonPython_src_python_libcommon_javastringhashcode/
    h = 0
    for c in s:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def create_id_string(f, rev=None):
    # Use rev to override the revision in the id string. Used in followup review creation
    f_rev = rev or f['revision']
    return "%s,%s,%s,%s,%s" %\
           (f['path'], f_rev, f['line_start'], f['line_end'], f['repo'])


def create_file_hash_id(f):
    return 'id%s' % java_string_hashcode(create_id_string(f))


def add_users_to_data(env, reviewID, data):
    """Add user, assigned and unassigned users to dict data.

    This function searches all users assigned to the given review and adds the list to the data dictionary using
    key 'assigned_users'. Not yet assigned users are added using the key 'unassigned_users'.
    If data['user'] doesn't exist this function will query the list of available users and add them.

    :param env: Trac environment object
    :param reviewID: Id of a review
    :param data:

    :return: None. Data is added to dict data using keys 'users', 'assigned_users', 'unassigned_users', 'emptyList'
    """
    if 'users' not in data:
        data['users'] = get_users(env)
    all_users = data['users']

    # get code review data and populate
    reviewers = PeerReviewerModel.select_by_review_id(env, reviewID)
    popUsers = []
    for reviewer in reviewers:
        popUsers.append(reviewer['reviewer'])
    data['assigned_users'] = popUsers

    # Figure out the users that were not included
    # in the previous code review so that they can be
    # added to the dropdown to select more users
    # (only check if all users were not included in previous code review)
    notUsers = []
    if len(popUsers) != len(all_users):
        notUsers = list(set(all_users)-set(popUsers))
        data['emptyList'] = 0
    else:
        data['emptyList'] = 1

    data['unassigned_users'] = notUsers


class NewReviewModule(Component):
    """Component handling the creation of code reviews.

    [[BR]]
    This component handles the creation of a new review and creation of followup reviews.
    """

    implements(IRequestHandler, INavigationContributor)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/peerReviewNew'

    def process_request(self, req):
        req.perm.require('CODE_REVIEW_DEV')

        if req.method == 'POST':
            oldid = req.args.get('oldid')
            if req.args.get('create'):
                returnid = self.createCodeReview(req, 'create')
                if oldid:
                    # Automatically close the review we resubmitted from
                    review = PeerReviewModel(self.env, oldid)
                    review['status'] = "closed"
                    review.save_changes(req.authname, comment="Closed after resubmitting as review '#%s'." %
                                                              returnid)
                    add_notice(req, "Review '%s' (#%s) was automatically closed after resubmitting as '#%s'." %
                               (review['name'], oldid, returnid))
                # If no errors then redirect to the viewCodeReview page
                req.redirect(self.env.href.peerreviewview(returnid))
            if req.args.get('createfollowup'):
                returnid = self.createCodeReview(req, 'followup')
                # If no errors then redirect to the viewCodeReview page of the new review
                req.redirect(self.env.href.peerreviewview(returnid))
            if req.args.get('save'):
                self.save_changes(req)
                req.redirect(self.env.href.peerreviewview(oldid))
            if req.args.get('cancel'):
                req.redirect(self.env.href.peerreviewview(oldid))

        # Handling of GET request

        data = {'users': get_users(self.env),
                'new': "no",
                'cycle': itertools.cycle,
                'followup': req.args.get('followup')
                }

        is_followup = req.args.get('followup', None)
        review_id = req.args.get('resubmit')
        review = PeerReviewModel(self.env, review_id)

        # If we tried resubmitting and the review_id is not a valid number or not a valid code review, error
        if review_id and (not review_id.isdigit() or not review):
            raise TracError("Invalid resubmit ID supplied - unable to load page correctly.", "Resubmit ID error")

        if review['status'] == 'closed' and req.args.get('modify'):
            raise TracError("The Review '#%s' is already closed and can't be modified." % review['review_id'],
                            "Modify Review error")

        # If we are resubmitting a code review, and are neither the author nor the manager
        if review_id and not review['owner'] == req.authname and not 'CODE_REVIEW_MGR' in req.perm:
            raise TracError("You need to be a manager or the author of this code review to resubmit it.",
                            "Access error")

        # If we are resubmitting a code review and we are the author or the manager
        if review_id and (review['owner'] == req.authname or 'CODE_REVIEW_MGR' in req.perm):
            data['oldid'] = review_id

            add_users_to_data(self.env, review_id, data)

            rfiles = ReviewFileModel.select_by_review(self.env, review_id)
            popFiles = []
            # Set up the file information
            for f in rfiles:
                if is_followup:
                    # Get the current file and repo revision
                    repo = RepositoryManager(self.env).get_repository(f['repo'])
                    node, display_rev, context = get_node_from_repo(req, repo, f['path'], None)
                    f.curchangerevision = unicode(node.created_rev)
                    f.curreporev = repo.youngest_rev
                    # We use the current repo revision here so on POST that revision is used for creating
                    # the file entry in the database. The POST handler parses the string for necessary information.
                    f.id_string = create_id_string(f, repo.youngest_rev)
                else:
                    # The id_String holds info like revision, line numbers, path and repo. It is later used to save
                    # file info to the database during a post.
                    f.id_string = create_id_string(f)
                # This id is used by the javascript code to find duplicate entries.
                f.element_id = create_file_hash_id(f)
                if req.args.get('modify'):
                    comments = Comment.select_by_file_id(self.env, f['file_id'])
                    f.num_comments = len(comments) or 0
                popFiles.append(f)

            data['name'] = review['name']
            if req.args.get('modify'):
                data['notes'] = review['notes']
            elif  req.args.get('followup'):
                data['notes'] = "%sReview is followup to review ''%s''." % \
                                (review['notes']+ CRLF, review['name'])
            else:
                data['notes'] = "%sReview based on ''%s'' (resubmitted)." %\
                                (review['notes']+ CRLF, review['name'])
            data['prevFiles'] = popFiles
        # If we are not resubmitting
        else:
            data['new'] = "yes"

        prj = self.env.config.getlist("peerreview", "projects", default=[])
        if not prj:
            prj = self.env.config.getlist("ticket-custom", "project.options", default=[], sep='|')

        data['projects'] = prj
        data['curproj'] = review['project']

        Chrome(self.env).add_jquery_ui(req)
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_script(req, 'common/js/auto_preview.js')
        add_script_data(req, {'repo_browser': self.env.href.peerReviewBrowser(),
                              'auto_preview_timeout': self.env.config.get('trac', 'auto_preview_timeout', '2.0'),
                              'form_token': req.form_token,
                              'peer_is_modify': req.args.get('modify', '0'),
                              'peer_is_followup': req.args.get('followup', '0')})
        add_script(req, "hw/js/peer_review_new.js")
        add_script(req, 'hw/js/peer_user_list.js')
        add_ctxt_nav_items(req)
        return 'peerReviewNew.html', data, None

    def createCodeReview(self, req, action):
        """Create a new code review from the data in the request object req.

        Takes the information given when the page is posted and creates a
        new code review struct in the database and populates it with the
        information. Also creates new reviewer structs and file structs for
        the review.
        """
        oldid = req.args.get('oldid', 0)
        review = PeerReviewModel(self.env)
        review['owner'] = req.authname
        review['name'] = req.args.get('Name')
        review['notes'] = req.args.get('Notes')
        if req.args.get('project'):
            review['project'] = req.args.get('project')
        if oldid:
            # Resubmit or follow up
            if action == 'followup':
                review['parent_id'] = oldid
            else:
                # Keep parent -> follow up relationship when resubmitting
                old_review = PeerReviewModel(self.env, oldid)
                review['parent_id'] = old_review['parent_id']
        review.insert()
        id_ = review['review_id']
        self.log.debug('New review created: %s', id_)

        # loop here through all the reviewers
        # and create new reviewer structs based on them
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

        # loop here through all included files
        # and create new file structs based on them
        files = req.args.get('file', [])
        if not type(files) is list:
            files = [files]
        for item in files:
            segment = item.split(',')
            rfile = ReviewFileModel(self.env)
            rfile['review_id'] = id_
            rfile['path'] = segment[0]
            rfile['revision'] = segment[1]  # If we create a followup review this is the current repo revision
            rfile['line_start'] = segment[2]
            rfile['line_end'] = segment[3]
            rfile['repo'] = segment[4]
            repo = RepositoryManager(self.env).get_repository(rfile['repo'])
            node, display_rev, context = get_node_from_repo(req, repo, rfile['path'], rfile['revision'])
            rfile['changerevision'] = unicode(node.created_rev)
            rfile['hash'] = self._hash_from_file_node(node)
            rfile.insert()
        return id_

    def _hash_from_file_node(self, node):
        return hash_from_file_node(node)

    def save_changes(self, req):
        def file_is_commented(author):
            rfiles = ReviewFileModel.select_by_review(self.env, review['review_id'])
            for f in rfiles:
                comments = [c for c in Comment.select_by_file_id(self.env, f['file_id']) if c.author == author]
                if comments:
                    return True
            return False

        review = PeerReviewModel(self.env, req.args.get('oldid'))
        review['name'] = req.args.get('Name')
        review['notes'] = req.args.get('Notes')
        review['project'] = req.args.get('project')
        review.save_changes(req.authname)

        user = req.args.get('user')
        if not type(user) is list:
            user = [user]
        data = {}
        add_users_to_data(self.env,review['review_id'], data)
        # Handle new users if any
        new_users = list(set(user) - set(data['assigned_users']))
        for name in new_users:
            if name != "":
                reviewer = PeerReviewerModel(self.env)
                reviewer['review_id'] = review['review_id']
                reviewer['reviewer'] = name
                reviewer['vote'] = -1
                reviewer.insert()
        # Handle removed users if any
        rem_users = list(set(data['assigned_users']) - set(user))
        for name in rem_users:
            if name != "":
                if file_is_commented(name):
                    add_warning(req, "User '%s' already commented a file. Not removed from review '#%s'",
                                name, review['review_id'])
                else:
                    PeerReviewerModel.delete_by_review_id_and_name(self.env, review['review_id'], name)

        # Handle file removal
        new_files = req.args.get('file')
        if not type(new_files) is list:
            new_files = [new_files]
        old_files = []
        rfiles = {}
        for f in ReviewFileModel.select_by_review(self.env, review['review_id']):
            fid = u"%s,%s,%s,%s,%s" % (f['path'], f['revision'], f['line_start'], f['line_end'], f['repo'])
            old_files.append(fid)
            rfiles[fid] = f

        rem_files = list(set(old_files) - set(new_files))
        for fid in rem_files:
            rfiles[fid].delete()
