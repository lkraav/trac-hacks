# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2012 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest

from trac.core import TracError
from trac.test import EnvironmentStub, Mock
from trac.util.html import html as tag

from customfieldadmin.api import CustomFields, tag_


class CustomFieldApiTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.cf_api = CustomFields(self.env)

    def tearDown(self):
        self.env.destroy_db()

    def test_create(self):
        for f in ['one', 'two', 'three']:
            cfield = {'name': f, 'type': 'text'}
            self.cf_api.create_custom_field(cfield)
        self.assertEquals([{
                'custom': True, 'name': u'one', 'format': 'plain',
                'value': '', 'label': u'One', 'type': u'text', 'order': 1
            }, {
                'custom': True, 'name': u'two', 'format': 'plain',
                'value': '', 'label': u'Two', 'type': u'text', 'order': 2
            }, {
                'custom': True, 'name': u'three', 'format': 'plain',
                'value': '', 'label': u'Three', 'type': u'text', 'order': 3
            }
        ], self.cf_api.get_custom_fields())

    def test_update(self):
        cfield = {'name': 'foo', 'type': 'text'}
        self.cf_api.create_custom_field(cfield)
        self.assertEquals({
            'custom': True, 'name': u'foo', 'format': 'plain',
            'value': '', 'label': u'Foo', 'type': u'text', 'order': 1
        }, cfield)

        cfield['label'] = 'Answer'
        cfield['value'] = '42'
        self.cf_api.update_custom_field(cfield=cfield)
        self.assertEquals({
            'custom': True, 'name': u'foo', 'format': 'plain',
            'value': '42', 'label': u'Answer', 'type': u'text', 'order': 1
        }, cfield)

    def test_update_textarea(self):
        cfield = {'name': 'foo', 'type': 'textarea'}
        self.cf_api.create_custom_field(cfield)

        self.assertEquals({
            'custom': True, 'name': u'foo', 'format': 'plain', 'value': '',
            'label': u'Foo', 'type': u'textarea', 'order': 1, 'rows': 5
        }, cfield)

        cfield['rows'] = 3
        self.cf_api.update_custom_field(cfield=cfield)

        self.assertEquals({
            'custom': True, 'name': u'foo', 'format': 'plain', 'value': '',
            'label': u'Foo', 'type': u'textarea', 'order': 1, 'rows': 3
        }, cfield)

    def test_update_non_existing(self):
        with self.assertRaises(Exception) as cm:
            self.cf_api.update_custom_field(cfield={'name': 'no_field'})
        self.assertTrue("'no_field'" in cm.exception.message)
        self.assertTrue('does not exist' in cm.exception.message)

    def test_update_non_existing_no_name(self):
        with self.assertRaises(Exception) as cm:
            self.cf_api.update_custom_field(cfield={})
        self.assertTrue("'(none)'" in cm.exception.message)
        self.assertTrue('does not exist' in cm.exception.message)

    def test_delete(self):
        for f in ['one', 'two', 'three']:
            cfield = {'name': f, 'type': 'text'}
            self.cf_api.create_custom_field(cfield)
        self.assertIn(('two', 'text'),
                self.env.config.options('ticket-custom'))
        self.cf_api.delete_custom_field({'name': 'two'})
        self.assertNotIn(('two', 'text'),
                self.env.config.options('ticket-custom'))
        # Note: Should also reorder higher-ordered items
        self.assertEquals([{
                'custom': True, 'name': u'one', 'format': 'plain',
                'value': '', 'label': u'One', 'type': u'text', 'order': 1
            }, {
                'custom': True, 'name': u'three', 'format': 'plain',
                'value': '', 'label': u'Three', 'type': u'text', 'order': 2
            }
        ], self.cf_api.get_custom_fields())
        self.assertIsNone(
                self.cf_api.get_custom_fields(cfield={'name': 'two'}))

    def test_delete_unknown_options(self):
        cf = {'name': 'foo', 'type': 'text', 'label': 'Foo'}
        self.cf_api.create_custom_field(cf)
        self.assertEquals('text',
                self.env.config.get('ticket-custom', 'foo'))
        self.assertEquals('Foo',
                self.env.config.get('ticket-custom', 'foo.label'))
        self.env.config.set('ticket-custom', 'foo.answer', '42')
        self.cf_api.delete_custom_field(cf, modify=False)
        self.assertEquals('',
                self.env.config.get('ticket-custom', 'foo'))
        self.assertEquals('',
                self.env.config.get('ticket-custom', 'foo.label'))
        self.assertEquals('',
                self.env.config.get('ticket-custom', 'foo.answer'))

    def test_not_delete_unknown_options_for_modify(self):
        cf = {'name': 'foo', 'type': 'text', 'label': 'Foo'}
        self.cf_api.create_custom_field(cf)
        self.assertEquals('text',
                self.env.config.get('ticket-custom', 'foo'))
        self.assertEquals('Foo',
                self.env.config.get('ticket-custom', 'foo.label'))
        self.env.config.set('ticket-custom', 'foo.answer', '42')
        self.cf_api.delete_custom_field(cf, modify=True)
        self.assertEquals('',
                self.env.config.get('ticket-custom', 'foo'))
        self.assertEquals('',
                self.env.config.get('ticket-custom', 'foo.label'))
        self.assertEquals('42',
                self.env.config.get('ticket-custom', 'foo.answer'))

    def test_verify_unknown_type(self):
        self.env.config.set('ticket-custom', 'one', 'foo_type')
        fields = self.cf_api.get_custom_fields()
        self.assertEquals(1, len(fields))
        with self.assertRaises(TracError) as cm:
            self.cf_api.verify_custom_field(fields[0], create=False)
        self.assertTrue('foo_type' in cm.exception.message)

    def test_verify_reserved_names(self):
        cf = {'name': 'group', 'type': 'text', 'label': 'Group'}
        with self.assertRaises(TracError):
            self.cf_api.verify_custom_field(cf)
        cf = {'name': 'Group', 'type': 'text'}
        with self.assertRaises(TracError):
            self.cf_api.verify_custom_field(cf)
        cf = {'name': 'group_', 'type': 'text', 'label': 'Group'}
        self.cf_api.verify_custom_field(cf)  # no errors


class CustomFieldL10NTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.cf_api = CustomFields(self.env)

    def tearDown(self):
        self.env.destroy_db()

    def test_translation_function(self):
        from customfieldadmin.api import _
        self.assertEquals('foo bar', _("foo bar"))
        self.assertEquals('foo bar', _("foo %(bar)s", bar='bar'))

    def test_translation_function_tag(self):
        self.assertEquals('<p>foo bar</p>', str(tag_(tag.p('foo bar'))))
        self.assertEquals('<p>foo bar</p>',
                    unicode(tag_(tag.p('foo %(bar)s' % {'bar': 'bar'}))))
