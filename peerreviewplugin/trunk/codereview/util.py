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

from .model import PeerReviewModel, PeerReviewerModel, ReviewFileModel

__author__ = 'Cinc'
__copyright__ = "Copyright 2016-2021"
__license__ = "BSD"


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
    :authname: login name of user

    :return True if review is in lock state, usually 'reviewed'.

    authname may be an empty string to check if a review is in the lock state at all.
    If not empty the review is not locked for the user with the given login name.
    """
    if review['owner'] == authname:
        return False

    lock_states = config.getlist("peerreview", "reviewer_locked_states")
    return review['status'] in lock_states
