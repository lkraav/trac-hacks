import unittest
from pkg_resources import get_distribution, parse_version
from trac.test import EnvironmentStub
from trac.ticket.model import Ticket, Version
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.smp_model import SmpVersion
from simplemultiproject.tests.util import revert_schema
from simplemultiproject.version import SmpVersionModule


pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')


class TestSmpVersion(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
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

    def test_template_jinja_13974(self):
        """Test Jinja2 template, see #13974."""
        from trac.web.chrome import Chrome
        from trac.test import Mock, MockRequest

        version = Version(self.env)
        version.name = 'foo1'
        version.insert()
        tkt = Ticket(self.env)
        tkt.summary ='summary'
        tkt.description = 'description'
        tkt['version'] = version.name
        tkt.insert()
        tkt = Ticket(self.env)
        tkt.summary ='summary'
        tkt.description = 'description'
        tkt['version'] = version.name
        tkt['status'] = 'closed'
        tkt.insert()

        chrome = Chrome(self.env)
        session = Mock()
        req = MockRequest(self.env)
        vm = SmpVersionModule(self.env)
        tmpl, data, stuff = vm._render_view(req, version)
        if pre_1_3:
            chrome.render_template(req, 'version_view.html', data)
        else:
            chrome.render_template(req, 'version_view_jinja.html', data, metadata={})


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSmpVersion))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
