# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
#
# License: 3-clause BSD
#
import unittest
from pkg_resources import get_distribution, parse_version

from childtickets.admin import ChildTicketsAdminPanel
from trac.admin.web_ui import AdminModule
from trac.test import EnvironmentStub, MockRequest


pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')


class TestCreateTableTree(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*",
                                           "childtickets.*"])
        self.plugin = ChildTicketsAdminPanel(self.env)
        self.env.config.set("ticket-custom", "parent", "text")
        self.env.config.set("ticket-custom", "parent.format", "wiki")
        # Note that the ticket custom field 'foo' is not defined
        self.env.config.set('childtickets', 'parent.defect.table_headers', 'status,parent,summary,foo')

    def test_admin_template_type_jinja(self):
        """Test Jinja2 template, see #13974."""
        from trac.web.chrome import Chrome

        am = AdminModule(self.env)  # So admin templates are added to the template search path
        chrome = Chrome(self.env)
        req = MockRequest(self.env)

        tmpl, data = self.plugin.render_admin_panel(req, 'childtickets', 'type', None)

        # This only shows exceptions with Trac 1.2 and Trac 1.4.
        # Trac 1.5 seems to catch them during rendering albeit they are shown on the Trac console
        # in real life.
        if pre_1_3:
            chrome.render_template(req, tmpl, data)
        else:
            chrome.render_template(req, tmpl, data, metadata={})


if __name__ == '__main__':
    unittest.main()
