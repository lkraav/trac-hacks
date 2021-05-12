# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#
from trac.resource import Resource
from trac.wiki.formatter import format_to_oneliner
from trac.web.chrome import web_context

from .model import PeerReviewModel, PeerReviewerModel, ReviewCommentModel, ReviewDataModel, ReviewFileModel


__author__ = 'Cinc'
__copyright__ = "Copyright 2016-2021"
__license__ = "BSD"


def to_db_path(path):
    """Convert a path comming from Trac for db storage.

    A Trac path has no leading '/'. Files for reviews are stored with leading '/'
    in the database.
    """
    return '/' + path.lstrip('/')


def to_trac_path(path):
    """Convert a file path from the review database for usage with Trac.

    A Trac path has no leading '/'. Files for reviews are stored with leading '/'
    in the database.
    """
    return path.lstrip('/')


def get_review_for_file(env, file_id):
    rf = ReviewFileModel(env, file_id)
    if not rf:
        return None
    rev = PeerReviewModel(env, rf['review_id'])
    return rev


def not_allowed_to_comment(env, review, perm, authname):
    """Check if the current user may comment on a file.

    For adding a comment you must either be:

    * the owner of the review
    * one of the reviewers
    * a user with permission CODE_REVIEW_MGR

    @return: True if commenting is not allowed, False otherwise
    """
    # Don't let users comment who are not part of this review
    reviewers = PeerReviewerModel.select_by_review_id(env, review['review_id'])
    all_names = [reviewer['reviewer'] for reviewer in reviewers]
    # Include owner of review in allowed names
    all_names.append(review['owner'])  # We don't care if the name is already in the list

    if authname not in all_names and 'CODE_REVIEW_MGR' not in perm:
        return True

    return False


def review_is_finished(config, review):
    """A finished review may only be reopened by a manager or admisnistrator

    :param config: Trac config object
    :param review: review object

    :return True if review is in one of the terminal states
    """
    finish_states = config.getlist("peerreview", "terminal_review_states")
    return review['status'] in finish_states


def review_is_locked(config, review, authname=""):
    """For a locked review a user can't change his voting
    :param config: Trac config object
    :param review: review object
    :param authname: login name of user

    :return True if review is in lock state else False. Default lock state is
            usually 'reviewed'.

    authname may be an empty string to check if a review is in the lock state at all.
    If not empty the review is not locked for the user with the given login name.
    """
    if review['owner'] == authname:
        return False

    lock_states = config.getlist("peerreview", "reviewer_locked_states")
    return review['status'] in lock_states


def get_changeset_html(env, req, rev, repos):
    """Create html for use in templates from changeset and repository information

    :param env: Environment object
    :param req: Request object
    :param rev: changeset revision as a string
    :param repos: Repository object for this changeset

    We use Tracs formatting functions to get proper Trac links with correct titles and rendering.
    """
    if rev:
        resource_repo = Resource('repository', repos.reponame)
        changeset_html = format_to_oneliner(env,
                                            web_context(req,
                                                        Resource('changeset', rev, parent=resource_repo)),
                                            '[changeset:%s %s]' % (rev, rev))
    else:
        changeset_html = ''
    return changeset_html


def get_files_for_review_id(env, req, review_id, comments=False):
    """Get all file objects belonging to the given review id. Provide the number of comments if asked for.

    :param env: Environment object
    :param review_id: id of review as an int
    :param req: Request object
    :param comments: if True add information about comments as attributes to the file objects
    :return: list of ReviewFileModels
    """
    rev_files = list(ReviewFileModel.select_by_review(env, review_id))
    if comments:
        for file_ in rev_files:
            file_.comment_data = list(ReviewCommentModel.select_by_file_id(env, file_['file_id']))
            file_.num_comments = len(file_.comment_data)
            my_comment_data = ReviewDataModel.comments_for_file_and_owner(env, file_['file_id'], req.authname)
            file_.num_notread = file_.num_comments - len([c_id for c_id, t, dat in my_comment_data if t == 'read'])
    return rev_files
