# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
#
import unittest

from trac.test import EnvironmentStub
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.model import Project
from simplemultiproject.tests.util import revert_schema


class TestProject(unittest.TestCase):
    """Test Project class in model.py"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)

    def tearDown(self):
        self.env.reset_db()

    def test_insert(self):

        prj = Project(self.env)
        prj.name = 'Project 1'
        prj.insert()
        self.assertEqual(1, prj.id)
        prj = Project(self.env)
        prj.name = 'Project 2'
        prj.insert()
        self.assertEqual(2, prj.id)


if __name__ == '__main__':
    unittest.main()
