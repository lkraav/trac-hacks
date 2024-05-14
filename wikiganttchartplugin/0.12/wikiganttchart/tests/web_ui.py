# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import inspect
import io
import json
import re
import unittest

from trac.perm import PermissionCache, PermissionSystem
from trac.test import EnvironmentStub, MockPerm
from trac.ticket.model import Ticket
from trac.util.datefmt import utc
from trac.web.api import Request, RequestDone
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage
import trac.wiki.web_ui
del trac

from ..web_ui import (WikiGanttChart, WikiGanttChartError,
                      WikiGanttChartModule, web_context)

try:
    unicode
except NameError:
    unicode = str


def _norm_newline(text):
    return re.sub(r'\r?\n', '\r\n', text)


def _make_environ(scheme='http', server_name='example.org',
                  server_port=80, method='POST', script_name='/trac',
                  **kwargs):
    environ = {'wsgi.url_scheme': scheme, 'wsgi.input': io.BytesIO(b''),
               'REQUEST_METHOD': method, 'SERVER_NAME': server_name,
               'SERVER_PORT': server_port, 'SCRIPT_NAME': script_name}
    environ.update(kwargs)
    return environ


def _create_req(path_info='/', page=None, **kwargs):
    content = io.BytesIO()
    def start_response(status, headers, exc_info=None):
        return content.write
    if page:
        path_info = '/wiki/' + page.name
    environ = _make_environ(PATH_INFO=path_info)
    req = Request(environ, start_response)
    attrs = {'_content': content, 'perm': MockPerm(),
             'form_token': '01234567890123456789', 'session': {}, 'chrome': {},
             'locale': None, 'tz': utc, 'authname': 'anonymous'}
    attrs.update(kwargs)
    for name in attrs:
        value = attrs[name]
        setattr(req, name, value)
        if name == 'args':
            req.arg_list = list(value.items())
    return req


def _insert_ticket(env, **kwargs):
    ticket = Ticket(env)
    ticket['status'] = 'new'
    for name in kwargs:
        ticket[name] = kwargs[name]
    ticket.insert()
    return ticket


def _check_task(self, task, **kwargs):
    for name in kwargs:
        value = kwargs[name]
        if name == 'summary':
            value = task['data'].get('subjectName')
        else:
            value = task.get(name)
        expected = kwargs[name]
        self.assertEqual(expected, value,
                          "%r != %r on %s" % (expected, value, name))


getargspec = inspect.getfullargspec \
             if hasattr(inspect, 'getfullargspec') else \
             inspect.getargspec

if 'ipnr' in getargspec(WikiPage.save)[0]:
    def _page_save(page, author, comment, ipnr):
        return page.save(author, comment, ipnr)
else:
    def _page_save(page, author, comment, ipnr):
        return page.save(author, comment)


class WikiTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', WikiGanttChartModule])
        self.mod = WikiGanttChartModule(self.env)

    def tearDown(self):
        self.env.reset_db()

    def _verify_newlines(self, text):
        for line in text.split('\n'):
            if line:
                self.assertEqual('\r', line[-1], repr(text))

    def test_replace_inline_macro(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        text = _norm_newline("""\
foo[[Gantt]]bar
foo[[Gantt]]bar[[Gantt]]foo
foo`[[Gantt]]`bar{{{[[Gantt]]}}}foo![[Gantt]]bar
foo!`[[Gantt]]`bar!{{{[[Gantt]]}}}foo
""")
        page.text = text
        req = _create_req()
        self.mod.validate_wiki_page(req, page)
        self._verify_newlines(page.text)

        ids = set(match.group(1)
                  for match in re.finditer(r' id="([^"]+)"', page.text))
        self.assertEqual(3, len(ids))

        text = re.sub(r' id="([^"]+)"', ' id="*"', page.text)
        expected = _norm_newline("""\
foo
{{{#!Gantt id="*" style="blue"
}}}
bar
foo
{{{#!Gantt id="*" style="blue"
}}}
bar
{{{#!Gantt id="*" style="blue"
}}}
foo
foo`[[Gantt]]`bar{{{[[Gantt]]}}}foo![[Gantt]]bar
foo!`[[Gantt]]`bar!{{{[[Gantt]]}}}foo
""")
        self.assertEqual(expected, text)

    def test_replace_macro_in_code_block(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        text = _norm_newline("""\
foo
{{{
  [[Gantt]]
}}}
bar
{{{#!python
  {{{
    [[Gantt]]
  }}}
}}}
""")
        page.text = text
        req = _create_req()
        self.mod.validate_wiki_page(req, page)
        self._verify_newlines(page.text)
        self.assertEqual(text, page.text)

    def test_replace_block_macro(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        text = _norm_newline("""\
foo
{{{#!Gantt
}}}
bar
{{{#!Gantt id="deadbeef"
}}}
foo
{{{#!Gantt
}}}
bar
""")
        page.text = text
        req = _create_req()
        self.mod.validate_wiki_page(req, page)
        self._verify_newlines(page.text)

        ids = set(match.group(1)
                  for match in re.finditer(r' id="([^"]+)"', page.text))
        self.assertEqual(3, len(ids))
        self.assertTrue('deadbeef' in ids, repr(ids))

        text = re.sub(r' id="([^"]+)"', ' id="*"', page.text)
        expected = _norm_newline("""\
foo
{{{#!Gantt id="*" style="blue"
}}}
bar
{{{#!Gantt id="*"
}}}
foo
{{{#!Gantt id="*" style="blue"
}}}
bar
""")
        self.assertEqual(expected, text)

    def test_expand(self):
        page = WikiPage(self.env, 'NewPage')
        text = _norm_newline("""\
{{{#!Gantt id="deadbeef" blah="1" abc-def="42"
}}}
""")
        page.text = text
        _req = _create_req(page=page)
        context = web_context(_req, page.resource)
        format_to_html(self.env, context, page.text)

    def _test_update_tasks(self, page, tasks=(), id='deadbeef', style='red',
                           perm=MockPerm()):
        content = json.dumps({'tasks': tasks, 'id': id, 'style': style})
        args = {'realm': 'wiki', 'id': page.name, 'version': str(page.version),
                'content': unicode(content)}
        req = _create_req(path_info='/_wikiganttchart/update', args=args,
                          perm=perm,
                          _inheaders=[('x-requested-with', 'XMLHttpRequest')])
        args['form_token'] = req.form_token
        self.assertEqual(True, self.mod.match_request(req))
        self.assertRaises(RequestDone, self.mod.process_request, req)
        return req

    def _json_from_req(self, req):
        content = req._content.getvalue()
        if isinstance(content, bytes):
            content = content.decode('ascii')
        return json.loads(content)

    def test_update_tasks_normal(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
{{{#!Gantt id="deadbeef"
Blah blah blah...
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        tasks = [
            {'level': 1,
             'parent': None,
             'startDate': '2014-06-23',
             'dueDate': '2014-07-09',
             'data': {'subjectName': 'Summary 1', 'ticket': '', 'owner':''},
             'ratio': 42},
            {'level': 2,
             'parent': 0,
             'startDate': None,
             'dueDate': '2014-07-21',
             'data': {'subjectName': 'Summary 2', 'ticket': '', 'owner':''},
             'ratio': 84},
            {'level': 2,
             'parent': 0,
             'startDate': '2014-07-02',
             'dueDate': None,
             'data': {'subjectName': r'Sum"mary\3', 'ticket': '', 'owner':''},
             'ratio': 63},
            ]
        req = self._test_update_tasks(page, tasks)
        result = self._json_from_req(req)
        version = page.version + 1
        self.assertEqual(True, result['valid'])
        self.assertEqual(version, result['version'])
        page = WikiPage(self.env, page.name)
        self.assertEqual(version, page.version)
        expected = _norm_newline(
r"""{{{#!Gantt id="deadbeef" style="red"
Summary 1, , 2014-06-23, 2014-07-09, 42%
  Summary 2, , , 2014-07-21, 84%
  "Sum\"mary\\3", , 2014-07-02, , 63%
}}}
""")
        self.assertEqual(expected, page.text)

    def test_update_tasks_empty(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
{{{#!Gantt id="deadbeef"
Blah blah blah...
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        req = self._test_update_tasks(page, [])
        result = self._json_from_req(req)
        version = page.version + 1
        self.assertEqual(True, result['valid'])
        self.assertEqual(version, result['version'])
        page = WikiPage(self.env, page.name)
        self.assertEqual(version, page.version)
        expected = _norm_newline("""\
{{{#!Gantt id="deadbeef" style="red"
}}}
""")
        self.assertEqual(expected, page.text)

    def test_update_tasks_empty_with_old_style(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
{{{
#!Gantt id="deadbeef"
Blah blah blah...
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        self._test_update_tasks(page, [])
        page = WikiPage(self.env, page.name)
        expected = _norm_newline("""\
{{{#!Gantt id="deadbeef" style="red"
}}}
""")
        self.assertEqual(expected, page.text)

    def test_update_tasks_minimum(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
{{{#!Gantt id="deadbeef"
Blah blah blah...
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        tasks = [
            {'level':1, 'parent': None, 'data': {'subjectName': 'Summary 1'}},
            {'level':1, 'parent': None, 'data': {'subjectName': 'Summary 2'}},
            {'level':1, 'parent': None,
             'data': {'subjectName': r'Test, "test", te\st'}},
            ]
        req = self._test_update_tasks(page, tasks)
        result = self._json_from_req(req)
        version = page.version + 1
        self.assertEqual(True, result['valid'])
        self.assertEqual(version, result['version'])
        page = WikiPage(self.env, page.name)
        self.assertEqual(version, page.version)
        expected = _norm_newline(
r"""{{{#!Gantt id="deadbeef" style="red"
Summary 1, , , , 
Summary 2, , , , 
"Test, \"test\", te\\st", , , , 
}}}
""")
        self.assertEqual(expected, page.text)

    def test_update_tasks_without_permission(self):
        permsys = PermissionSystem(self.env)
        permsys.grant_permission('anonymous', 'WIKI_VIEW')
        perm = PermissionCache(self.env, 'anonymous')

        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        content = page.text = _norm_newline("""\
{{{#!Gantt id="deadbeef"
Blah blah blah...
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        req = self._test_update_tasks(page, [], perm=perm)
        self.assertEqual('403 Forbidden', req._status)
        result = self._json_from_req(req)
        self.assertEqual(False, result['valid'])
        self.assertTrue('WIKI_MODIFY' in result['content'], result['content'])
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(1, page.version)
        self.assertEqual(content, page.text)

    def test_update_tasks_with_non_gantt_processor(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
This line should not be modified: `{{{#!Gantt id="deadbeef"`
blah.
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        req = self._test_update_tasks(page, [])
        result = self._json_from_req(req)
        self.assertEqual(False, result['valid'])

    def test_update_tasks_with_braces(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
{{{#!Gantt id="deadbeef"
Summary{}
  }}} aaaa
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        tasks = [
            {'level':1, 'parent': None, 'data': {'subjectName': 'Summary{}'}},
            {'level':1, 'parent': None, 'data': {'subjectName': 'Summary 2'}},
            ]
        req = self._test_update_tasks(page, tasks)
        result = self._json_from_req(req)
        version = page.version + 1
        self.assertEqual(True, result['valid'])
        self.assertEqual(version, result['version'])
        page = WikiPage(self.env, page.name)
        self.assertEqual(version, page.version)
        expected = _norm_newline("""\
{{{#!Gantt id="deadbeef" style="red"
Summary{}, , , , 
Summary 2, , , , 
}}}
""")
        self.assertEqual(expected, page.text)

    def test_update_tasks_with_multiple_macros(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
{{{#!Gantt id="beefdeadbeef"
Summary 1
}}}

{{{#!Gantt id="deadbeef"
Summary 2
}}}

{{{#!Gantt id="beefbeefbeef"
Summary 3
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        tasks = [
            {'level':1, 'parent': None, 'data': {'subjectName': 'Summary A'}},
            {'level':1, 'parent': None, 'data': {'subjectName': 'Summary B'}},
            ]
        req = self._test_update_tasks(page, tasks)
        result = self._json_from_req(req)
        version = page.version + 1
        self.assertEqual(True, result['valid'], result['content'])
        self.assertEqual(version, result['version'])
        page = WikiPage(self.env, page.name)
        self.assertEqual(version, page.version)
        expected = _norm_newline("""\
{{{#!Gantt id="beefdeadbeef"
Summary 1
}}}

{{{#!Gantt id="deadbeef" style="red"
Summary A, , , , 
Summary B, , , , 
}}}

{{{#!Gantt id="beefbeefbeef"
Summary 3
}}}
""")
        self.assertEqual(expected, page.text)

    def test_update_tasks_with_non_alphanum_id(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
{{{#!Gantt id="*+abc){x}("
Blah blah blah...
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        req = self._test_update_tasks(page, [], id='*+abc){x}(')
        result = self._json_from_req(req)
        version = page.version + 1
        self.assertEqual(True, result['valid'])
        self.assertEqual(version, result['version'])
        page = WikiPage(self.env, page.name)
        self.assertEqual(version, page.version)
        expected = _norm_newline("""\
{{{#!Gantt id="*+abc){x}(" style="red"
}}}
""")
        self.assertEqual(expected, page.text)

    def test_update_tasks_with_ticket_id(self):
        page = WikiPage(self.env, 'NewPage')
        self.assertEqual(False, page.exists)
        page.text = _norm_newline("""\
{{{#!Gantt id="deadbeef"
}}}
""")
        _page_save(page, 'anonymous', '', '::1')
        self.assertEqual(1, page.version)
        tickets = [_insert_ticket(self.env, summary='Ticket 1'),
                   _insert_ticket(self.env, summary='Ticket 2')]
        tasks = [
            {'level':1, 'parent': None,
             'data': {'subjectName': 'Summary 1', 'ticket': tickets[1].id}},
            {'level':1, 'parent': None,
             'data': {'subjectName': 'Summary 2', 'ticket': tickets[0].id}},
            {'level':1, 'parent': None,
             'data': {'subjectName': 'Summary 3', 'ticket': '1,#2'}},
            ]
        req = self._test_update_tasks(page, tasks)
        result = self._json_from_req(req)
        version = page.version + 1
        self.assertEqual(True, result['valid'])
        self.assertEqual(version, result['version'])
        page = WikiPage(self.env, page.name)
        self.assertEqual(version, page.version)
        expected = _norm_newline(
r"""{{{#!Gantt id="deadbeef" style="red"
#%(t1)d Summary 1, , , , 
#%(t2)d Summary 2, , , , 
Summary 3, , , , 
}}}
""" % {'t1': tickets[1].id, 't2': tickets[0].id})
        self.assertEqual(expected, page.text)


class WikiGanttChartTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', WikiGanttChartModule])
        self.mod = WikiGanttChartModule(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_parse(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = """\
Summary 1, admin,         2014-07-01, 2014-07-20, 42%
Summary 2, ,              2014-07-02, 2014-07-21, 0%
Summary 3, "admin,guest", 2014-07-03, 2014-07-22,
Summary 4, admin,         2014-07-04, ,           100%
Summary 5, admin,         ,           2014-07-24, 101%
"""
        gantt.parse_macro(id='deadbeef', body=body)
        tasks = gantt.tasks
        self.assertEqual(5, len(tasks))

        self.assertEqual('Summary 1', tasks[0]['data'].get('subjectName'))
        self.assertEqual(['admin'], tasks[0]['data'].get('owner'))
        self.assertEqual('2014-07-01', tasks[0].get('startDate'))
        self.assertEqual('2014-07-20', tasks[0].get('dueDate'))
        self.assertEqual(42, tasks[0]['ratio'])
        self.assertEqual(None, tasks[0]['parent'])

        self.assertEqual('Summary 2', tasks[1]['data'].get('subjectName'))
        self.assertEqual([], tasks[1]['data'].get('owner'))
        self.assertEqual('2014-07-02', tasks[1].get('startDate'))
        self.assertEqual('2014-07-21', tasks[1].get('dueDate'))
        self.assertEqual(0, tasks[1]['ratio'])

        self.assertEqual('Summary 3', tasks[2]['data'].get('subjectName'))
        self.assertEqual(['admin', 'guest'], tasks[2]['data'].get('owner'))
        self.assertEqual(None, tasks[2].get('ratio'))

        self.assertEqual('Summary 4', tasks[3]['data'].get('subjectName'))
        self.assertEqual(None, tasks[3].get('dueDate'))
        self.assertEqual(100, tasks[3].get('ratio'))

        self.assertEqual('Summary 5', tasks[4]['data'].get('subjectName'))
        self.assertEqual(None, tasks[4].get('startDate'))
        self.assertEqual(100, tasks[4].get('ratio'))

        for task in tasks:
            self.assertEqual(1, task['level'])
            self.assertEqual(None, task['parent'])

    def test_parse_empty_summary(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = """\
Summary 1,,,,
, , , ,

Summary 2,,,,
"""
        gantt.parse_macro(id='deadbeef', body=body)
        tasks = gantt.tasks
        self.assertEqual(2, len(tasks))
        _check_task(self, tasks[0], summary='Summary 1')
        _check_task(self, tasks[1], summary='Summary 2')

    def test_parse_summary(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = r"""Summary 1
"Sum, \"ma\ry\" 2"
Summary 3
"""
        gantt.parse_macro(id='deadbeef', body=body)
        tasks = gantt.tasks
        self.assertEqual(3, len(tasks))

        self.assertEqual('Summary 1', tasks[0]['data'].get('subjectName'))
        self.assertEqual(r'Sum, "ma\ry" 2', tasks[1]['data'].get('subjectName'))
        self.assertEqual('Summary 3', tasks[2]['data'].get('subjectName'))
        for task in tasks:
            self.assertEqual(1, task['level'])
            self.assertEqual(None, task['parent'])
            self.assertEqual(None, task['data'].get('owner'))
            self.assertEqual(None, task.get('startDate'))
            self.assertEqual(None, task.get('dueDate'))
            self.assertEqual(None, task.get('ratio'))

    def test_hierarchical_summary(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = r"""Summary 1
    Summary 1.1
Summary 2
  Summary 2.1
    Summary 2.1.1
    Summary 2.1.2
  Summary 2.2
    "Summary 2.2.1"
      "Summary\"2.2\\1.1"
        Summary 2.2.1.1.1
Summary 3
"""
        gantt.parse_macro(id='deadbeef', body=body)
        iterator = iter(gantt.tasks)
        next_task = lambda: next(iterator)
        _check_task(self, next_task(),
                    parent=None, level=1, summary='Summary 1')
        _check_task(self, next_task(),
                    parent=0, level=2, summary='Summary 1.1')
        _check_task(self, next_task(),
                    parent=None, level=1, summary='Summary 2')
        _check_task(self, next_task(),
                    parent=2, level=2, summary='Summary 2.1')
        _check_task(self, next_task(),
                    parent=3, level=3, summary='Summary 2.1.1')
        _check_task(self, next_task(),
                    parent=3, level=3, summary='Summary 2.1.2')
        _check_task(self, next_task(),
                    parent=2, level=2, summary='Summary 2.2')
        _check_task(self, next_task(),
                    parent=6, level=3, summary='Summary 2.2.1')
        _check_task(self, next_task(),
                    parent=7, level=4, summary=r'Summary"2.2\1.1')
        _check_task(self, next_task(),
                    parent=8, level=5, summary='Summary 2.2.1.1.1')
        _check_task(self, next_task(),
                    parent=None, level=1, summary='Summary 3')
        self.assertRaises(StopIteration, next_task)

        for task in gantt.tasks:
            self.assertEqual(None, task['data'].get('owner'))
            self.assertEqual(None, task.get('startDate'))
            self.assertEqual(None, task.get('dueDate'))
            self.assertEqual(None, task.get('ratio'))

    def test_using_tab_characters(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = """\
Summary 1
    Summary 1.1
        Summary 1.1.1
\tSummary 1.1.2
Summary 2
\tSummary 2.1
\t\tSummary 2.1.1
"""
        gantt.parse_macro(id='deadbeef', body=body)
        iterator = iter(gantt.tasks)
        next_task = lambda: next(iterator)
        _check_task(self, next_task(),
                    parent=None, level=1, summary='Summary 1')
        _check_task(self, next_task(),
                    parent=0, level=2, summary='Summary 1.1')
        _check_task(self, next_task(),
                    parent=1, level=3, summary='Summary 1.1.1')
        _check_task(self, next_task(),
                    parent=1, level=3, summary='Summary 1.1.2')
        _check_task(self, next_task(),
                    parent=None, level=1, summary='Summary 2')
        _check_task(self, next_task(),
                    parent=4, level=2, summary='Summary 2.1')
        _check_task(self, next_task(),
                    parent=5, level=3, summary='Summary 2.1.1')
        self.assertRaises(StopIteration, next_task)

    def test_invalid_indentation(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = """\
Summary 1
    Summary 1.1
      Summary 1.1.1
   Summary 1.2
  Summary 2
 Summary 3
Summary 4
"""
        gantt.parse_macro(id='deadbeef', body=body)
        tasks = gantt.tasks
        self.assertEqual(7, len(tasks))
        _check_task(self, tasks[0], parent=None, level=1, summary='Summary 1')
        _check_task(self, tasks[1], parent=0, level=2, summary='Summary 1.1')
        _check_task(self, tasks[2], parent=1, level=3, summary='Summary 1.1.1')
        _check_task(self, tasks[3], parent=0, level=2, summary='Summary 1.2')
        _check_task(self, tasks[4], parent=None, level=1, summary='Summary 2')
        _check_task(self, tasks[5], parent=None, level=1, summary='Summary 3')
        _check_task(self, tasks[6], parent=None, level=1, summary='Summary 4')

    def test_export_with_wiki_modify(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = "Summary 1\r\n"
        gantt.parse_macro(id='deadbeef', body=body)
        exported = gantt.export()
        self.assertEqual('deadbeef', exported['id'])
        self.assertEqual(True, exported['writable'])

    def test_export_if_versioned_page(self):
        page = WikiPage(self.env, 'NewPage')
        page.text = 'blah'
        _page_save(page, 'anonymous', '@1', '::1')
        self.assertEqual(1, page.version)
        page.text = 'blah blah'
        _page_save(page, 'anonymous', '@2', '::1')
        self.assertEqual(2, page.version)

        page = WikiPage(self.env, 'NewPage', version=1)
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = "Summary 1\r\n"
        gantt.parse_macro(id='deadbeef', body=body)
        exported = gantt.export()
        self.assertEqual('deadbeef', exported['id'])
        self.assertEqual(False, exported['writable'])

    def test_export_without_wiki_modify(self):
        permsys = PermissionSystem(self.env)
        permsys.grant_permission('anonymous', 'WIKI_VIEW')
        perm = PermissionCache(self.env, 'anonymous')

        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page, perm=perm)
        gantt = WikiGanttChart(self.mod, req, page)
        body = "Summary 1\r\n"
        gantt.parse_macro(id='deadbeef', body=body)
        exported = gantt.export()
        self.assertEqual('deadbeef', exported['id'])
        self.assertEqual(False, exported['writable'])

    def test_empty_summary(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = """\
Summary 1, ,      2014-07-02, 2014-07-21,
         , admin, 2014-07-14, 2014-07-22,
"""
        try:
            gantt.parse_macro(id='deadbeef', body=body)
            self.fail('WikiGanttChartError not raised')
        except WikiGanttChartError as e:
            self.assertEqual('Task name is missing in line 2', unicode(e))

    def test_invalid_date(self):
        page = WikiPage(self.env, 'NewPage')
        req = _create_req(page=page)
        gantt = WikiGanttChart(self.mod, req, page)
        body = """\
Summary 1, ,      2014-07-02, 2014-07-21,
Summary 2, admin, 2014-07-32, 2014-07-22,
"""
        try:
            gantt.parse_macro(id='deadbeef', body=body)
            self.fail('WikiGanttChartError not raised')
        except WikiGanttChartError as e:
            self.assertEqual('Invalid date format in line 2: "2014-07-32"',
                              unicode(e))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(WikiTestCase))
    suite.addTest(unittest.makeSuite(WikiGanttChartTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
