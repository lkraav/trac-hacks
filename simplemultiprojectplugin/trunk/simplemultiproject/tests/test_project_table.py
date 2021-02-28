# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 Cinc
#
# License: 3-clause BSD
#
import unittest

from trac.admin.console import TracAdmin
from trac.test import EnvironmentStub, MockPerm, MockRequest
from simplemultiproject.admin_filter import SmpFilterDefaultMilestonePanels, SmpFilterDefaultVersionPanels
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.milestone import create_cur_projects_table, create_projects_table_j
from simplemultiproject.tests.util import revert_schema
from simplemultiproject.smp_model import SmpMilestone, SmpProject


class TestProjectTableVersionNoProjects(unittest.TestCase):
    """Test if the informational message about no defined projects is shown on the version page."""
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterDefaultVersionPanels(self.env)
        self.req = MockRequest(self.env, username='Tester')

    def tearDown(self):
        self.env.reset_db()

    def test_no_projects_but_required(self):
        """No projects are defined, default configuration is 'milestone_without_project = disabled'."""
        expected = u"""<div><div class="system-message warning">No projects are defined or all projects are completed.</div>
<p>Your current configuration requires that you associate the {item} with at least one 
project before you can add it. Go to the <em>Manage Projects</em> section to define projects.</p></div>""".format(item='item')
        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)

    def test_no_projects_allow_for_ms(self):
        """No projects are defined but configuration is 'milestone_without_project = True'."""
        expected = u"""<div><p>No projects are defined or all projects are completed.</p></div>"""
        self.env.config.set('simple-multi-project', 'milestone_without_project', True)
        res = create_projects_table_j(self.plugin, self.req)
        self.assertNotEqual(expected, res)

    def test_no_projects_but_allow_for_version(self):
        """No projects are defined but configuration is 'version_without_project = True'."""
        expected = u"""<div><p>No projects are defined or all projects are completed.</p></div>"""
        self.env.config.set('simple-multi-project', 'version_without_project', True)
        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)


class TestProjectTableMilestonesNoProjects(unittest.TestCase):
    """Test if the informational message about no defined projects is shown on the milestone page."""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterDefaultMilestonePanels(self.env)
        self.req = MockRequest(self.env, username='Tester')

    def tearDown(self):
        self.env.reset_db()

    def test_no_projects_but_required(self):
        """No projects are defined, default configuration is 'milestone_without_project = disabled'."""
        expected = u"""<div><div class="system-message warning">No projects are defined or all projects are completed.</div>
<p>Your current configuration requires that you associate the {item} with at least one 
project before you can add it. Go to the <em>Manage Projects</em> section to define projects.</p></div>""".format(item='item')
        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)

    def test_no_projects_but_allow_version(self):
        """No projects are defined but configuration is 'version_without_milestone = True'."""
        expected = u"""<div><p>No projects are defined or all projects are completed.</p></div>"""
        self.env.config.set('simple-multi-project', 'milestone_without_project', True)
        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)

    def test_no_projects_but_allow_ms(self):
        """No projects are defined but configuration is 'milestone_without_project = True'."""
        expected = u"""<div><p>No projects are defined or all projects are completed.</p></div>"""
        self.env.config.set('simple-multi-project', 'milestone_without_project', True)
        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)


class TestProjectTableNoMilestones(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterDefaultMilestonePanels(self.env)
        self.req = MockRequest(self.env, username='Tester')
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_with_projects_checkbox(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="checkbox">
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="checkbox">
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="checkbox">
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""
        self.model.add(u"foo1öäü", 'Summary 1', 'Description 1', None, None)
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)

        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)

    def test_with_projects_radio(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="radio">
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="radio">
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="radio">
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""
        self.model.add(u"foo1öäü", 'Summary 1', 'Description 1', None, None)
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)

        res = create_projects_table_j(self.plugin, self.req, 'radio')
        self.assertEqual(expected, res)


