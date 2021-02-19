# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
#
# License: 3-clause BSD
#
import unittest

from trac.test import EnvironmentStub, MockPerm, MockRequest
from simplemultiproject.smp_model import SmpProject
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
# from simplemultiproject.permission import SmpPermissionPolicy
from simplemultiproject.roadmap import SmpRoadmapModule
from simplemultiproject.tests.util import revert_schema


class TestRoadmapModule(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prj_model = SmpProject(self.env)
        # self.perm_plugin = SmpPermissionPolicy(self.env)
        self.roadmap_plugin = SmpRoadmapModule(self.env)

    def test_add_projects_to_dict(self):
        class Perm(MockPerm):
            perms = ['PROJECT_SETTINGS_VIEW', 'TICKET_VIEW', 'PROJECT_1_MEMBER']
            def has_permission_mock(self, action, realm_or_resource=None, id=False,
                       version=False):
                return action in self.perms
            __contains__ = has_permission_mock

        prjs = ((1, 'p 1', 'YES'), (2, 'p 2', None), (3, 'p 3', 'YES'), (4, 'p 4', None),
                (5, 'p 5', 'YES'), (6, 'p 6', 'YES'), (7, 'p 7', None), (8, 'p 8', None))
        for p_id, name, restrict in prjs:
            prj_id = self.prj_model.add(name, restrict_to=restrict)
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        req = MockRequest(self.env)
        req.perm = Perm()
        data = {}
        # Some projects are restricted. User only has permission to access project 'p 1'.
        self.roadmap_plugin.add_projects_to_dict(req, data)
        self.assertEqual(5, len(data['project_ids']))
        self.assertListEqual([1, 2, 4, 7, 8], data['project_ids'])
        self.assertEqual(5, len(data['projects']))
        # Closed projects must be omitted
        for prj in data['projects']:
            self.assertIsNone(prj.closed)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRoadmapModule))

    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
