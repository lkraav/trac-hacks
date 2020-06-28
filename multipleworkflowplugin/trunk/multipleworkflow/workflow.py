# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2015 ermal
# Copyright (C) 2015-2020 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import implements
from trac.ticket import model
from trac.ticket.default_workflow import ConfigurableTicketWorkflow, \
                                         parse_workflow_config
from trac.ticket.api import ITicketActionController
from trac.util import sub_val
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script

def get_workflow_config_by_type(config, ticket_type):
    """return the [ticket-workflow-type] session"""
    if ticket_type == 'default':
        raw_actions = list(config.options('ticket-workflow'))
    else:
        raw_actions = list(config.options('ticket-workflow-%s' % ticket_type))
    return parse_workflow_config(raw_actions)


def get_all_status(actions):
    """Calculate all states from the given list of actions.

    :return a list of states like 'new', 'closed' etc.
    """
    all_status = set()
    for attributes in actions.values():
        all_status.update(attributes['oldstates'])
        all_status.add(attributes['newstate'])
    all_status.discard('*')
    all_status.discard('')
    all_status.discard(None)
    return all_status


class MultipleWorkflowPlugin(ConfigurableTicketWorkflow):
    """Ticket action controller providing actions according to the ticket type.

    The [http://trac-hacks.org/wiki/MultipleWorkflowPlugin MultipleWorkflowPlugin]
    replaces the [TracWorkflow ConfigurableTicketWorkflow] used by Trac to
    control what actions can be performed on a ticket. The actions are
    specified in the {{{[ticket-workflow]}}} section of the TracIni file.

    With [http://trac-hacks.org/wiki/MultipleWorkflowPlugin MultipleWorkflowPlugin]
    Trac can read the workflow based on the type of a ticket. If a section for
    that ticket type doesn't exist, then it uses the default workflow.

    == Installation

    Enable the plugin by adding the following to your trac.ini file:

    {{{#!ini
    [components]
    multipleworkflow.* = enabled
    }}}
    Add the controller to the workflow controller list:

    {{{#!ini
    [ticket]
    workflow = MultipleWorkflowPlugin
    }}}

    == Example
    To define a different workflow for a ticket with type {{{Requirement}}}
    create a section in ''trac.ini'' called
    {{{[ticket-workflow-Requirement]}}} and add your workflow items:
    {{{#!ini
    [ticket-workflow-Requirement]
    leave = * -> *
    leave.default = 1
    leave.operations = leave_status

    approve = new, reopened -> approved
    approve.operations = del_resolution
    approve.permissions = TICKET_MODIFY

    reopen_verified = closed -> reopened
    reopen_verified.name= Reopen
    reopen_verified.operations = set_resolution
    reopen_verified.set_resolution=from verified
    reopen_verified.permissions = TICKET_MODIFY

    reopen_approved = approved -> reopened
    reopen_approved.name = Reopen
    reopen_approved.operations = set_resolution
    reopen_approved.set_resolution=from approved
    reopen_approved.permissions = TICKET_CREATE

    remove = new, reopened, approved, closed -> removed
    remove.name=Remove this Requirement permanently
    remove.operations = set_resolution
    remove.set_resolution= removed
    remove.permissions = TICKET_MODIFY

    verify = approved -> closed
    verify.name=Verifiy the Requirement and mark
    verify.operations = set_resolution
    verify.set_resolution=verified
    verify.permissions = TICKET_MODIFY
    }}}
    """
    implements(ITicketActionController, IRequestFilter)

    def __init__(self):
        self.type_actions = {}
        for t in self._ticket_types + ['default']:
            actions = self.get_all_actions_for_type(t)
            if actions:
                self.type_actions[t] = actions
        self.log.debug('Workflow actions at initialization: %s\n',
                       self.type_actions)

    @property
    def _ticket_types(self):
        return [enum.name for enum in model.Type.select(self.env)]

    def get_actions_by_type(self, ticket_type):
        """Return the ticket actions defined by the workflow for the given
        ticket type or {}.
        """
        try:
            return self.type_actions[ticket_type]
        except KeyError:
            return self.type_actions['default']

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        """Implements the special behaviour for requests with 'mw_refresh'
        argument should provide the proper list of available actions.
        """
        mine = ('/newticket', '/ticket', '/simpleticket')

        match = False
        for target in mine:
            if req.path_info.startswith(target):
                match = True
                break

        if match:
            if 'mw_refresh' in req.args:
                # This is our outosubmit handler for the type field requesting an update for the
                # ticket actions
                template = 'ticket_workflow.html'
            else:
                add_script(req, 'multipleworkflow/js/refresh_actions.js')
        return template, data, content_type

    # ITicketActionController methods

    def get_ticket_actions(self, req, ticket):
        ticket_type = req.args.get('field_type') or ticket['type']
        self.actions = self.get_actions_by_type(ticket_type)
        return super(MultipleWorkflowPlugin, self).\
               get_ticket_actions(req, ticket)

    def get_all_status_for_type(self, ticket_type):
        actions = self.get_actions_by_type(ticket_type)
        return get_all_status(actions)

    def get_all_status(self):
        """Return a list of all states described by the configuration.
        """
        # Default workflow
        all_status = self.get_all_status_for_type('default')

        # for all ticket types do
        for t in self._ticket_types:
            all_status.update(self.get_all_status_for_type(t))
        return all_status

    def render_ticket_action_control(self, req, ticket, action):
        self.actions = self.get_actions_by_type(ticket['type'])
        return super(MultipleWorkflowPlugin, self).\
               render_ticket_action_control(req, ticket, action)

    def get_ticket_changes(self, req, ticket, action):
        self.actions = self.get_actions_by_type(ticket['type'])
        return super(MultipleWorkflowPlugin, self). \
               get_ticket_changes(req, ticket, action)

    # Public methods (for other ITicketActionControllers that want to use
    #                 our config file and provide an operation for an action)

    def get_all_actions_for_type(self, ticket_type):
        actions = get_workflow_config_by_type(self.config, ticket_type)
        if not actions:
            return actions

        # Special action that gets enabled if the current status no longer
        # exists, as no other action can then change its state. (#5307/#11850)
        reset = {
            'default': 0,
            'label': 'reset',
            'newstate': 'new',
            'oldstates': [],
            'operations': ['reset_workflow'],
            'permissions': ['TICKET_ADMIN']
        }
        for key, val in reset.items():
            actions['_reset'].setdefault(key, val)

        for name, info in actions.iteritems():
            for val in ('<none>', '< none >'):
                sub_val(actions[name]['oldstates'], val, None)
            if not info['newstate']:
                self.log.warning("Ticket workflow action '%s' doesn't define "
                                 "any transitions", name)
        return actions

    def get_actions_by_operation(self, operation):
        """Return a list of all actions with a given operation
        (for use in the controller's get_all_status())
        """
        all_actions = {}
        all_actions.update(self.get_actions_by_type('default'))
        for t in self._ticket_types:
            all_actions.update(self.get_actions_by_type(t))
        self.actions = all_actions

        return super(MultipleWorkflowPlugin, self).\
               get_actions_by_operation(operation)

    def get_actions_by_operation_for_req(self, req, ticket, operation):
        """Return list of all actions with a given operation that are valid
        in the given state for the controller's get_ticket_actions().

        If state='*' (the default), all actions with the given operation are
        returned.
        """
        ticket_type = ticket._old.get('type', ticket['type'])
        self.actions = self.get_actions_by_type(ticket_type)

        return super(MultipleWorkflowPlugin, self).\
               get_actions_by_operation_for_req(req, ticket, operation)
