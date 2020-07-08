# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
import unittest

from trac.test import EnvironmentStub, MockRequest
from simplemultiproject.admin_filter import SmpFilterDefaultMilestonePanels
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.milestone import create_cur_projects_table, create_projects_table_j
from simplemultiproject.model import SmpModel
from simplemultiproject.tests.util import revert_schema
from simplemultiproject.smp_model import SmpMilestone


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
        self.model = SmpModel(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_no_projects(self):
        expected = """<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
 restrictions are imposed.</p>
</div>
<div class="admin-smp-proj-tbl-div">
<table id="projectlist" class="listing admin-smp-project-table">
    <thead>
        <tr><th></th><th>Project</th></tr>
    </thead>
    <tbody>
    </tbody>
</table>
</div>
<div></div>
</div>"""
        res = create_projects_table_j(self.plugin, self.model, self.req)
        self.assertEqual(expected, res)

    def test_with_projects_checkbox(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
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
        self.model.insert_project(u"foo1öäü", 'Summary 1', 'Description 1', None, None)
        self.model.insert_project("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.insert_project("foo3", 'Summary 3', 'Description 3', None, None)

        res = create_projects_table_j(self.plugin, self.model, self.req)
        self.assertEqual(expected, res)

    def test_with_projects_radio(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
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
        self.model.insert_project(u"foo1öäü", 'Summary 1', 'Description 1', None, None)
        self.model.insert_project("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.insert_project("foo3", 'Summary 3', 'Description 3', None, None)

        res = create_projects_table_j(self.plugin, self.model, self.req, 'radio')
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
        self.model = SmpModel(self.env)
        self.model.insert_project(u"foo1öäü", 'Summary 1', 'Description 1', None, None)
        self.model.insert_project("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.insert_project("foo3", 'Summary 3', 'Description 3', None, None)
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
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
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

        res = create_projects_table_j(self.plugin, self.model, self.req, item_name='ms1')
        self.assertEqual(expected, res)

    def test_with_radio_edit_milestone_ms1(self):
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
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

        res = create_projects_table_j(self.plugin, self.model, self.req, 'radio', item_name='ms1')
        self.assertEqual(expected, res)

    def test_with_checkbox_edit_milestone_ms2_dual_prj(self):
        """Check a milestone with two associated projects."""
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
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

        res = create_projects_table_j(self.plugin, self.model, self.req, item_name='ms2')
        self.assertEqual(expected, res)

    def test_with_radio_edit_milestone_ms2_dual_prj(self):
        """Check a milestone with two associated projects."""
        expected = u"""<div style="overflow:hidden;">
<div id="project-help-div">
<p class="help">Please chose the projects for which this item will be selectable. Without a selection here no
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

        res = create_projects_table_j(self.plugin, self.model, self.req, 'radio', item_name='ms2')
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
        self.model = SmpModel(self.env)
        self.msmodel = SmpMilestone(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_no_projects(self):
        expected = """"""
        res = create_cur_projects_table(self.msmodel, None)
        self.assertEqual(expected, res)

    def test_with_projects(self):
        expected = """"""
        self.model.insert_project("foo1", 'Summary 1', 'Description 1', None, None)
        self.model.insert_project("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.insert_project("foo3", 'Summary 3', 'Description 3', None, None)

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
        self.model = SmpModel(self.env)
        self.model.insert_project("foo1", 'Summary 1', 'Description 1', None, None)
        self.model.insert_project("foo2", 'Summary 2', 'Description 2', None, None)
        self.model.insert_project("foo3", 'Summary 3', 'Description 3', None, None)
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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestProjectTableNoMilestones))
    suite.addTest(unittest.makeSuite(TestProjectTableMilestones))
    suite.addTest(unittest.makeSuite(TestCurProjectTableNoMilestones))
    suite.addTest(unittest.makeSuite(TestCurProjectTableMilestones))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
