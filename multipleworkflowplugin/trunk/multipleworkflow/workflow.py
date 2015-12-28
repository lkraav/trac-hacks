# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2015
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag

from trac.core import TracError, implements
from trac.perm import PermissionSystem
from trac.ticket import model
from trac.ticket.default_workflow import ConfigurableTicketWorkflow, parse_workflow_config
from trac.ticket.api import ITicketActionController, TicketSystem
from trac.ticket.model import Resolution
from trac.util.compat import set
from trac.util.text import obfuscate_email_address
from trac.util.translation import _, tag_
from trac.web.chrome import Chrome


def get_workflow_config_by_type(config, tipo_ticket):
    """return the [ticket-workflow-type] session"""
    raw_actions = list(config.options('ticket-workflow-%s' % tipo_ticket))
    actions = parse_workflow_config(raw_actions)
    if actions and '_reset' not in actions:
        actions['_reset'] = {
            'default': 0,
            'name': 'reset',
            'newstate': 'new',
            'oldstates': [],  # Will not be invoked unless needed
            'operations': ['reset_workflow'],
            'permissions': []}
    return actions


def calc_status(actions):
    """Calculate all states from the given list of actions.

    :return a list of states like 'new', 'closed' etc.
    """
    all_status = set()
    for action_name, action_info in actions.items():
        all_status.update(action_info['oldstates'])
        all_status.add(action_info['newstate'])
    all_status.discard('*')
    all_status.discard('')
    return all_status


