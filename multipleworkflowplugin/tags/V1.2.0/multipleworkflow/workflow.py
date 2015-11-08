# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2015
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag

from trac.config import Configuration
from trac.core import Component, TracError, implements
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionSystem
from trac.ticket import model
from trac.ticket.api import ITicketActionController, TicketSystem
from trac.util.compat import set
from trac.util.translation import _


# -- supporting procedures
def parse_workflow_config(rawactions):
    """Given a list of options from [ticket-workflow-xxxxx] create the
    inner workflow model and normalize it's values"""
    actions = {}
    for option, value in rawactions:
        parts = option.split('.')
        action = parts[0]
        if action not in actions:
            actions[action] = {}
        if len(parts) == 1:
            # Base name, of the syntax: old,states,here -> newstate
            try:
                oldstates, newstate = [x.strip() for x in value.split('->')]
            except ValueError:
                raise Exception('Bad option "%s"' % (option, ))
            actions[action]['newstate'] = newstate
            actions[action]['oldstates'] = oldstates
        else:
            action, attribute = option.split('.')
            actions[action][attribute] = value
    # Fill in the defaults for every action, and normalize them to the desired types
    for action, attributes in actions.items():
        # Default the 'name' attribute to the name used in the ini file
        if 'name' not in attributes:
            attributes['name'] = action
        # If not specified, an action is not the default.
        if 'default' not in attributes:
            attributes['default'] = 0
        else:
            attributes['default'] = int(attributes['default'])
        # If operations are not specified, that means no operations
        if 'operations' not in attributes:
            attributes['operations'] = []
        else:
            attributes['operations'] = [a.strip() for a in
                                        attributes['operations'].split(',')]
        # If no permissions are specified, then no permissions are needed
        if 'permissions' not in attributes:
            attributes['permissions'] = []
        else:
            attributes['permissions'] = [a.strip() for a in
                                         attributes['permissions'].split(',')]
        # Normalize the oldstates
        attributes['oldstates'] = [x.strip() for x in
                                   attributes['oldstates'].split(',')]
    return actions


def get_workflow_config_default(config):
    """return the [ticket-workflow] session """
    raw_actions = list(config.options('ticket-workflow')) 
    actions = parse_workflow_config(raw_actions)
    if '_reset' not in actions:
        actions['_reset'] = {
            'default': 0,
            'name': 'reset',
            'newstate': 'new',
            'oldstates': [],  # Will not be invoked unless needed
            'operations': ['reset_workflow'],
            'permissions': []}
    return actions


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


def load_workflow_config_snippet(config, filename):
    """Loads the ticket-workflow section from the given file (expected to be in
    the 'workflows' tree) into the provided config.
    """
    from pkg_resources import resource_filename
    filename = resource_filename('trac.ticket', 'workflows/%s' % filename)
    new_config = Configuration(filename)
    for name, value in new_config.options('ticket-workflow'):
        config.set('ticket-workflow', name, value)

def calc_status(actions):
    """Calculate all states from the given list of actions.

    :return a list of states like 'new', 'closed' etc.
    """
    all_status = set()
    for action_name, action_info in actions.items():
        all_status.update(action_info['oldstates'])
        all_status.add(action_info['newstate'])
    all_status.discard('*')
    return all_status


class MultipleWorkflowPlugin(Component):
    """Ticket action controller providing actions according to the ticket type.

    == ==
    The [http://trac-hacks.org/wiki/MultipleWorkflowPlugin MultipleWorkflowPlugin] replaces the
    [TracWorkflow ConfigurableTicketWorkflow] used by Trac to control what actions can be performed on a ticket.
    The actions are specified in the {{{[ticket-workflow]}}} section of the TracIni file.

    With [http://trac-hacks.org/wiki/MultipleWorkflowPlugin MultipleWorkflowPlugin] Trac can read the workflow based
    on the type of a ticket. If a section for that ticket type doesn't exist, then it uses the default workflow.

    == Example ==
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
    implements(ITicketActionController, IEnvironmentSetupParticipant)

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        self.actions = get_workflow_config_default(self.config)
        self.log.debug('Workflow default actions at initialization: %s\n' %
                       str(self.actions))

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        if not 'ticket-workflow' in self.config.sections():
            load_workflow_config_snippet(self.config, 'basic-workflow.ini')
            self.config.save()
            self.actions = get_workflow_config_default(self.config)

    def environment_needs_upgrade(self, db):
        return not list(self.config.options('ticket-workflow'))

    def upgrade_environment(self, db):
        """Insert a [ticket-workflow] section using the original-workflow"""
        load_workflow_config_snippet(self.config, 'original-workflow.ini')
        self.config.save()
        self.actions = get_workflow_config_default(self.config)
        info_message = """

