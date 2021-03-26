# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
#
# License: 3-clause BSD
#
import unittest

from ticketfieldfilter.web_ui import TicketFieldFilter
from trac.test import EnvironmentStub


class TestConfiguration(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        self.env.config.set("ticket-field-filter", 'defect.fields', '+')
        self.plugin = TicketFieldFilter(self.env)

    def test_ticket_fields_defect_all(self):
        res = self.plugin.get_configuration_for_tkt_types()
        self.assertEqual(3, len(res))
        tkt_fields, fields_readonly, field_perms = res
        # This will break when Trac doesn't default to [defect, task, enhancement] anymore
        self.assertEqual(3, len(tkt_fields))
        self.assertEqual(3, len(fields_readonly))
        self.assertEqual(3, len(field_perms))

        self.assertNotIn('+', tkt_fields['defect'])


if __name__ == '__main__':
    unittest.main()
