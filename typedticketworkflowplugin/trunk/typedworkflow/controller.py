# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Vladimir Abramov <kivsiak@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.ticket.default_workflow import ConfigurableTicketWorkflow


class TypedTicketWorkflow(ConfigurableTicketWorkflow):
    """Allows workflow actions to be conditionally defined for specific
    ticket types."""

    def get_ticket_actions(self, req, ticket):        
        actions =  \
            ConfigurableTicketWorkflow.get_ticket_actions(self, req, ticket)
        actions = self.filter_actions(actions, ticket)
        return actions

    def filter_actions(self, action, ticket):
        """Finds the actions that use this operation"""
        filtered_actions = []
        for default, action_name in action:
            action_attributes = self.actions[action_name]
            if 'tickettype' in action_attributes:
                #TODO normalization this should be done only once
                required_types = [a.strip() for a in 
                                  action_attributes['tickettype'].split(',')]
                if ticket.get_value_or_default('type') in required_types:
                    filtered_actions.append((default, action_name))
            else:
                filtered_actions.append((default, action_name))
        return filtered_actions

    def get_actions_by_operation_for_req(self, req, ticket, operation):
        actions = ConfigurableTicketWorkflow \
                  .get_actions_by_operation_for_req(self, req, ticket,
                                                    operation)
        actions = self.filter_actions(actions, ticket)
        return actions