==== Upgrade Notice ====

The ticket Workflow is now configurable.

Your environment has been upgraded, but configured to use the original
workflow. It is recommended that you look at changing this configuration to use
basic-workflow. 

Read TracWorkflow for more information (don't forget to 'wiki upgrade' as well)

"""
        self.log.info(info_message.replace('\n', ' ').replace('==', ''))
        print info_message

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

        #it doesn't exist the requested session it returns the default workflow
        tipo_ticket = ticket._old.get('type', ticket['type'])
        actions = get_workflow_config_by_type(self.config, tipo_ticket)
        if not actions:
            actions = get_workflow_config_default(self.config)

        allowed_actions = []
        for action_name, action_info in actions.items():
            oldstates = action_info['oldstates']
            if oldstates == ['*'] or status in oldstates:
                # This action is valid in this state.  Check permissions.
                allowed = 0
                required_perms = action_info['permissions']
                if required_perms:
                    for permission in required_perms:
                        if permission in req.perm(ticket.resource):
                            allowed = 1
                            break
                else:
                    allowed = 1
                if allowed:
                    allowed_actions.append((action_info['default'],
                                            action_name))
        if not (status in ['new', 'closed'] or
                status in TicketSystem(self.env).get_all_status()) \
                and 'TICKET_ADMIN' in req.perm(ticket.resource):
            # State no longer exists - add a 'reset' action if admin.
            allowed_actions.append((0, '_reset'))

        # Check if the state is valid for the current ticket type. If not offer the action to reset it.
        type_status = self.get_all_status_for_type(tipo_ticket)
        if not type_status:
            type_status = self._calc_status(get_workflow_config_default(self.config))
        if status not in type_status and (0, '_reset') not in allowed_actions:
                allowed_actions.append((0, '_reset'))
        return allowed_actions


    def _calc_status(self, actions):
        """Calculate all states from the given list of actions.

        :return a list of states like 'new', 'closed' etc.
        """
        return calc_status(actions)


    def get_all_status_for_type(self, t_type):
        actions = get_workflow_config_by_type(self.config, t_type)
        return self._calc_status(actions)


    def get_all_status(self):
        """Return a list of all states described by the configuration.
        """
        # Default workflow
        all_status = self._calc_status(get_workflow_config_default(self.config))

        # for all ticket types do
        for t in [enum.name for enum in model.Type.select(self.env)]:
            all_status.update(self.get_all_status_for_type(t))
        return all_status


    def render_ticket_action_control(self, req, ticket, action):
        self.log.debug('render_ticket_action_control: action "%s"' % action)

        tipo_ticket = ticket._old.get('type', ticket['type'])
        actions = get_workflow_config_by_type(self.config, tipo_ticket)
        if not actions:
            actions = get_workflow_config_default(self.config)

        this_action = actions[action]
        status = this_action['newstate']
        operations = this_action['operations']
        current_owner = ticket._old.get('owner', ticket['owner'] or '(none)')

        control = []
        hints = []
        if 'reset_workflow' in operations:
            control.append(tag("from invalid state "))
            hints.append(_("Current state no longer exists"))
        if 'del_owner' in operations:
            hints.append(_("The ticket will be disowned"))
        if 'set_owner' in operations:
            id = 'action_%s_reassign_owner' % action
            selected_owner = req.args.get(id, req.authname)

            if this_action.has_key('set_owner'):
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
                control.append(tag(['to ', tag.input(type='text', id=id,
                                                     name=id, value=owner)]))
                hints.append(_("The owner will change from %(current_owner)s",
                               current_owner=current_owner))
            elif len(owners) == 1:
                control.append(tag('to %s ' % owners[0]))
                if ticket['owner'] != owners[0]:
                    hints.append(_("The owner will change from "
                                   "%(current_owner)s to %(selected_owner)s",
                                   current_owner=current_owner,
                                   selected_owner=owners[0]))
            else:
                control.append(tag([_("to "), tag.select(
                    [tag.option(x, selected=(x == selected_owner or None))
                     for x in owners],
                    id=id, name=id)]))
                hints.append(_("The owner will change from %(current_owner)s",
                               current_owner=current_owner))
        if 'set_owner_to_self' in operations and \
                ticket._old.get('owner', ticket['owner']) != req.authname:
            hints.append(_("The owner will change from %(current_owner)s "
                           "to %(authname)s", current_owner=current_owner,
                           authname=req.authname))
        if 'set_resolution' in operations:
            if 'set_resolution' in this_action:
                resolutions = [x.strip() for x in
                               this_action['set_resolution'].split(',')]
            else:
                resolutions = [val.name for val in
                               model.Resolution.select(self.env)]
            if not resolutions:
                raise TracError(_("Your workflow attempts to set a resolution "
                                  "but none is defined (configuration issue, "
                                  "please contact your Trac admin)."))
            if len(resolutions) == 1:
                control.append(tag('as %s' % resolutions[0]))
                hints.append(_("The resolution will be set to %s") %
                             resolutions[0])
            else:
                id = 'action_%s_resolve_resolution' % action
                selected_option = \
                    req.args.get(id, self.config.get('ticket',
                                                     'default_resolution'))
                control.append(tag(['as ', tag.select(
                    [tag.option(x, selected=(x == selected_option or None))
                     for x in resolutions],
                    id=id, name=id)]))
                hints.append(_("The resolution will be set"))
        if 'leave_status' in operations:
            control.append('as %s ' % ticket._old.get('status', 
                                                      ticket['status']))
        else:
            if status != '*':
                hints.append(_("Next status will be '%s'") % status)
        return this_action['name'], tag(*control), '. '.join(hints)


    def get_ticket_changes(self, req, ticket, action):

        tipo_ticket = ticket._old.get('type', ticket['type'])
        actions = get_workflow_config_by_type(self.config, tipo_ticket)
        if not actions:
            actions = get_workflow_config_default(self.config)
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
            if operation == 'del_owner':
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

            if operation == 'del_resolution':
                updated['resolution'] = ''
            elif operation == 'set_resolution':
                newresolution = \
                    req.args.get('action_%s_resolve_resolution' % action,
                                 this_action.get('set_resolution', '').strip())
                updated['resolution'] = newresolution

            # leave_status is just a no-op here, so we don't look for it.
        return updated


    def apply_action_side_effects(self, req, ticket, action):
        pass


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

    # Public methods

    def get_actions_by_operation(self, operation):
        """Return a list of all actions with a given operation
        (for use in the controller's get_all_status())
        """
        all_actions = {}
        # Default workflow
        all_actions.update(get_workflow_config_default(self.config))
        # for all ticket types do
        for t in [enum.name for enum in model.Type.select(self.env)]:
            all_actions.update(get_workflow_config_by_type(self.config, t))

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
        actions = get_workflow_config_by_type(self.config,tipo_ticket)
        if not actions:
            actions = get_workflow_config_default(self.config)

        # Be sure to look at the original status.
        status = ticket._old.get('status', ticket['status'])
        actions = [(info['default'], action) for action, info
                   in actions.items()
                   if operation in info['operations'] and
                      ('*' in info['oldstates'] or
                       status in info['oldstates']) and
                      self._has_perms_for_action(req, info, ticket.resource)]
        return actions
