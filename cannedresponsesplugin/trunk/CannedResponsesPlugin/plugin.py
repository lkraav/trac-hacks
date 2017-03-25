# -*- coding: utf-8 -*-

from trac.core import implements, Component
from trac.ticket.api import ITicketActionController
from trac.ticket.default_workflow import parse_workflow_config
from trac.util.html import tag


class CannedResponseActionController(Component):
    """ Allow the admin user to select from a list of canned responses that add
    a comment to the ticket and put it in pending status.

    Don't forget to add `CannedResponseActionController` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    [ticket]
    workflow = ConfigurableTicketWorkflow, CannedResponseActionController

    Responses are read from the [canned-responses] section of the config file:

    [canned-responses]
    debuglog = new,pending -> pending
    debuglog.name = get a debug log
    debuglog.comment = Please follow [wiki:TipsForBugReports the instructions] to get a debug log and attach it to this ticket.
    debuglog.default = 1
    faq.permissions = TICKET_MODIFY
    faq = new,pending -> closed
    faq.name = get a debug log
    faq.comment = This is addressed in the [wiki:FAQ].
    faq.permissions = TICKET_ADMIN
    """
    implements(ITicketActionController)

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        self.canned_responses = self.get_canned_response_config()
        self.all_actions = set([])
        for resp in self.canned_responses:
           action = self.canned_responses[resp]
           action['id'] = resp
           if not '*' in action['oldstates']:
               self.all_actions.union(action['oldstates'])
           if not '*' in action['newstate']:
               self.all_actions.add(action['newstate'])
        self.log.debug('Canned Responses at initialization: %s\n' %
                       str(self.canned_responses))

    # ITicketActionController methods

    def get_ticket_actions(self, req, ticket):
        actions = []

        if 'status' in ticket._old:
            status = ticket._old['status']
        else:
            status = ticket['status']
        status = status or 'new'

        if len(self._get_avail_responses(req, status, ticket.resource)) > 0:
            actions.append((0, 'canned_response'))
        return actions

    def get_all_status(self):
        return self.all_actions

    def render_ticket_action_control(self, req, ticket, action):
        # Need to use the list of all status so you can't manually set
        # something to an invalid state.

        if 'status' in ticket._old:
            status = ticket._old['status']
        else:
            status = ticket['status']
        status = status or 'new'

        selected_val = req.args.get('canned_response_value')

        render_control = tag.select(
            [(tag.option(x['name'],
                        value=x['id'],
                        selected=selected_val and x['id'] == selected_val or \
                                 (not selected_val and x['default'] and 'selected' or
                                     None))) for x in self._get_avail_responses(req, status, ticket.resource)],
            id='canned_response_value', name='canned_response_value')
        return ("canned response:", render_control,
                "Choose a response to apply")


    def get_ticket_changes(self, req, ticket, action):
        canned_response = req.args.get('canned_response_value')
        this_action = self.canned_responses[canned_response]

        # Enforce permissions
        if not self._has_perms_for_action(req, this_action, ticket.resource):
            # The user does not have any of the listed permissions, so we won't
            # do anything.
            return {}

        updated = {}

        # Status changes
        status = this_action['newstate']
        if status != '*':
            updated['status'] = status

        if this_action.has_key('comment'):
            oldcomment = req.args.get('comment')
            if not oldcomment or oldcomment.find(this_action['comment']) == -1:
                req.args['comment'] = "%s%s%s" % (this_action['comment'], oldcomment and "[[BR]]" or "", oldcomment or "")

        if this_action.has_key('resolution'):
            if this_action['resolution']:
               updated['resolution'] = this_action['resolution']

        if this_action.has_key('milestone'):
            if this_action['milestone']:
               updated['milestone'] = this_action['milestone']

        if this_action.has_key('type'):
            if this_action['type']:
               updated['type'] = this_action['type']

        #for operation in this_action['operations']:
            #I can't think of any useful operations offhand!

        return updated

    def apply_action_side_effects(self, req, ticket, action):
        pass

    # Internal Methods

    def get_canned_response_config(self):
        """Usually passed self.config, this will return the parsed ticket-workflow
        section.
        """
        raw_actions = list(self.config.options('canned-responses'))
        #cheat and reuse the workflow parser
        responses = parse_workflow_config(raw_actions)
        return responses

    def _has_perms_for_action(self, req, action, resource):
        required_perms = action['permissions']
        if required_perms:
            for permission in required_perms:
                if permission in req.perm(resource):
                    break
            else:
                # The user does not have any of the listed permissions
                return False
        return True

    def _get_avail_responses(self, req, status, resource):
        actions = []
        for resp in self.canned_responses:
           action = self.canned_responses[resp]
           if ('*' in action['oldstates'] or
                    status in action['oldstates']) and \
                    self._has_perms_for_action(req, action, resource):
                actions.append(action)

        return actions
