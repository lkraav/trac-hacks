# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Jean-Philippe Save
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.util.html import html as tag
from trac.ticket.api import ITicketActionController
from trac.ticket.default_workflow import ConfigurableTicketWorkflow, \
    get_workflow_config
from trac.ticket.model import Ticket


class AssignReviewerOperation(Component):
    """Provides the assignment of a Reviewer.

    This is action controllers that set/clear a reviewer field.

    Do not forget to add `AssignReviewerOperation` to the workflow option in
    [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,AssignReviewerOperation
    """
    implements(IEnvironmentSetupParticipant, ITicketActionController)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment(self.config)

    def environment_needs_upgrade(self, db=None):
        return _ticket_field_need_upgrade(self.config)

    def upgrade_environment(self, db=None):
        _do_ticket_field_upgrade(self.config)

    # ITicketActionController methods

    def get_ticket_actions(self, req, ticket):
        """Returns all actions that have these new operations: 'set_reviewer'
        and 'del_reviewer'.
        """
        controller = ConfigurableTicketWorkflow(self.env)
        actions = []
        for operation in ['set_reviewer', 'del_reviewer']:
            actions.extend(controller.get_actions_by_operation_for_req(
                    req, ticket, operation))
        return actions

    def get_all_status(self):
        """This action controller is not related to status."""
        return []

    def render_ticket_action_control(self, req, ticket, action):
        """Add comments and controls for actions that have the new operations:
        'set_reviewer' and 'del_reviewer'

        'set_reviewer' operation adds a textbox to the action to set the
        reviewer field.
        """
        self.log.debug('render_ticket_action_control: action "%s"' % action)

        # Retrieve operations for this action
        actions = get_workflow_config(self.config)
        this_action = actions[action]
        operations = this_action['operations']

        # Retrieve the current reviewer name for this ticket
        current_reviewer = ticket._old.get('reviewer',
                                           ticket['reviewer'] or '(none)')

        # Needed for textbox
        control = []
        # Needed for comment
        hints = ""

        # For del_reviewer operation, no control is needed, only a comment
        if 'del_reviewer' in operations:
            hints = "The reviewer will be removed"

        # For set_reviewer operation, in addition of the comment that informs
        # that the reviewer will change from the current one, add a textbox
        # that contains by default the login name
        elif 'set_reviewer' in operations:
            id = 'set_reviewer_%s_result' % action
            reviewer = req.args.get(id, req.authname)
            control = tag.input(type='text', value=reviewer, id=id, name=id)
            hints = ('The reviewer will be changed from "%s"' %
                     current_reviewer)

        return this_action['name'], control, hints

    def get_ticket_changes(self, req, ticket, action):
        """Set or clear the reviewer field according to the requested
        operation ('set_reviewer' or 'del_reviewer').
        """

        # Retrieve operations for this action
        actions = get_workflow_config(self.config)
        this_action = actions[action]
        operations = this_action['operations']

        # To store changes on ticket
        changed_fields = {}

        # For del_reviewer operation: clear the reviewer field
        if 'del_reviewer' in operations:
            changed_fields = {'reviewer': ''}

        # For set_reviewer operation: set the reviewer field with by default
        # the login name
        elif 'set_reviewer' in operations:
            id = 'set_reviewer_%s_result' % action
            reviewer = req.args.get(id, req.authname)
            changed_fields = {'reviewer': reviewer}

        return changed_fields

    def apply_action_side_effects(self, req, ticket, action):
        """This action controller has no side effects."""
        pass


def _ticket_field_need_upgrade(config):
    """Check the reviewer field presence"""
    return not config.get("ticket-custom", "reviewer")


def _do_ticket_field_upgrade(config):
    """Set the reviewer field"""
    config.set("ticket-custom", "reviewer", "text")
    config.set("ticket-custom", "reviewer.label", "Reviewer")
    config.save()
