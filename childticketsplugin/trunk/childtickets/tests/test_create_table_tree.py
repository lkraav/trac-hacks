# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
#
# License: 3-clause BSD
#
import unittest

from childtickets.web_ui import ChildTicketsModule
from trac.test import EnvironmentStub, MockRequest
from trac.ticket.model import Ticket

def create_ticket_tree(env):
    for num in range(1, 11):
        ticket = Ticket(env)
        ticket['summary'] = "Summary %s" % num
        ticket['description'] = "Description %s" % num
        ticket.insert()
    ticket = Ticket(env, 2)
    ticket['parent'] = '#1'
    ticket.save_changes()
    ticket = Ticket(env, 3)
    ticket['parent'] = '#1'
    ticket.save_changes()
    ticket = Ticket(env, 4)
    ticket['parent'] = '#2'
    ticket.save_changes()
    ticket = Ticket(env, 5)
    ticket['parent'] = '#4'
    ticket.save_changes()


class TestCreateTableTree(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "childtickets.*"])
        self.plugin = ChildTicketsModule(self.env)
        self.env.config.set("ticket-custom", "parent", "text")
        create_ticket_tree(self.env)


    def test_create_indented_html(self):
        # We just check if we don't crash here...
        req = MockRequest(self.env)
        for num in range(1, 11):
            ticket = Ticket(self.env, num)
            self.plugin.create_childticket_tree_html(req, ticket)


if __name__ == '__main__':
    unittest.main()