class MultipleWorkflowPlugin(ConfigurableTicketWorkflow):
    """Ticket action controller providing actions according to the ticket type.

    == ==
    The [http://trac-hacks.org/wiki/MultipleWorkflowPlugin MultipleWorkflowPlugin] replaces the
    [TracWorkflow ConfigurableTicketWorkflow] used by Trac to control what actions can be performed on a ticket.
    The actions are specified in the {{{[ticket-workflow]}}} section of the TracIni file.

    With [http://trac-hacks.org/wiki/MultipleWorkflowPlugin MultipleWorkflowPlugin] Trac can read the workflow based
    on the type of a ticket. If a section for that ticket type doesn't exist, then it uses the default workflow.

    == Installation

    Enable the plugin by adding the following to your trac.ini file:

    {{{
    [components]
    multipleworkflow.* = enabled
    }}}
    Add the controller to the workflow controller list:

    {{{
    [ticket]
    workflow = MultipleWorkflowPlugin
    }}}

    == Example
    To define a different workflow for a ticket with type {{{Requirement}}} create a section in ''trac.ini'' called
    {{{[ticket-workflow-Requirement]}}} and add your workflow items:
    {{{
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
    implements(ITicketActionController)

    def __init__(self, *args, **kwargs):
        # This call creates self.actions
        super(MultipleWorkflowPlugin, self).__init__(args, kwargs)
        self.type_actions = {}
        # for all ticket types do
        for t in [enum.name for enum in model.Type.select(self.env)]:
            actions = get_workflow_config_by_type(self.config, t)
            if actions:
                self.type_actions[t] = actions

    def get_workflow_actions_by_type(self, tkt_type):
        """Return the ticket actions defined by the workflow for the given ticket type or {}."""
        try:
            actions = self.type_actions[tkt_type]
        except KeyError:
            actions = {}
        return actions

    # ITicketActionController methods

    def get_ticket_actions(self, req, ticket):
        """Returns a list of (weight, action) tuples that are valid for this
        request and this ticket."""
        # Get the list of actions that can be performed

        # Determine the current status of this ticket.  If this ticket is in
        # the process of being modified, we need to base our information on the
        # pre-modified state so that we don't try to do two (or more!) steps at
        # once and get really confused.
        status = ticket._old.get('status', ticket['status']) or 'new'

        # Calculate actions for ticket type. If no wtype workflow exists use the default workflow.
        tipo_ticket = ticket._old.get('type', ticket['type'])
        actions = self.get_workflow_actions_by_type(tipo_ticket)
        if not actions:
            actions = self.actions

        ticket_perm = req.perm(ticket.resource)
        allowed_actions = []
        for action_name, action_info in actions.items():
            oldstates = action_info['oldstates']
            if oldstates == ['*'] or status in oldstates:
                # This action is valid in this state.  Check permissions.
                required_perms = action_info['permissions']
                if self._is_action_allowed(ticket_perm, required_perms):
                    allowed_actions.append((action_info['default'],
                                            action_name))
        if not (status in ['new', 'closed'] or
                status in TicketSystem(self.env).get_all_status()) \
                and 'TICKET_ADMIN' in ticket_perm:
            # State no longer exists - add a 'reset' action if admin.
            allowed_actions.append((0, '_reset'))

        # Check if the state is valid for the current ticket type. If not offer the action to reset it.
        type_status = self.get_all_status_for_type(tipo_ticket)
        if not type_status:
            type_status = calc_status(self.actions)
        if status not in type_status and (0, '_reset') not in allowed_actions:
                allowed_actions.append((0, '_reset'))
        return allowed_actions

    def get_all_status_for_type(self, t_type):
        actions = self.get_workflow_actions_by_type(t_type)
        return calc_status(actions)

    def get_all_status(self):
        """Return a list of all states described by the configuration.
        """
        # Default workflow
        all_status = calc_status(self.actions)

        # for all ticket types do
        for t in [enum.name for enum in model.Type.select(self.env)]:
            all_status.update(self.get_all_status_for_type(t))
        return all_status

    def render_ticket_action_control(self, req, ticket, action):

        self.log.debug('render_ticket_action_control: action "%s"' % action)

        tipo_ticket = ticket._old.get('type', ticket['type'])
        actions = self.get_workflow_actions_by_type(tipo_ticket)
        if not actions:
            actions = self.actions

        this_action = actions[action]
        status = this_action['newstate']
        operations = this_action['operations']
        current_owner = ticket._old.get('owner', ticket['owner'] or '(none)')
        if not (Chrome(self.env).show_email_addresses
                or 'EMAIL_VIEW' in req.perm(ticket.resource)):
            format_user = obfuscate_email_address
        else:
            format_user = lambda address: address
        current_owner = format_user(current_owner)

        control = []  # default to nothing
        hints = []
        if 'reset_workflow' in operations:
            control.append(tag("from invalid state "))
            hints.append(_("Current state no longer exists"))
        if 'del_owner' in operations:
            hints.append(_("The ticket will be disowned"))
        if 'set_owner' in operations:
            id = 'action_%s_reassign_owner' % action
            selected_owner = req.args.get(id, req.authname)

            if 'set_owner' in this_action:
                owners = [x.strip() for x in
                          this_action['set_owner'].split(',')]
            elif self.config.getbool('ticket', 'restrict_owner'):
                perm = PermissionSystem(self.env)
                owners = perm.get_users_with_permission('TICKET_MODIFY')
                owners.sort()
            else:
                owners = None

            if owners is None:
                owner = req.args.get(id, req.authname)
                control.append(tag_('to %(owner)s',
                                    owner=tag.input(type='text', id=id,
                                                    name=id, value=owner)))
                hints.append(_("The owner will be changed from "
                               "%(current_owner)s",
                               current_owner=current_owner))
            elif len(owners) == 1:
                owner = tag.input(type='hidden', id=id, name=id,
                                  value=owners[0])
                formatted_owner = format_user(owners[0])
                control.append(tag_('to %(owner)s ',
                                    owner=tag(formatted_owner, owner)))
                if ticket['owner'] != owners[0]:
                    hints.append(_("The owner will be changed from "
                                   "%(current_owner)s to %(selected_owner)s",
                                   current_owner=current_owner,
                                   selected_owner=formatted_owner))
            else:
                control.append(tag_('to %(owner)s', owner=tag.select(
                    [tag.option(x, value=x,
                                selected=(x == selected_owner or None))
                     for x in owners],
                    id=id, name=id)))
                hints.append(_("The owner will be changed from "
                               "%(current_owner)s",
                               current_owner=current_owner))
        if 'set_owner_to_self' in operations and \
                ticket._old.get('owner', ticket['owner']) != req.authname:
            hints.append(_("The owner will be changed from %(current_owner)s "
                           "to %(authname)s", current_owner=current_owner,
                           authname=req.authname))
        if 'set_resolution' in operations:
            if 'set_resolution' in this_action:
                resolutions = [x.strip() for x in
                               this_action['set_resolution'].split(',')]
            else:
                resolutions = [val.name for val in Resolution.select(self.env)]
            if not resolutions:
                raise TracError(_("Your workflow attempts to set a resolution "
                                  "but none is defined (configuration issue, "
                                  "please contact your Trac admin)."))
            id_ = 'action_%s_resolve_resolution' % action
            if len(resolutions) == 1:
                resolution = tag.input(type='hidden', id=id_, name=id_,
                                       value=resolutions[0])
                control.append(tag_('as %(resolution)s',
                                    resolution=tag(resolutions[0],
                                                   resolution)))
                hints.append(_("The resolution will be set to %(name)s",
                               name=resolutions[0]))
            else:
                selected_option = req.args.get(id_, TicketSystem(self.env).default_resolution)
                control.append(tag_('as %(resolution)s',
                                    resolution=tag.select(
                                    [tag.option(x, value=x, selected=(x == selected_option or None))
                                     for x in resolutions],
                                     id=id_, name=id_)))
                hints.append(_("The resolution will be set"))
        if 'del_resolution' in operations:
            hints.append(_("The resolution will be deleted"))
        if 'leave_status' in operations:
            control.append(_('as %(status)s ',
                             status=ticket._old.get('status',
                                                    ticket['status'])))
        else:
            if status != '*':
                hints.append(_("Next status will be '%(name)s'", name=status))
        return this_action['name'], tag(*control), '. '.join(hints)

    def get_ticket_changes(self, req, ticket, action):
        tipo_ticket = ticket._old.get('type', ticket['type'])
        actions = self.get_workflow_actions_by_type(tipo_ticket)
        if not actions:
            actions = self.actions
        this_action = actions[action]

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

        for operation in this_action['operations']:
            if operation == 'reset_workflow':
                updated['status'] = 'new'
            elif operation == 'del_owner':
                updated['owner'] = ''
            elif operation == 'set_owner':
                newowner = req.args.get('action_%s_reassign_owner' % action,
                                        this_action.get('set_owner', '').strip())
                # If there was already an owner, we get a list, [new, old],
                # but if there wasn't we just get new.
                if type(newowner) == list:
                    newowner = newowner[0]
                updated['owner'] = newowner
            elif operation == 'set_owner_to_self':
                updated['owner'] = req.authname
            elif operation == 'del_resolution':
                updated['resolution'] = ''
            elif operation == 'set_resolution':
                newresolution = req.args.get('action_%s_resolve_resolution' %
                                             action,
                                             this_action.get('set_resolution', '').strip())
                updated['resolution'] = newresolution

            # leave_status is just a no-op here, so we don't look for it.
        return updated

    # Public methods (for other ITicketActionControllers that want to use
    #                 our config file and provide an operation for an action)

    def get_actions_by_operation(self, operation):
        """Return a list of all actions with a given operation
        (for use in the controller's get_all_status())
        """
        all_actions = {}
        # Default workflow
        all_actions.update(self.actions)
        # for all ticket types do
        for t in [enum.name for enum in model.Type.select(self.env)]:
            all_actions.update(self.get_workflow_actions_by_type(t))

        actions = [(info['default'], action) for action, info
                   in all_actions.items()
                   if operation in info['operations']]
        return actions

    def get_actions_by_operation_for_req(self, req, ticket, operation):
        """Return list of all actions with a given operation that are valid
        in the given state for the controller's get_ticket_actions().

        If state='*' (the default), all actions with the given operation are
        returned.
        """
        tipo_ticket = ticket._old.get('type', ticket['type'])
        actions = self.get_workflow_actions_by_type(tipo_ticket)
        if not actions:
            actions = self.actions

        # Be sure to look at the original status.
        status = ticket._old.get('status', ticket['status'])
        actions = [(info['default'], action) for action, info in actions.items()
                   if operation in info['operations'] and
                   ('*' in info['oldstates'] or status in info['oldstates']) and
                   self._has_perms_for_action(req, info, ticket.resource)]
        return actions
