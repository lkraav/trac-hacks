# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
#
# License: 3-clause BSD
#
import unittest

from trac.test import EnvironmentStub
from simplemultiproject.admin_filter import SmpFilterBase
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.tests.util import revert_schema
from simplemultiproject.smp_model import SmpMilestone, SmpProject


class TestSmpFilterBase(unittest.TestCase):
    """Test if the informational message about no defined projects is shown on the version page."""
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterBase(self.env)
        self.model_prj = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_create_project_select_ctrl_no_prj(self):
        """No projects are defined, default configuration is 'milestone_without_project = disabled'."""
        expected = u"""<div id="smp-ms-sel-div">
    Project
    <select id="smp-project-sel">
        <option value="" selected>All</option>
    </select>
    </div>"""
        res = self.plugin.create_project_select_ctrl([])
        self.assertEqual(expected, res)

    def test_create_project_select_ctrl_with_prj(self):
        """No projects are defined, default configuration is 'milestone_without_project = disabled'."""
        expected = u"""<div id="smp-ms-sel-div">
    Project
    <select id="smp-project-sel">
        <option value="" selected>All</option><option value="foo">foo</option><option value="bar">bar</option>
    </select>
    </div>"""
        prjs = ('foo', 'bar')

        res = self.plugin.create_project_select_ctrl(prjs)
        self.assertEqual(expected, res)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSmpFilterBase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
