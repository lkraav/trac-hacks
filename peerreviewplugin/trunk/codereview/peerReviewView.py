#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016-2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

# Provides functionality for view code review page
# Works with peerreview_view.html

import itertools
import re
from codereview.changeset import get_changeset_data
from codereview.model import Comment, get_users, \
    PeerReviewerModel, PeerReviewModel, ReviewCommentModel, ReviewDataModel, ReviewFileModel
from codereview.peerReviewMain import add_ctxt_nav_items
from codereview.tracgenericworkflow.api import IWorkflowOperationProvider, IWorkflowTransitionListener, \
    ResourceWorkflowSystem
from codereview.util import get_changeset_html, get_files_for_review_id, review_is_finished, review_is_locked
from string import Template
from trac.config import BoolOption, ListOption
from trac.core import Component, implements, TracError
from trac.mimeview.api import Mimeview
from trac.resource import Resource
from trac.util.datefmt import format_date, to_datetime, user_time
from trac.util.html import html as tag
from trac.util.text import CRLF, obfuscate_email_address
from trac.util.translation import _
from trac.versioncontrol.api import RepositoryManager
from trac.web.chrome import add_link, add_script, add_stylesheet, Chrome, INavigationContributor, web_context
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to_html, format_to_oneliner


class PeerReviewView(Component):
    """Displays a summary page for a review.

    === The following configuration options may be set:

    [[TracIni(peerreview)]]
    """
    implements(IRequestHandler, INavigationContributor, IWorkflowOperationProvider, IWorkflowTransitionListener)

    ListOption("peerreview", "terminal_review_states", ['closed', 'approved', 'disapproved'],
               doc="Ending states for a review. Only an administrator may force a review to leave these states. "
                   "Reviews in one of these states may not be modified.")

    ListOption("peerreview", "reviewer_locked_states", ['reviewed'],
               doc="A reviewer may no longer comment on reviews in one of the given states. The review owner still "
                   "may comment. Used to lock a review against modification after all reviewing persons have "
                   "finished their task.")

    show_ticket = BoolOption("peerreview", "show_ticket", False,
                             doc="A ticket may be created with information about "
                                 "a review. If set to {{{True}}} a ticket preview on "
                                 "the view page of a review will be shown and a button "
                                 "for filling the '''New Ticket''' page with data. "
                                 "The review must have status ''reviewed''. Only the "
                                 "author or a manager have the necessary permisisons.")

    peerreview_view_re = re.compile(r'/peerreviewview/([0-9]+)$')

    # used to build the url inside a workflow. Must be changed, when the depth of the url of this page changes.
    workflow_base_href = '..'  # account for trailing review id in url

    # IWorkflowOperationProvider methods

    def get_implemented_operations(self):
        yield 'set_review_owner'

    def get_operation_control(self, req, action, operation, res_wf_state, resource):
        """Get markup for workflow operation 'set_review_owner."""

        id_ = 'action_%s_operation_%s' % (action, operation)

        rws = ResourceWorkflowSystem(self.env)
        this_action = rws.actions[resource.realm][action]  # We need the full action data for custom label

        if operation == 'set_review_owner':
            self.log.debug("Creating control for setting review owner.")
            review = PeerReviewModel(self.env, resource.id)

            if not (Chrome(self.env).show_email_addresses
                    or 'EMAIL_VIEW' in req.perm(resource)):
                format_user = obfuscate_email_address
            else:
                format_user = lambda address: address
            current_owner = format_user(review['owner'])

            self.log.debug("Current owner is %s." % current_owner)

            selected_owner = req.args.get(id_, req.authname)

            hint = "The owner will be changed from %s" % current_owner

            owners = get_users(self.env)
            if not owners:
                owner = req.args.get(id_, req.authname)
                control = tag(u'%s ' % this_action['name'],
                              tag.input(type='text', id=id_,
                                        name=id_, value=owner))
            elif len(owners) == 1:
                owner = tag.input(type='hidden', id=id_, name=id_,
                                  value=owners[0])
                formatted_owner = format_user(owners[0])
                control = tag(u'%s ' % this_action['name'],
                              tag(formatted_owner, owner))
                if res_wf_state['owner'] != owners[0]:
                    hint = "The owner will be changed from %s to %s" % (current_owner, formatted_owner)
            else:
                control = tag(u'%s ' % this_action['name'], tag.select(
                        [tag.option(format_user(x), value=x,
                                    selected=(x == selected_owner or None))
                         for x in owners],
                        id=id_, name=id_))

            return control, hint

        return None, ''

    def perform_operation(self, req, action, operation, old_state, new_state, res_wf_state, resource):
        """Perform 'set_review_owner' operation on reviews."""

        self.log.debug("---> Performing operation %s while transitioning from %s to %s."
                       % (operation, old_state, new_state))
        new_owner = req.args.get('action_%s_operation_%s' % (action, operation), None)
        review = PeerReviewModel(self.env, int(resource.id))
        if review:
            review['owner'] = new_owner
            review.save_changes(author=req.authname)

    # IWorkflowTransitionListener

    def object_transition(self, res_wf_state, resource, action, old_state, new_state):
        if resource.realm == 'peerreviewer':
            reviewer = PeerReviewerModel(self.env, resource.id)
            reviewer['status'] = new_state
            # This is for updating the PeerReviewer object. The info is used for displaying the review state to the
            # review author. Note that this change is recorded in 'peerreviewer_change' by this.
            # The change is also recorded in the generic change table 'resourceworkflow_change' because of the
            # Resource object 'resource'.
            reviewer.save_changes(author=res_wf_state.authname,
                                  comment="State change to %s  for %s from object_transition() of %s"
                                                                        % (new_state, reviewer, resource))
        elif resource.realm == 'peerreview':
            review = PeerReviewModel(self.env, resource.id)
            review.change_status(new_state, res_wf_state.authname)

    # INavigationContributor

    def get_active_navigation_item(self, req):
        return 'peerreviewmain'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
        match = self.peerreview_view_re.match(req.path_info)
        if match:
            req.args['Review'] = match.group(1)
            return True
        # Deprecated legacy URL.
        if req.path_info == '/peerReviewView':
            self.env.log.info("Legacy URL 'peerReviewView' called from: %s", req.get_header('Referer'))
            return True

    def process_request(self, req):
        req.perm.require('CODE_REVIEW_VIEW')

        review_id = req.args.get('Review')
        if review_id is None or not review_id.isdigit():
            raise TracError(u"Invalid review ID supplied - unable to load page.")

        if req.method == 'POST':
            req.perm.require('CODE_REVIEW_DEV')
            if req.args.get('resubmit'):
                req.redirect(req.href.peerreviewnew(resubmit=review_id))
            elif req.args.get('followup'):
                req.redirect(req.href.peerreviewnew(resubmit=review_id, followup=1))
            elif req.args.get('modify'):
                req.redirect(req.href.peerreviewnew(resubmit=review_id, modify=1))

        # Add display_rev() function to files so we can properly display the revision
        # during template processing
        rm = RepositoryManager(self.env)
        files = self.get_files_for_review_id(req, review_id, True)
        for file in files:
            repos = rm.get_repository(file['repo'])
            file['display_rev'] = repos.display_rev

        # If this is not a changeset review 'reponame' and 'changeset' are empty strings.
        reponame, changeset = get_changeset_data(self.env, review_id)
        repos = rm.get_repository(reponame)
        short_rev = repos.display_rev(changeset) if repos else changeset
        data = {'review_files': files,
                'users': get_users(self.env),
                'show_ticket': self.show_ticket,
                'cycle': itertools.cycle,
                'review': self.get_review_by_id(req, review_id),
                'reviewer': list(PeerReviewerModel.select_by_review_id(self.env, review_id)),
                'repo': reponame,
                'display_rev': repos.display_rev if repos else lambda x: x,
                'changeset': changeset,
                'changeset_html': get_changeset_html(self.env, req, short_rev, repos)
                }

        # check to see if the user is a manager of this page or not
        if 'CODE_REVIEW_MGR' in req.perm:
            data['manager'] = True

        review = data['review']

        # A finished reviews can't be changed anymore except by a manager
        data['is_finished'] = review_is_finished(self.env.config, review)
        # A user can't change his voting for a reviewed review
        data['review_locked'] = review_is_locked(self.env.config, review, req.authname)
        # Used to indicate that a review is done. 'review_locked' is not suitable because it is false for the
        # author of a review even when the review is done.
        data['review_done'] = review_is_locked(self.env.config, review)
        data['finished_states_str'] = ', '.join(self.env.config.getlist("peerreview", "terminal_review_states"))

        # Add data for parent review if any
        self.add_parent_data(req, review, data)

        self.add_ticket_data(req, data)  # This updates dict 'data'

        # Actions for a reviewer. Each reviewer marks his progress on a review. The author
        # can see this progress in the user list. The possible actions are defined in trac.ini
        # as a workflow in [peerreviewer-resource_workflow]
        wflow = self.prepare_workflow_for_reviewer(req, review, data)
        if wflow:
            data['reviewer_workflow'] = wflow
        # Actions for the author of a review. The author may approve, disapprove or close a review.
        # The possible actions are defined in trac.ini as a workflow in [peerreview-resource_workflow]
        data['workflow'] = self.prepare_workflow_for_author(req, review, data)

        # For downloading in docx format
        self.add_docx_export_link(req, review_id)

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'common/css/ticket.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        Chrome(self.env).add_jquery_ui(req)  # For user icons
        add_ctxt_nav_items(req)
        if hasattr(Chrome, 'jenv'):
            return 'peerreview_view_jinja.html', data
        else:
            add_script(req, 'common/js/folding.js')
            return 'peerreview_view.html', data, None

    def add_parent_data(self, req, review, data):
        """Add inforamtion about parent review to dict 'data'. Do nothing if not parent."""
        def get_parent_file(curfile, par_files):
            fid = u"%s%s%s" % (curfile['path'], curfile['line_start'], curfile['line_end'])
            for parfile in par_files:
                tmp = u"%s%s%s" % (parfile['path'], parfile['line_start'], parfile['line_end'])
                if tmp == fid:
                    return parfile
            return None

        if review['parent_id'] != 0:
            data['parent_review'] = self.get_review_by_id(req, review['parent_id'])

            # Add display_rev() function to files so we can properly display the revision
            # during template processing
            rm = RepositoryManager(self.env)
            files = self.get_files_for_review_id(req, review['parent_id'], False)
            for file in files:
                repos = rm.get_repository(file['repo'])
                file['display_rev'] = repos.display_rev
            data['parent_files'] = files

            # Map files to parent files. Key is current file id, value is parent file object
            file_map = {}
            for rfile in data['review_files']:
                file_map[rfile['file_id']] = get_parent_file(rfile, data['parent_files'])
            data['file_map'] = file_map

    def prepare_workflow_for_reviewer(self, req, review, data):
        """
        :param req: Request object
        :param review: PeerReviewModel object representing the current review
        :return: a workflow suitable for directly inserting into the page. or None if we are not a reviewer.
        """
        # Actions for a reviewer. Each reviewer marks his progress on a review. The author
        # can see this progress in the user list. The possible actions are defined in trac.ini
        # as a workflow in [peerreviewer-resource_workflow]
        realm = 'peerreviewer'
        for reviewer in data['reviewer']:
            if reviewer['reviewer'] == req.authname:
                # Todo: 'canivote' should be obsolete by now
                if not data['is_finished'] and not data['review_done']:  # even author isn't allowed to change
                    data['canivote'] = True
                res = Resource(realm, str(reviewer['reviewer_id']))  # id must be a string
                wf_data = {'redirect': req.href.peerreviewview(review['review_id']),
                           'legend': _("Set review progress"),
                           'help': _("Setting the current state helps the review author to track progress.")}
                return ResourceWorkflowSystem(self.env).get_workflow_markup(req, self.workflow_base_href,
                                                                            realm, res, wf_data)
        return

    def prepare_workflow_for_author(self, req, review, data):
        """
        :param req: Request object
        :param review: PeerReviewModel object representing the current review
        :return: a workflow suitable for directly inserting into the page.
        """
        # Actions for the author of a review. The author may approve, disapprove or close a review.
        # The possible actions are defined in trac.ini as a workflow in [peerreview-resource_workflow]
        realm = 'peerreview'
        res = Resource(realm, str(review['review_id']))  # Must be a string (?)

        wf_data = {'redirect': req.href.peerreviewview(review['review_id']),
                   'legend': _("Set state of review (author or manager only)"),
                   'help': _("Closing a review means it is marked as obsolete and <strong>all associated data will be unavailable</strong>.")}
        return ResourceWorkflowSystem(self.env).get_workflow_markup(req, self.workflow_base_href, realm, res, wf_data)

    def add_docx_export_link(self, req, review_id):
        """Ad a download link for docx format if conversion is available.

        Note that python-docx must be installed for the link to show up.
        """
        conversions = Mimeview(self.env).get_supported_conversions('text/x-trac-peerreview')
        for key, name, ext, mime_in, mime_out, q, c in conversions:
            conversion_href = req.href("peerreview", format=key, reviewid=review_id)
            add_link(req, 'alternate', conversion_href, name, mime_out)


    def get_files_for_review_id(self, req, review_id, comments=False):
        """Get all file objects belonging to the given review id. Provide the number of comments if asked for.

        :param review_id: id of review as an int
        :param req: Request object
        :param comments: if True add information about comments as attributes to the file objects
        :return: list of ReviewFileModels
        """
        return get_files_for_review_id(self.env, req, review_id, comments)

        rev_files = list(ReviewFileModel.select_by_review(self.env, review_id))
        if comments:
            for file_ in rev_files:
                file_.num_comments = len(list(ReviewCommentModel.select_by_file_id(self.env, file_['file_id'])))
                my_comment_data = ReviewDataModel.comments_for_file_and_owner(self.env, file_['file_id'], req.authname)
                file_.num_notread = file_.num_comments - len([c_id for c_id, t, dat in my_comment_data if t == 'read'])
        return rev_files

    def get_review_by_id(self, req, review_id):
        """Get a PeerReviewModel for the given review id and prepare some additional data used by the template"""
        review = PeerReviewModel(self.env, review_id)
        review.html_notes = format_to_html(self.env, web_context(req), review['notes'])
        review.date = user_time(req, format_date, to_datetime(review['created']))
        if review['closed']:
            review.finish_date = user_time(req, format_date, to_datetime(review['closed']))
        else:
            review.finish_date = ''
        return review

    desc = u"""
Review [/peerreviewview/${review_id} ${review_name}] is finished.
=== Review

||= Name =|| ${review_name} ||
||= ID =|| ${review_id} ||
[[br]]
**Review Notes:**
${review_notes}

=== Files
||= File name =||= Comments =||
"""

    def add_ticket_data(self, req, data):
        """Create the ticket description for tickets created from the review page"""
        review = data['review']
        tmpl = Template(self.desc)
        txt = tmpl.substitute(review_name=review['name'], review_id=review['review_id'],
                                   review_notes="")  #review['notes'])

        try:
            for f in data['review_files']:
                txt += u"||[/peerreviewperform?IDFile=%s %s]|| %s ||%s" % \
                       (f['file_id'], f['path'], f.num_comments, CRLF)
        except KeyError:
            pass

        data['ticket_desc_wiki'] = self.create_preview(req, txt)
        data['ticket_desc'] = txt
        data['ticket_summary'] = u'Problems with Review "%s"' % review['name']

    def create_preview(self, req, text):
        resource = Resource('peerreview')
        context = web_context(req, resource)
        return format_to_html(self.env, context, text)
