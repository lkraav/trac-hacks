# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
import unittest

from trac.test import EnvironmentStub
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.smp_model import SmpProject
from simplemultiproject.tests.util import revert_schema


class TestSmpProjectAdd(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prj_model = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_project_add_name_only(self):
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name)
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

    def test_project_add_summary_desc(self):
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name, summary=name + u'summary äöü', description=name + u'desc äöü')
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        for item in self.prj_model.get_all_projects():
            self.assertEqual(item[1] + u'summary äöü', item[2])
            self.assertEqual(item[1] + u'desc äöü', item[3])
            prj_id = int(item[1].split()[1])  # derived from name. This works because of auto increment
            self.assertEqual(item[0], prj_id)


class TestSmpProjectExists(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prj_model = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_project_exist_no_prj(self):
        self.assertFalse(self.prj_model.project_exists())
        self.assertFalse(self.prj_model.project_exists(project_id=1))
        self.assertFalse(self.prj_model.project_exists(project_name='foo'))

    def test_project_exist(self):
        # prepare data
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name, summary=name + u'summary äöü', description=name + u'desc äöü')
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        # Check inserted projects
        for p_id, name in prjs:
            self.assertTrue(self.prj_model.project_exists(project_id=p_id))
            self.assertTrue(self.prj_model.project_exists(project_name=name))

        # negative test
        self.assertFalse(self.prj_model.project_exists(project_id=5))
        self.assertFalse(self.prj_model.project_exists(project_name='foo'))

        # Test deleted projects


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSmpProjectAdd))
    suite.addTest(unittest.makeSuite(TestSmpProjectExists))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
