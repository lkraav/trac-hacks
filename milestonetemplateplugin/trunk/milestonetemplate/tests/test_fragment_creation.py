# -*- coding: utf-8 -*-
# Copyright (c) 2020 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest
from milestonetemplate.web_ui import MilestoneTemplatePlugin
from trac.test import EnvironmentStub


class TestHtmlFragment(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                              'milestonrtemplate.*',
                                                              ])
        self.plugin = MilestoneTemplatePlugin(self.env)

    def tearDown(self):
        self.env.shutdown()

    def test_create_admin_fragment(self):
        expected = u"""<div class="field">
            <label>Template:
            <select id="ms-templates" name="template">
                <option value="">(blank)</option>
                <option value="Foo">
                    Foo
                </option><option value="Bar">
                    Bar
                </option>
            </select>
            <span class="hint">For Milestone description</span>
            </label>
        </div>"""
        # Produces a Genshi stream
        templates = ['Foo', 'Bar']
        res = self.plugin.create_admin_page_select_ctrl(templates)
        self.assertEqual(expected, res)

    def test_create_milestone_page_fragment(self):
        expected = u"""<div class="field">
            <p>Or use a template for the description:</p>
            <label>Template:
            <select id="ms-templates" name="template">
                <option value="" selected="selected">(Use given Description)</option>
                <option value="Foo">
                    Foo
                </option><option value="Bar">
                    Bar
                </option>
            </select>
            <span class="hint">The description will be replaced with the template contents on submit.</span>
            </label>
        </div>"""
        # Produces a Genshi stream
        templates = ['Foo', 'Bar']
        res = self.plugin.create_milestone_page_select_ctrl(templates)
        self.assertEqual(expected, res)

    def test_create_milestone_page_fragment_select(self):
        expected = u"""<div class="field">
            <p>Or use a template for the description:</p>
            <label>Template:
            <select id="ms-templates" name="template">
                <option value="">(Use given Description)</option>
                <option value="Foo">
                    Foo
                </option><option value="Bar" selected="selected">
                    Bar
                </option>
            </select>
            <span class="hint">The description will be replaced with the template contents on submit.</span>
            </label>
        </div>"""
        # Produces a Genshi stream
        templates = ['Foo', 'Bar']
        res = self.plugin.create_milestone_page_select_ctrl(templates, 'Bar')
        self.assertEqual(expected, res)


def fragment_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestHtmlFragment))

    return suite
