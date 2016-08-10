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
from trac.web.chrome import INavigationContributor, add_javascript, add_script_data, \
    add_warning, add_notice, add_stylesheet, Chrome
from trac.web.main import IRequestHandler
from trac.versioncontrol.api import RepositoryManager
from CodeReviewStruct import *
from model import Comment, get_users, \
    PeerReviewerModel, PeerReviewModel, Reviewer, ReviewFileModel
from peerReviewMain import add_ctxt_nav_items
from repobrowser import get_node_from_repo
from .repo import hash_from_file_node


def java_string_hashcode(s):
    # See: http://garage.pimentech.net/libcommonPython_src_python_libcommon_javastringhashcode/
    h = 0
    for c in s:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def create_id_string(f):
    return "%s,%s,%s,%s,%s" %\
           (f['path'], f['revision'], f['line_start'], f['line_end'], f['repo'])


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
    implements(IRequestHandler, INavigationContributor)

    trac_version = get_distribution('trac').version
    legacy_trac = parse_version(trac_version) < parse_version('1.0.0')  # True if Trac V0.12.x

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
                returnid = self.createCodeReview(req)
                if oldid:
                    # Automatically close the review we resubmitted from
                    review = PeerReviewModel(self.env, oldid)
                    review['status'] = "closed"
                    review.save_changes(req.authname, comment="Closed after resubmitting as review '#%s'." %
                                                              returnid)
                    add_notice(req, "Review '%s' (#%s) was automatically closed after resubmitting as '#%s'." %
                               (review['name'], oldid, returnid))
                #If no errors then redirect to the viewCodeReview page
                req.redirect(self.env.href.peerReviewView() + '?Review=' + str(returnid))
            if req.args.get('createfollowup'):
                returnid = self.createCodeReview(req)
                #If no errors then redirect to the viewCodeReview page
                req.redirect(self.env.href.peerReviewView(Review=returnid))
            if req.args.get('save'):
                self.save_changes(req)
                req.redirect(self.env.href.peerReviewView(Review=oldid))
            if req.args.get('cancel'):
                req.redirect(self.env.href.peerReviewView(Review=oldid))

        data = {}
        data['users'] = get_users(self.env)

        review_id = req.args.get('resubmit')

        # If we tried resubmitting and the review_id is not a valid number or not a valid code review, error
        review = PeerReviewModel(self.env, review_id)
        if review_id and (not review_id.isdigit() or not review):
            raise TracError("Invalid resubmit ID supplied - unable to load page correctly.", "Resubmit ID error")

        if review['status'] == 'closed' and req.args.get('modify'):
            raise TracError("The Review '#%s' is already closed and can't be modified." % review['review_id'],
                            "Modify Review error")

        # If we are resubmitting a code review and we are the author or the manager
        if review_id and (review['owner'] == req.authname or 'CODE_REVIEW_MGR' in req.perm):
            data['new'] = "no"
            data['oldid'] = review_id

            add_users_to_data(self.env, review_id, data)

            rfiles = ReviewFileModel.select_by_review(self.env, review_id)
            popFiles = []
            # Set up the file information
            for f in rfiles:
                # This id is used by the javascript code to find duplicate entries.
                f.element_id = create_file_hash_id(f)
                f.id_string = create_id_string(f)
                if req.args.get('modify'):
                    comments = Comment.select_by_file_id(self.env, f['file_id'])
                    f.num_comments = len(comments) or 0
                popFiles.append(f)

            data['name'] = review['name']
            if req.args.get('modify') or req.args.get('followup'):
                data['notes'] = review['notes']
            else:
                data['notes'] = "%sReview based on ''%s'' (resubmitted)." %\
                                (review['notes']+ CRLF + CRLF, review['name'])

            data['prevFiles'] = popFiles

        # If we resubmitting a code review, and are neither the author and the manager
        elif review_id and not review['owner'] == req.authname and not 'CODE_REVIEW_MGR' in req.perm:
            raise TracError("You need to be a manager or the author of this code review to resubmit it.",
                            "Access error")
        # If we are not resubmitting
        else:
            data['new'] = "yes"

        data['cycle'] = itertools.cycle
        data['followup'] = req.args.get('followup')
        prj = self.env.config.getlist("peerreview", "projects", default=[])
        if not prj:
            prj = self.env.config.getlist("ticket-custom", "project.options", default=[], sep='|')

        data['projects'] = prj
        data['curproj'] = review['project']

        if self.legacy_trac:
            add_javascript(req, self.env.config.get('trac', 'jquery_ui_location') or
                           'hw/js/jquery-ui-1.11.4.min.js')
            add_stylesheet(req, self.env.config.get('trac', 'jquery_ui_theme_location') or
                           'hw/css/jquery-ui-1.11.4.min.css')
        else:
            Chrome(self.env).add_jquery_ui(req)
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_javascript(req, 'common/js/auto_preview.js')
        add_script_data(req, {'repo_browser': self.env.href.peerReviewBrowser(),
                              'auto_preview_timeout': self.env.config.get('trac', 'auto_preview_timeout', '2.0'),
                              'form_token': req.form_token,
                              'peer_is_modify': req.args.get('modify', '0')})
        add_javascript(req, "hw/js/peer_review_new.js")
        add_javascript(req, 'hw/js/peer_user_list.js')
        add_ctxt_nav_items(req)
        return 'peerReviewNew.html', data, None

    # Takes the information given when the page is posted
    # and creates a new code review struct in the database
    # and populates it with the information.  Also creates
    # new reviewer structs and file structs for the review.
    def createCodeReview(self, req):
        oldid = req.args.get('oldid', 0)
        review = PeerReviewModel(self.env)
        review['owner'] = req.authname
        review['name'] = req.args.get('Name')
        review['notes'] = req.args.get('Notes')
        if req.args.get('project'):
             review['project'] = req.args.get('project')
        if oldid:
            # Resubmit or follow up
            if req.args.get('followup'):
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
            if req.args.get('followup'):
                rfile['revision'] = req.args.get('revision', 0)
            else:
                rfile['revision'] = segment[1]
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
                reviewer = Reviewer(self.env, review['review_id'], name)
                if file_is_commented(name):
                    add_warning(req, "User '%s' already commented a file. Not removed from review '#%s'",
                                name, review['review_id'])
                    continue
                reviewer.delete()

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
