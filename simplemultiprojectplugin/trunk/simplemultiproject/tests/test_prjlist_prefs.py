#
# These tests check the creation of the project list for roadmap and timeline page
#
import unittest

from datetime import datetime
from trac.util.datefmt import to_utimestamp, utc
from trac.test import EnvironmentStub, MockRequest
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.model import SmpModel
from simplemultiproject.roadmap import create_proj_table, SmpRoadmapProjectFilter
from simplemultiproject.tests.util import revert_schema


class TestProjectListPrefsNoProject(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpRoadmapProjectFilter(self.env)
        self.req = MockRequest(self.env, username='Tester')
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpModel(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_projects_not_closed(self):
        expected = """<div><p>No projects defined.</p><br></div>"""
        res = create_proj_table(self.plugin, self.model, self.req)
        self.assertEqual(expected, res)

class TestProjectListPrefs(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpRoadmapProjectFilter(self.env)
        self.req = MockRequest(self.env, username='Tester')
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpModel(self.env)
        self.model.insert_project("foo1", 'Summary 1', 'Description 1', None, None)
        self.model.insert_project("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.insert_project("foo3", 'Summary 3', 'Description 3', None, None)

    def tearDown(self):
        self.env.reset_db()

    def test_projects_not_closed(self):
        expected = """<div style="overflow:hidden;">
<div>
<label>Filter Project:</label>
</div>
<div>
<input type="hidden" name="smp_update" value="filter">
<select id="Filter-Projects" name="smp_projects" multiple size="4" style="overflow:auto;">
    <option value="All">All</option>
    <option value="foo1">
        foo1
    </option><option value="foo2">
        foo2
    </option><option value="foo3">
        foo3
    </option>
</select>
</div>
<br>
</div>"""
        res = create_proj_table(self.plugin, self.model, self.req)
        self.assertEqual(expected, res)


class TestProjectListPrefsClosed(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpRoadmapProjectFilter(self.env)
        self.req = MockRequest(self.env, username='Tester')
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpModel(self.env)
        self.model.insert_project("foo1", 'Summary 1', 'Description 1', None, None)
        time = to_utimestamp(datetime(2000, 1, 1, tzinfo=utc))
        self.model.insert_project("foo2", 'Summary 2', 'Description 2', time, None)
        self.model.insert_project("foo3", 'Summary 3', 'Description 3', None, None)

    def tearDown(self):
        self.env.reset_db()

    def test_project_closed(self):
        expected = """<div style="overflow:hidden;">
<div>
<label>Filter Project:</label>
</div>
<div>
<input type="hidden" name="smp_update" value="filter">
<select id="Filter-Projects" name="smp_projects" multiple size="3" style="overflow:auto;">
    <option value="All">All</option>
    <option value="foo1">
        foo1
    </option><option value="foo3">
        foo3
    </option>
</select>
</div>
<br>
</div>"""
        res = create_proj_table(self.plugin, self.model, self.req)
        self.assertEqual(expected, res)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestProjectListPrefsNoProject))
    suite.addTest(unittest.makeSuite(TestProjectListPrefs))
    suite.addTest(unittest.makeSuite(TestProjectListPrefsClosed))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