class TestProjectTableMilestones(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterDefaultMilestonePanels(self.env)
        self.req = MockRequest(self.env, username='Tester')
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpProject(self.env)
        self.model.add(u"foo1öäü", 'Summary 1', 'Description 1', None, None)
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)
        self.msmodel = SmpMilestone(self.env)
        self.msmodel.add("ms1", 1)  # second parm is project id
        self.msmodel.add("ms2", (2, 3))  # this milestone belongs to project 2 and 3
        self.msmodel.add("ms3", 3)
        self.msmodel.add("ms4", 1)

    def tearDown(self):
        self.env.reset_db()

    def test_with_checkbox_edit_milestone_ms1(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="checkbox" checked>
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="checkbox">
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="checkbox">
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""

        res = create_projects_table_j(self.plugin, self.req, item_name='ms1')
        self.assertEqual(expected, res)

    def test_with_radio_edit_milestone_ms1(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="radio" checked>
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="radio">
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="radio">
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""

        res = create_projects_table_j(self.plugin, self.req, 'radio', item_name='ms1')
        self.assertEqual(expected, res)

    def test_with_checkbox_edit_milestone_ms2_dual_prj(self):
        """Check a milestone with two associated projects."""
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="checkbox">
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="checkbox" checked>
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="checkbox" checked>
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""

        res = create_projects_table_j(self.plugin, self.req, item_name='ms2')
        self.assertEqual(expected, res)

    def test_with_radio_edit_milestone_ms2_dual_prj(self):
        """Check a milestone with two associated projects."""
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="radio">
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="radio" checked>
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="radio" checked>
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""

        res = create_projects_table_j(self.plugin, self.req, 'radio', item_name='ms2')
        self.assertEqual(expected, res)


class TestCurProjectTableNoMilestones(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterDefaultMilestonePanels(self.env)
        self.req = MockRequest(self.env, username='Tester')
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpProject(self.env)
        self.msmodel = SmpMilestone(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_no_projects(self):
        expected = """"""
        res = create_cur_projects_table(self.msmodel, None)
        self.assertEqual(expected, res)

    def test_with_projects(self):
        expected = """"""
        self.model.add("foo1", 'Summary 1', 'Description 1', None, None)
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)

        res = create_cur_projects_table(self.msmodel, '')
        self.assertEqual(expected, res)


class TestCurProjectTableMilestones(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterDefaultMilestonePanels(self.env)
        self.req = MockRequest(self.env, username='Tester')
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpProject(self.env)
        self.model.add("foo1", 'Summary 1', 'Description 1', None, None)
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)
        self.msmodel = SmpMilestone(self.env)
        self.msmodel.add("ms1", 1)  # second parm is project id
        self.msmodel.add("ms2", (2, 3))  # this milestone belongs to project 2 and 3
        self.msmodel.add("ms3", 3)
        self.msmodel.add("ms4", 1)

    def tearDown(self):
        self.env.reset_db()

    def test_single_poject_milestone(self):
        expected = """<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">This milestone is connected to the following projects.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td>foo1</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""

        res = create_cur_projects_table(self.msmodel, 'ms1')
        self.assertEqual(expected, res)

    def test_multiple_poject_milestone(self):
        expected = """<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">This milestone is connected to the following projects.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td>foo2</td>
    </tr><tr>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""

        res = create_cur_projects_table(self.msmodel, 'ms2')
        self.assertEqual(expected, res)


class TestProjectTableNoMilestonesWithRetrictions(unittest.TestCase):

    def setUp(self):
        class Perm(MockPerm):
            perms = ['PROJECT_SETTINGS_VIEW', 'TICKET_VIEW']
            def has_permission_mock(self, action, realm_or_resource=None, id=False,
                       version=False):
                return action in self.perms
            __contains__ = has_permission_mock

        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterDefaultMilestonePanels(self.env)
        self.req = MockRequest(self.env, username='Tester')
        self.req.perm = Perm()
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_with_projects_checkbox_no_perms(self):
        """Check table creation with one restricted project and no users.

        The restricted project shouldn't be shown.
        """
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="2" type="checkbox">
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="checkbox">
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""
        self.model.add(u"foo1öäü", 'Summary 1', 'Description 1', None, "YES")
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)

        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)

    def test_with_projects_checkbox_perms(self):
        """Check table creation with one restricted project and user with permission.

        The restricted project should be shown together with the unrestricted ones.
        """
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="checkbox">
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="checkbox">
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="checkbox">
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""
        # Setup projects
        self.model.add(u"foo1öäü", 'Summary 1', 'Description 1', None, "YES")
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)

        self.req.perm.perms.append('PROJECT_2_MEMBER')
        res = create_projects_table_j(self.plugin, self.req)
        self.assertNotEqual(expected, res)

        # Add necessary permission a user associated to project 1 would have
        self.req.perm.perms.append('PROJECT_1_MEMBER')
        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)


class TestProjectTableMilestoneRestrictMessage(unittest.TestCase):
    """There are different messages wrt project selection depending on configuration.

    Note that we only test this for the milestone admin page. The version page uses the same code.
    """
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpFilterDefaultMilestonePanels(self.env)
        self.req = MockRequest(self.env, username='Tester')
        # self.env.config.set("ticket-custom", "project", "select")
        self.model = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_with_projects_required(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="checkbox">
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="checkbox">
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="checkbox">
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""
        self.model.add(u"foo1öäü", 'Summary 1', 'Description 1', None, None)
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)

        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)

    def test_with_projects_not_required(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects this item will be associated with. Without a selection here no
 restrictions are imposed.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    <tr>
        <td class="name">
            <input name="sel" value="1" type="checkbox">
        </td>
        <td>foo1öäü</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="2" type="checkbox">
        </td>
        <td>foo2</td>
    </tr><tr>
        <td class="name">
            <input name="sel" value="3" type="checkbox">
        </td>
        <td>foo3</td>
    </tr>
    </tbody>
</table>
</div>
<div></div>
</div>"""
        self.env.config.set('simple-multi-project', 'milestone_without_project', True)
        self.model.add(u"foo1öäü", 'Summary 1', 'Description 1', None, None)
        self.model.add("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.add("foo3", 'Summary 3', 'Description 3', None, None)

        res = create_projects_table_j(self.plugin, self.req)
        self.assertEqual(expected, res)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestProjectTableVersionNoProjects))
    suite.addTest(unittest.makeSuite(TestProjectTableMilestonesNoProjects))
    suite.addTest(unittest.makeSuite(TestProjectTableNoMilestones))
    suite.addTest(unittest.makeSuite(TestProjectTableMilestones))
    suite.addTest(unittest.makeSuite(TestCurProjectTableNoMilestones))
    suite.addTest(unittest.makeSuite(TestCurProjectTableMilestones))
    suite.addTest(unittest.makeSuite(TestProjectTableNoMilestonesWithRetrictions))
    suite.addTest(unittest.makeSuite(TestProjectTableMilestoneRestrictMessage))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
