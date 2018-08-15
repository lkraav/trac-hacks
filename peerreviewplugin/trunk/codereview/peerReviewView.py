#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

# Provides functionality for view code review page
# Works with peerReviewView.html

import itertools
from string import Template
from trac.config import BoolOption, ListOption
from trac.core import Component, implements, TracError
from trac.mimeview import Context
from trac.mimeview.api import Mimeview
from trac.resource import Resource
from trac.util import format_date
from trac.util.html import html as tag
from trac.util.text import CRLF, obfuscate_email_address
from trac.web.chrome import add_link, add_stylesheet, Chrome, INavigationContributor
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to, format_to_html
from model import Comment, get_users, \
    PeerReviewerModel, PeerReviewModel, ReviewFileModel, ReviewDataModel
from peerReviewMain import add_ctxt_nav_items, web_context_compat
from tracgenericworkflow.api import IWorkflowOperationProvider, IWorkflowTransitionListener, ResourceWorkflowSystem
from util import review_is_finished, review_is_locked

try:
    from trac.web.chrome import web_context
except ImportError:
    web_context = web_context_compat


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
            reviewer.save_changes(author=res_wf_state.authname)
        elif resource.realm == 'peerreview':
            review = PeerReviewModel(self.env, resource.id)
            review.change_status(new_state, res_wf_state.authname)

    # INavigationContributor

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewView'

    def process_request(self, req):
        def get_review_by_id(review_id):
            """Get a PeerReviewModel for the given review id and prepare some additional data used by the template"""
            review = PeerReviewModel(self.env, review_id)
            review.html_notes = format_to_html(self.env, Context.from_request(req), review['notes'])
            review.date = format_date(review['created'])
            return review
        def get_files_for_review_id(review_id, comments=False):
            """Get all files belonging to the given review id. Provide the number of comments if asked for."""
            rfm = ReviewFileModel(self.env)
            rfm.clear_props()
            rfm['review_id'] = review_id
            rev_files = list(rfm.list_matching_objects())
            if comments:
                for f in rev_files:
                    f.num_comments = len(Comment.select_by_file_id(self.env, f['file_id']))
                    my_comment_data = ReviewDataModel.comments_for_file_and_owner(self.env, f['file_id'], req.authname)
                    f.num_notread = f.num_comments - len([c_id for c_id, t, dat in my_comment_data if t == 'read'])
            return rev_files

        req.perm.require('CODE_REVIEW_DEV')

        data = {}
        # check to see if the user is a manager of this page or not
        if 'CODE_REVIEW_MGR' in req.perm:
            data['manager'] = True

        # review_id argument checking
        review_id = req.args.get('Review')
        if review_id is None or not review_id.isdigit():
            raise TracError(u"Invalid review ID supplied - unable to load page.")

        if req.method == 'POST':
            if req.args.get('resubmit'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id))
            elif req.args.get('followup'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id, followup=1))
            elif req.args.get('modify'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id, modify=1))

        data['review_files'] = get_files_for_review_id(review_id, True)
        data['users'] = get_users(self.env)
        data['show_ticket'] = self.show_ticket

        review = get_review_by_id(review_id)
        data['review'] = review

        # A finished review can't be changed anymore except by a manager
        data['is_finished'] = review_is_finished(self.env.config, review)
        # A user can't change his voting for a reviewed review
        data['review_locked'] = review_is_locked(self.env.config, review, req.authname)
        # Used to indicate that a review is done. 'review_locked' is not suitable because it is false for the
        # author of a review even when the review is done.
        data['review_done'] = review_is_locked(self.env.config, review)
        data['finished_states_str'] = ', '.join(self.env.config.getlist("peerreview", "terminal_review_states"))
        # Parent review if any
        if review['parent_id'] != 0:
            data['parent_review'] = get_review_by_id(review['parent_id'])
            par_files = get_files_for_review_id(review['parent_id'], False)
            data['parent_files'] = par_files

            # Map files to parent files. Key is current file id, value is parent file object

            def get_parent_file(rfile, par_files):
                fid = u"%s%s%s" % (rfile['path'], rfile['line_start'], rfile['line_end'])
                for f in par_files:
                    tmp = u"%s%s%s" % (f['path'], f['line_start'], f['line_end'])
                    if tmp == fid:
                        return f
                return None
            file_map = {}
            for f in data['review_files']:
                file_map[f['file_id']] = get_parent_file(f, par_files)

            data['file_map'] = file_map

        self.create_ticket_data(req, data)
        url = '.'
        # Actions for a reviewer. Each reviewer marks his progress on a review. The author
        # can see this progress in the user list. The possible actions are defined in trac.ini
        # as a workflow in [peerreviewer-resource_workflow]
        realm = 'peerreviewer'
        res = None

        rm = PeerReviewerModel(self.env)
        rm.clear_props()
        rm['review_id'] = review_id
        reviewers = list(rm.list_matching_objects())
        data['reviewer'] = reviewers

        for reviewer in reviewers:
            if reviewer['reviewer'] == req.authname:
                res = Resource(realm, str(reviewer['reviewer_id']))  # id must be a string
                if not data['is_finished'] and not data['review_done']:  # even author isn't allowed to change
                    data['canivote'] = True
                break
        if res:
            data['reviewer_workflow'] = ResourceWorkflowSystem(self.env).\
                get_workflow_markup(req, url, realm, res, {'redirect': req.href.peerReviewView(Review=review_id)})

        # Actions for the author of a review. The author may approve, disapprove or close a review.
        # The possible actions are defined in trac.ini as a workflow in [peerreview-resource_workflow]
        realm = 'peerreview'
        res = Resource(realm, str(review['review_id']))  # Must be a string
        data['workflow'] = ResourceWorkflowSystem(self.env).\
            get_workflow_markup(req, url, realm, res, {'redirect': req.href.peerReviewView(Review=review_id)})

        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'common/css/ticket.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_ctxt_nav_items(req)

        # For downloading in docx format
        conversions = Mimeview(self.env).get_supported_conversions('text/x-trac-peerreview')
        for key, name, ext, mime_in, mime_out, q, c in conversions:
            conversion_href = req.href("peerreview", format=key, reviewid=review_id)
            add_link(req, 'alternate', conversion_href, name, mime_out)

        return 'peerReviewView.html', data, None

    desc = u"""
Review [/peerReviewView?Review=${review_id} ${review_name}] is finished.
=== Review

||= Name =|| ${review_name} ||
||= ID =|| ${review_id} ||
[[br]]
**Review Notes:**
${review_notes}

=== Files
||= File name =||= Comments =||
"""

    def create_ticket_data(self, req, data):
        """Create the ticket description for tickets created from the review page"""
        txt = u""
        review = data['review']
        tmpl = Template(self.desc)
        txt = tmpl.substitute(review_name=review['name'], review_id=review['review_id'],
                                   review_notes="")  #review['notes'])

        try:
            for f in data['review_files']:
                txt += u"||[/peerReviewPerform?IDFile=%s %s]|| %s ||%s" % \
                       (f['file_id'], f['path'], f.num_comments, CRLF)
        except KeyError:
            pass

        data['ticket_desc_wiki'] = self.create_preview(req, txt)
        data['ticket_desc'] = txt
        data['ticket_summary'] = u'Problems with Review "%s"'% review['name']

    def create_preview(self, req, text):
        resource = Resource('peerreview')
        context = web_context(req, resource)
        return format_to_html(self.env, context, text)
