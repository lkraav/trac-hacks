import unittest
from trac.test  import EnvironmentStub
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.smp_model import SmpVersion
from simplemultiproject.tests.util import revert_schema

__author__ = 'cinc'


class TestSmpVersion(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpVersion(self.env)
        self.model.add("foo1", 1)
        self.model.add("bar", 2)
        self.model.add("baz", 3)
        self.model.add("foo2", 1)

    def tearDown(self):
        self.env.reset_db()

    def print_table(self, tbl_name):
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT version, id_project FROM smp_version_project")
        for item in cursor:
            print repr(item)

    def test_delete(self):
        self.assertEqual(4, len(self.model.get_all_versions_and_project_id()))
        self.model.delete("baz")
        self.assertEqual(3, len(self.model.get_all_versions_and_project_id()))
        versions = self.model.get_versions_for_project_id(1)
        self.assertEqual(2, len(versions))
        self.assertEqual("foo1", versions[0])
        self.assertEqual("foo2", versions[1])


    def test_add(self):
        self.assertEqual(4, len(self.model.get_all_versions_and_project_id()))
        versions = self.model.get_versions_for_project_id(1)
        self.assertEqual(2, len(versions))
        self.assertEqual("foo1", versions[0])
        self.assertEqual("foo2", versions[1])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSmpVersion))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
