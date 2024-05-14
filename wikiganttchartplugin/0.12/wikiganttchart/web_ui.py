# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import json
import pkg_resources
import re
import sys
import time
from datetime import datetime, timedelta

from trac.core import Component, TracError, implements
from trac.env import Environment
from trac.perm import PermissionError
from trac.resource import ResourceNotFound
from trac.test import Mock, MockPerm
from trac.ticket.api import IMilestoneChangeListener, TicketSystem
from trac.ticket.model import Milestone, Ticket
from trac.util import hex_entropy
from trac.util.html import tag
from trac.util.datefmt import localtz, to_datetime, to_utimestamp, utc
from trac.util.text import expandtabs, exception_to_unicode, to_unicode
from trac.web.api import IRequestHandler, IRequestFilter, RequestDone
from trac.web.chrome import (
    Chrome, ITemplateProvider, add_script, add_script_data, add_stylesheet,
)
from trac.web.main import FakeSession
from trac.wiki.api import IWikiMacroProvider, IWikiPageManipulator
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage
from trac.wiki.parser import WikiParser
try:
    from trac.web.chrome import web_context
except ImportError:
    from trac.mimeview.api import Context
    web_context = Context.from_request
    del Context

from .api import (
    _, N_, ChoiceOption, IntOption, Option, TEXTDOMAIN, add_domain, babel,
    db_exc, getargspec, gettext, iso8601_parse_date, iso8601_format_date,
    locale_en, l10n_format_datetime, tag_,
)

if sys.version_info[0] != 2:
    unicode = str
    xrange = range

_use_jinja2 = hasattr(Chrome, 'jenv')

_htdocs_dirs = (
    ('wikiganttchart', pkg_resources.resource_filename(__name__, 'htdocs')),
)

_templates_dirs = (
    pkg_resources.resource_filename(
        __name__,
        'templates/{0}'.format('jinja2' if _use_jinja2 else 'genshi'),
    ),
)

_has_ipnr = 'remote_addr' in getargspec(WikiPage.save)[0]

MACRO_NAME = 'Gantt'
NEWLINE = u'\r\n'


def _send_json(req, data, status=200):
    data = json.dumps(data)
    if isinstance(data, unicode):
        data = data.encode('utf-8')
    req.send(data, 'text/javascript', status)


def _send_json_exception(req, e, status=200):
    data = {'valid': False, 'content': to_unicode(e)}
    _send_json(req, data, status)


def new_id():
    return hex_entropy(12)


if hasattr(datetime, 'strptime'):
    def parse_json_date(value, tzinfo=None):
        dt = datetime.strptime(value, '%Y-%m-%d')
        dt = to_datetime(dt, tzinfo=tzinfo)
        if dt.tzinfo:
            dt = dt.astimezone(tzinfo)
        else:
            dt = tzinfo.localize(dt)
        if hasattr(tzinfo, 'normalize'):
            dt = tzinfo.normalize(dt)
        return dt
else:
    def parse_json_date(value, tzinfo=None):
        if not value:
            return None
        tt = time.strptime(value, '%Y-%m-%d')
        dt = to_datetime(datetime(*tt[:6]), tzinfo=tzinfo)
        if dt.tzinfo:
            dt = dt.astimezone(tzinfo)
        else:
            dt = tzinfo.localize(dt)
        if hasattr(tzinfo, 'normalize'):
            dt = tzinfo.normalize(dt)
        return dt


class WikiGanttChartError(Exception):
    pass


class WikiGanttChart(object):

    def __init__(self, component, req, model):
        resource = model.resource
        self.mod = component
        self.env = component.env
        self.log = component.log
        self.req = req
        self.tz = req.tz
        self.locale = req.locale
        self.context = web_context(req, resource)
        self.ratio = None
        self.style = None
        self.tasks = []
        self.model = model
        if resource.realm == 'wiki':
            if resource.version or 'preview' in req.args:
                self.writable = False
            else:
                action = ('WIKI_ADMIN', 'WIKI_MODIFY')[model.readonly == 0]
                self.writable = action in req.perm(resource)
        elif resource.realm == 'milestone':
            self.writable = 'MILESTONE_MODIFY' in req.perm(resource)
        self.ticket_creatable = 'TICKET_CREATE' in req.perm

    def gen_id(self):
        self._id = new_id()

    def parse_macro(self, **data):
        if 'id' in data:
            self._id = data['id']
        else:
            self.gen_id()
        self.style = data.get('style')
        if 'body' in data:
            self._parse_macro_body(data['body'])
        elif 'tasks' in data:
            self._conv_task_list(data['tasks'])
        else:
            self.tasks = []

    @property
    def id(self):
        return self._id

    def export(self):
        def fn(task):
            if task == {}:
                return {}
            return task.to_dict()
        return {'id': self._id, 'tasks': [fn(task) for task in self.tasks],
                'writable': self.writable, 'style': self.style, 'zoom': 4,
                'ticketCreatable': self.ticket_creatable}

    def to_json(self):
        return json.dumps(self.export())

    _replace_macro_re = re.compile(r"""
^[ ]*\{\{\{
    (?:\r?\n)?
    \#!%s
    (?P<params>[^\n]*)
    \n
(?P<body>
    (?:(?!^[ ]*\}\}\}[ ]*\n)
       [^\n]*\n)*?
)
[ ]*\}\}\}[ ]*(?:\n|\Z)
        """ % re.escape(MACRO_NAME),
        re.MULTILINE | re.VERBOSE)

    def replace_macro(self, data, content):
        self.tasks = data.get('tasks')
        self._append_formatted_value()
        self._id = data.get('id')
        self.style = data.get('style')

        content = expandtabs(content)
        content = ''.join(line + '\n' for line in content.splitlines())
        formatter = Formatter(self.env, self.context)
        id_ = None
        for match in self._replace_macro_re.finditer(content):
            args = formatter.parse_processor_args(match.group('params'))
            id_ = args.get('id')
            if id_ == self._id:
                break
        if id_ != self._id:
            raise WikiGanttChartError(_("No %(name)s macro.", name=MACRO_NAME))
        generated = self.generate_macro()
        self._parse_macro_body(self._last_body)
        data['tasks'] = self.tasks
        content = content[:match.start()] + generated + content[match.end():]
        return ''.join(line + NEWLINE for line in content.splitlines())

    def generate_macro_body(self):
        def escape(text):
            if not text:
                text = ''
            elif any(c in text for c in r',\"'):
                text = '"%s"' % text.replace('\\', r'\\').replace('"', r'\"')
            return text

        def make_task(task):
            if task == {}:
                return ''

            indent = int(task.get('level')) or 1
            data = task.get('data') or {}
            subject = data.get('subjectName')
            ticket_id = data.get('ticket')
            ticket = None
            if ticket_id:
                try:
                    ticket_id = int(ticket_id)
                except:
                    ticket_id = None
            if ticket_id:
                try:
                    ticket = Ticket(self.env, ticket_id)
                except ResourceNotFound:
                    pass
                else:
                    subject = "#%s %s" % (ticket.id, subject)
            date = {}
            for key in ("startDate", "dueDate"):
                value = task.get(key) or None
                if value:
                    try:
                        value = self._parse_date(value)
                        value = iso8601_format_date(value)
                    except ValueError:
                        value = None
                date[key] = value
            ratio = None
            if isinstance(task.get('ratio'), int):
                ratio = u'%d%%' % task.get('ratio')
            owner = data.get('owner')
            if isinstance(owner, list):
                owner = ','.join(owner)

            line = [subject, owner, date['startDate'], date['dueDate'], ratio]
            return '  ' * (indent - 1) + ', '.join(map(escape, line))

        return ''.join(line + NEWLINE for line in map(make_task, self.tasks))

    def generate_macro(self):
        buf = []
        self._last_body = self.generate_macro_body()
        buf.append(u'{{{#!%s id="%s"' % (MACRO_NAME, self._id))
        if self.style:
            buf.append(u' style="%s"' % self.style)
        buf.append(NEWLINE)
        buf.append(self._last_body)
        buf.append('}}}')
        buf.append(NEWLINE)
        return ''.join(buf)

    def create_new_ticket_with_task(self, task):
        data = task['data']
        owner = data.get('owner')
        if owner and isinstance(owner, list):
            owner = owner[0]
        else:
            owner = None
        start = task.get('startDate') or None
        due = task.get('dueDate') or None
        if start:
            dt = self._parse_date(start)
            start = self.mod.format_start_date(dt)
        if due:
            dt = self._parse_date(due)
            due = self.mod.format_due_date(dt)
        kwargs = {}
        if self.model.resource.realm == 'milestone':
            kwargs['milestone'] = self.model.name
        return self._create_new_ticket(data['subjectName'], owner, start, due,
                                       **kwargs)

    def _parse_macro_body(self, body):
        body = expandtabs(body)
        self._indents = []
        tasks = (self._parse_line(l, i)
                 for i, l in enumerate(body.splitlines()))
        self._conv_task_list(tasks)

    def _parse_line(self, line, i):
        if not line.strip(', \t'):
            return None

        task = {}
        level = self._get_level(line, i)
        fields = self._iter_fields(line.strip(), i)

        try:
            title = next(fields)
            m = re.search(r'\A#(\d+)\s*(.*)\Z', title)
            if m:
                task['ticket'] = m.group(1)
                task['name'] = m.group(2)
            else:
                task['name'] = title
            owner = [value.strip() for value in next(fields).split(",")]
            task['owner'] = [v for v in owner if v]
            task['startDate'] = next(fields)
            task['dueDate'] = next(fields)
            ratio_src = next(fields)
            ratio = None
            m = re.search(r'^(\d+)\s*%?', ratio_src)
            if m:
                r = int(m.group(1))
                if r < 0:
                    r = 0
                if r > 100:
                    r = 100
                ratio = r
            task['ratio'] = ratio
        except StopIteration:
            pass

        if not task:
            return None
        task['level'] = level
        return task

    def _iter_fields(self, line, idx):
        line = ',' + line
        while len(line) > 0:
            col = ""
            match = re.search(r'^,\s*"(((\\")|[^"])*)"\s*', line)
            if match:
                col = match.group(1).replace('\\"', '"').replace('\\\\', '\\')
            else:
                match = re.search(r'^,\s*([^,"]*)', line)
                if not match:
                    raise WikiGanttChartError(_("Unexpected '\"' in line "
                                                "%(lineno)d", lineno=idx + 1))
                else:
                    col = match.group(1)
            pos = len(match.group(0))
            yield col
            line = line[pos:]

    _indent_re = re.compile(r'\s*')

    def _get_level(self, line, i):
        indents = self._indents
        indent = len(self._indent_re.match(line).group(0))
        if indent == 0 or not indents:
            indents[:] = (indent,)
            return 1
        last_indent = indents[-1]
        if indent == last_indent:
            return len(indents)
        if indent > last_indent:
            indents.append(indent)
            return len(indents)
        while True:
            last_indent = indents.pop()
            if not indents:
                indents[:] = (indent,)
                return 1
            if indent < last_indent:
                indents[-1] = indent
                return len(indents)

    def _conv_task_list(self, tlist):
        self.tasks = []
        parents = []
        prev_lv = 0
        for idx, task in enumerate(tlist):
            lineno = idx + 1
            if task is None:
                continue

            ntask = WikiGanttTask()
            if task['level'] == 1:
                ntask['parent'] = None
            elif task['level'] <= prev_lv + 1:
                diff = prev_lv - task['level']
                for x in range(diff + 1):
                    parents.pop()
                ntask['parent'] = parents[-1]
            else:
                raise WikiGanttChartError(_("Invalid indent level in line "
                                            "%(lineno)d", lineno=lineno))

            ntask['level'] = prev_lv = task['level']
            parents.append(idx)

            for key in ('startDate', 'dueDate'):
                value = task.get(key)
                if not value:
                    continue
                try:
                    d = iso8601_parse_date(task[key])
                except ValueError:
                    raise WikiGanttChartError(_("Invalid date format in line "
                                                "%(lineno)d: \"%(value)s\"",
                                                lineno=lineno, value=value))
                else:
                    ntask[key] = iso8601_format_date(d)

            if task.get('ratio') is not None:
                ntask['ratio'] = int(task['ratio'])

            data = {}
            if task.get('name'):
                data['subjectName'] = task['name']
            else:
                raise WikiGanttChartError(_("Task name is missing in line "
                                            "%(lineno)d", lineno=lineno))

            if 'ticket' in task:
                try:
                    ticket = Ticket(self.env, int(task['ticket']))
                    data['ticket'] = ticket.id
                except ResourceNotFound:
                    pass

            if 'owner' in task:
                data['owner'] = task['owner']

            ntask['data'] = data
            self.tasks.append(ntask)
        self._append_formatted_value()

    def _append_formatted_value(self):
        tktsys = TicketSystem(self.env)
        locale = self.locale or locale_en
        for task in self.tasks:
            if task == {}:
                continue
            for key in ('startDate', 'dueDate'):
                d = task.get(key)
                if not d:
                    continue
                try:
                    d = self._parse_date(d)
                except:
                    continue
                task[key + 'Printable'] = \
                    l10n_format_datetime(d, format='MMMd', locale=locale)
                task[key + 'PrintableLong'] = \
                    l10n_format_datetime(d, format='medium', locale=locale)

            data = task['data']
            tktid = data.get('ticket')
            if tktid:
                try:
                    tktid = int(tktid)
                except:
                    tktid = None
            if tktid:
                try:
                    ticket = Ticket(self.env, tktid)
                except ResourceNotFound:
                    pass
                else:
                    title = tktsys.format_summary(
                            ticket['summary'], ticket['status'],
                            ticket['resolution'], ticket['type'])
                    data['ticket'] = tktid = ticket.id
                    data['linkToTicket'] = unicode(tag.a(
                        '#%d' % tktid, href=self.req.href('ticket', tktid),
                        class_=ticket['status'], title=title))

    def _create_new_ticket(self, summary, owner, start_date, due_date,
                           **kwargs):
        ticket = Ticket(self.env)
        resource = self.model.resource
        realm = resource.realm
        if realm == 'wiki':
            description = '[wiki:"%s"]' % resource.id
        elif realm == 'milestone':
            description = '[milestone:"%s"]' % resource.id
        ticket['status'] = 'new'
        ticket['reporter'] = self.req.authname
        ticket['summary'] = summary
        ticket['owner'] = owner
        ticket['description'] = description
        ticket['type'] = self._get_ticket_type()
        if self.mod.start_date_name:
            ticket[self.mod.start_date_name] = start_date
        if self.mod.due_date_name:
            ticket[self.mod.due_date_name] = due_date
        for name, value in kwargs.iteritems():
            ticket[name] = value
        ticket.insert()
        return ticket

    def _get_ticket_type(self):
        tktsys = TicketSystem(self.env)
        options = None
        for field in tktsys.fields:
            if field['name'] == 'type':
                options = field.get('options')
                break
        if not options:
            options = ()

        default = self.mod.ticket_default_type
        if default in options:
            return default
        default = field['value']
        if default in options:
            return default
        if options:
            default = options[0]
        return default

    def _parse_date(self, value):
        return parse_json_date(value, tzinfo=self.tz)


class WikiGanttTask(object):

    __slots__ = ('level', 'parent', 'startDate', 'dueDate', 'data', 'ratio',
                 'startDatePrintable', 'startDatePrintableLong',
                 'dueDatePrintable', 'dueDatePrintableLong')

    def __init__(self):
        self.level = 1
        self.parent = None
        self.startDate = None
        self.startDatePrintable = None
        self.startDatePrintableLong = None
        self.dueDate = None
        self.dueDatePrintable = None
        self.dueDatePrintableLong = None
        self.data = {}
        self.ratio = None

    def to_dict(self):
        return dict(level=self.level,
                    parent=self.parent,
                    startDate=self.startDate,
                    startDatePrintable=self.startDatePrintable,
                    startDatePrintableLong=self.startDatePrintableLong,
                    dueDate=self.dueDate,
                    dueDatePrintable=self.dueDatePrintable,
                    dueDatePrintableLong=self.dueDatePrintableLong,
                    data=self.data,
                    ratio=self.ratio)

    def get(self, name, *args):
        if len(args) > 1:
            raise TypeError()
        if name in self.__slots__:
            return getattr(self, name)
        if len(args) == 0:
            raise KeyError(repr(name))
        return args[0]  # default value

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        setattr(self, name, value)


class WikiGanttChartModule(Component):

    implements(IMilestoneChangeListener, IRequestFilter, IRequestHandler,
               ITemplateProvider, IWikiMacroProvider, IWikiPageManipulator)

    _date_formats = ['YYYY-MM-dd', 'YYYY/MM/dd', 'YYYY.MM.dd']

    start_date_name = Option(
        'wikiganttchart', 'ticket.start_date', default='start_date',
        doc=N_("Name for ''start date'' field of ticket"))

    start_date_format = ChoiceOption(
        'wikiganttchart', 'ticket.start_date.format', _date_formats,
        doc=N_("Format for ''start date'' field of ticket"))

    due_date_name = Option(
        'wikiganttchart', 'ticket.due_date', default='due_date',
        doc=N_("Name for ''due date'' field of ticket"))

    due_date_format = ChoiceOption(
        'wikiganttchart', 'ticket.due_date.format', _date_formats,
        doc=N_("Format for ''due date'' field of ticket"))

    ticket_default_type = Option(
        'wikiganttchart', 'ticket.default_type', default=None,
        doc=N_("Default type for a new ticket created by the plugin"))

    short_term_updating = IntOption(
        'wikiganttchart', 'short_term_updating', '300',
        N_("Seconds in the short-time updating. If the short-term updating, "
           "it wouldn't create a new version of wiki page."))

    def __init__(self):
        if pkg_resources.resource_isdir(__name__, 'locale'):
            locale_dir = pkg_resources.resource_filename(__name__, 'locale')
            add_domain(self.env.path, locale_dir)
        self._stylesheet_files = self.config.getlist('wikiganttchart',
                                                     'stylesheet_files')
        self._javascript_files = self.config.getlist('wikiganttchart',
                                                     'javascript_files')

    def format_start_date(self, d):
        format = self.start_date_format or 'YYYY-mm-dd'
        return self._format_date(d, format=format)

    def format_due_date(self, d):
        format = self.due_date_format or 'YYYY-mm-dd'
        return self._format_date(d, format=format)

    _date_format_re = re.compile(r'[yY]+|M+|[dD]+|h+|m+|s+')

    def _format_date(self, d, format):
        def repl(match):
            match = match.group(0)[0]
            if match in ('y', 'Y'):
                return '%Y'
            if match == 'M':
                return '%m'
            if match in ('d', 'D'):
                return '%d'
            if match == 'h':
                return '%H'
            if match == 'm':
                return '%M'
            if match == 's':
                return '%S'
        format = self._date_format_re.sub(repl, format)
        if isinstance(format, unicode):
            format = format.encode('utf-8')
        return d.strftime(format)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if (template and template.endswith('.html') and
            template in ('wiki_edit.html', 'wiki_view.html',
                         'milestone_edit.html', 'milestone_view.html',
                         'roadmap.html')):
            self._add_header_contents(req)
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return _htdocs_dirs

    def get_templates_dirs(self):
        return _templates_dirs

    # IWikiMacroProvider methods

    def get_macros(self):
        return [MACRO_NAME]

    _macro_description = N_("""\
`[[Gantt]]` displays gantt editor in milestone and Trac wiki.
""")

    def get_macro_description(self, name):
        from trac.wiki.macros import WikiMacroBase
        if hasattr(WikiMacroBase, '_domain'):
            return TEXTDOMAIN, self._macro_description
        else:
            return gettext(self._macro_description)

    def is_inline(self, content):
        return False

    def expand_macro(self, formatter, name, text, args):
        req = formatter.req
        context = formatter.context
        resource = context.resource
        params = {}
        model = self._get_model(resource.realm, resource.id, resource.version)
        if resource.realm == 'wiki':
            params['version'] = model.version
        elif resource.realm == 'milestone':
            params['version'] = None
        else:
            return tag.div(tag_("%(name)s macro is disabled here.",
                                name=MACRO_NAME),
                           class_='system-message')

        if args:
            args.update({'body': text})
        else:
            args = {}
        try:
            gantt = WikiGanttChart(self, req, model)
            gantt.parse_macro(**args)
        except WikiGanttChartError as e:
            return tag.div(
                tag.div(tag.strong('Error: Macro WikiGanttChart failed'),
                        tag.pre(to_unicode(e), class_='system-message')),
                class_='system-message')

        params.update({
            'gantt': gantt, 'realm': resource.realm, 'id': resource.id,
            'token': req.form_token,
            'updateUrl': req.href('_wikiganttchart', 'update'),
            'createTicketUrl': req.href('_wikiganttchart', 'create-ticket'),
        })
        return self._render_fragment(req, 'wikiganttchart-macro.html', params)

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info in ('/_wikiganttchart/update',
                                 '/_wikiganttchart/create-ticket')

    def process_request(self, req):
        xhr = req.get_header('X-Requested-With') == 'XMLHttpRequest'
        if req.method != 'POST' or not xhr:
            raise PermissionError()

        realm = req.args['realm']
        try:
            model = self._get_model(realm, req.args['id'], req.args['version'])
            if realm == 'wiki':
                req.perm(model.resource).require('WIKI_MODIFY')
                if model.version != int(req.args['version']):
                    raise WikiGanttChartError(_(
                        "Sorry, this page has been modified by somebody else "
                        "since you started editing. Your changes cannot be "
                        "saved."))
                model.resource.version = None
            elif realm == 'milestone':
                req.perm(model.resource).require('MILESTONE_MODIFY')
            else:
                raise TracError('realm %r is invalid' % realm)

            gantt = WikiGanttChart(self, req, model)

            if req.path_info.endswith('update'):
                self._update_request(req, model, gantt)
            elif req.path_info.endswith('create-ticket'):
                self._create_ticket_request(req, model, gantt)

        except RequestDone:
            raise
        except WikiGanttChartError as e:
            _send_json_exception(req, e, 200)
        except PermissionError as e:
            _send_json_exception(req, e, 403)
        except TracError as e:
            _send_json_exception(req, e, 500)

    # IWikiPageManipulator methods

    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        self._replace_macro(page, req=req)
        return ()

    # IMilestoneChangeListener methods

    def milestone_created(self, milestone):
        if self._replace_macro(milestone):
            milestone.update()

    def milestone_changed(self, milestone, old_values):
        if old_values and 'description' in old_values and \
           self._replace_macro(milestone):
            milestone.update()

    def milestone_deleted(self, milestone):
        pass

    # Internal methods

    def _add_header_contents(self, req):
        self._add_script_data_jquery_ui(req)

        locale = req.locale and str(req.locale)
        if locale and pkg_resources.resource_exists(
                                __name__, 'htdocs/js/locale/%s.js' % locale):
            add_script(req, 'wikiganttchart/js/locale/%s.js' % locale)

        if self._stylesheet_files or self._javascript_files:
            for path in self._stylesheet_files:
                add_stylesheet(req, path)
            for path in self._javascript_files:
                add_script(req, path)
        else:
            self._add_jquery_ui(req)
            add_stylesheet(req, 'wikiganttchart/css/jquery.contextmenu.css')
            add_stylesheet(req, 'wikiganttchart/css/font-awesome.min.css')
            add_stylesheet(req, 'wikiganttchart/css/gantt.css')
            add_script(req, 'wikiganttchart/js/jquery.cookie.js')
            add_script(req, 'wikiganttchart/js/xdate.js')
            add_script(req, 'wikiganttchart/js/jquery.livequery.js')
            add_script(req, 'wikiganttchart/js/jquery.balloon.min.js')
            add_script(req, 'wikiganttchart/js/jquery.contextmenu.js')
            add_script(req, 'wikiganttchart/js/jsrender.min.js')
            add_script(req, 'wikiganttchart/js/gantt-templates.js')
            add_script(req, 'wikiganttchart/js/rmgantt.js')

    if hasattr(Chrome, 'add_jquery_ui'):
        def _add_jquery_ui(self, req):
            Chrome(self.env).add_jquery_ui(req)
    else:
        def _add_jquery_ui(self, req):
            add_stylesheet(req, 'wikiganttchart/css/jquery-ui.min.css')
            add_script(req, 'wikiganttchart/js/jquery-ui.min.js')

    def _add_script_data_jquery_ui(self, req):
        locale = req.locale if babel else None
        if locale:
            from babel.dates import (get_date_format, get_day_names,
                                     get_month_names)
            def month_names(width):
                names = get_month_names(width, locale=locale)
                return [names[i] for i in xrange(1, 13)]
            def day_names(width):
                names = get_day_names(width, locale=locale)
                return [names[(i + 6) % 7] for i in xrange(7)]
            def date_format():
                values = {'yyyy': 'yy', 'y': 'yy',
                          'M': 'm', 'MM': 'mm', 'MMM': 'M',
                          'd': 'd', 'dd': 'dd'}
                return get_date_format('medium', locale=locale).format % values
        else:
            def month_names(width):
                if width == 'wide':
                    return ('January', 'February', 'March', 'April',
                            'May', 'June', 'July', 'August',
                            'September', 'October', 'November', 'December')
                if width == 'abbreviated':
                    return ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
            def day_names(width):
                if width == 'wide':
                    return ('Sunday', 'Monday', 'Tuesday', 'Wednesday',
                            'Thursday', 'Friday', 'Saturday')
                if width == 'abbreviated':
                    return ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')
                if width == 'narrow':
                    return ('S', 'M', 'T', 'W', 'T', 'F', 'S')
            def date_format():
                return 'M d, yy'

        format_month = _("$month$year")
        data = {}
        data['datepicker'] = {
            'monthNames': month_names('wide'),
            'monthNamesShort': month_names('abbreviated'),
            'dayNames': day_names('wide'),
            'dayNamesShort': day_names('abbreviated'),
            'dayNamesMin': day_names('narrow'),
            'dateFormat': 'yy-mm-dd',
            'prevText': _("Prev month"),
            'nextText': _("Next month"),
            'currentText': _("Today"),
            'closeText': _("Done"),
            'yearSuffix': (
                format_month.replace('$month', '').replace('$year', '')),
            'showMonthAfterYear': (
                format_month.find('$month') > format_month.find('$year')),
            'weekHeader': _("Wk"),
            'showButtonPanel': True,
        }
        add_script_data(req, {'wikiganttchart': data})

    def _create_request(self):
        return Mock(href=self.env.href, abs_href=self.env.abs_href,
                    authname='anonymous', perm=MockPerm(),
                    session=FakeSession({}),
                    chrome={'notices': [], 'warnings': []},
                    args={}, arg_list=(), locale=locale_en, tz=localtz)

    if _use_jinja2:
        def _render_fragment(self, req, template, data):
            return Chrome(self.env).render_fragment(req, template, data)
    else:
        def _render_fragment(self, req, template, data):
            return Chrome(self.env).render_template(req, template, data, None,
                                                    fragment=True)

    _empty_macro_re = re.compile(
        r'!?\{\{\{.*?\}\}\}|'
        r'!?`[^`]*`|'
        r'!?\[\[%(name)s *(?:\(.*?\))? *]]' %
        {'name': MACRO_NAME})

    def _replace_macro(self, model, req=None):
        if req is None:
            req = self._create_request()
        resource = model.resource
        realm = resource.realm
        formatter = Formatter(self.env, web_context(req, resource))
        if realm == 'wiki':
            text = model.text
        elif realm == 'milestone':
            text = model.description

        def repl(match):
            entire = match.group(0)
            if entire.startswith('!'):
                return entire
            if entire.startswith('`') and entire.endswith('`'):
                return entire
            if entire.startswith('{{{') and entire.endswith('}}}'):
                return entire
            buf = []
            if match.start(0):
                buf.append(NEWLINE)
            buf.append('{{{#!%s id="%s" style="blue"' % (MACRO_NAME, new_id()))
            buf.append(NEWLINE)
            buf.append('}}}')
            if match.end(0) < len(match.string):
                buf.append(NEWLINE)
            return ''.join(buf)

        changed = False
        buf = []
        code_buf = []
        in_code_block = 0
        processor_name = None
        processor_args = None
        for line in text.splitlines():
            startmatch = None
            if WikiParser.ENDBLOCK not in line:
                startmatch = WikiParser._startblock_re.match(line)
            if startmatch:
                code_buf.append(line)
                in_code_block += 1
                if in_code_block == 1:
                    processor_name = startmatch.group(2)
                    processor_args = formatter.parse_processor_args(
                                                    line[startmatch.end():])
                continue
            if in_code_block > 0:
                code_buf.append(line)
                if line.strip() != WikiParser.ENDBLOCK:
                    continue
                in_code_block -= 1
                if in_code_block > 0:
                    continue
                if processor_name == MACRO_NAME and \
                        not processor_args.get('id'):
                    code_buf[0] = code_buf[0].replace(
                        '#!%s' % MACRO_NAME,
                        '#!%s id="%s" style="blue"' % (MACRO_NAME, new_id()))
                    changed = True
                buf.extend(code_buf)
                code_buf[:] = ()
                processor_name = None
                processor_args = None
                continue

            replaced = self._empty_macro_re.sub(repl, line)
            if replaced != line:
                changed = True
            buf.append(replaced)

        if not changed:
            return False
        buf.extend(code_buf)
        new_text = ''.join(line + NEWLINE for line in buf)
        if new_text == text:
            return False
        if realm == 'wiki':
            model.text = new_text
        elif realm == 'milestone':
            model.description = new_text
        return True

    def _get_model(self, realm, id, version):
        if realm == 'wiki':
            return WikiPage(self.env, id, version)
        if realm == 'milestone':
            return Milestone(self.env, id)

    def _update_request(self, req, model, gantt):
        realm = model.resource.realm
        if realm == 'wiki':
            old_text = model.text
            version = model.version
        elif realm == 'milestone':
            old_text = model.description
            version = None
        data = json.loads(req.args['content'])

        text = gantt.replace_macro(data, old_text)
        if old_text != text:
            version = self._save_model(req, model, text, realm)

        _send_json(req, {'valid': True, 'content': gantt.export(),
                         'version': version})

    def _create_ticket_request(self, req, model, gantt):
        req.perm.require('TICKET_CREATE')
        realm = model.resource.realm
        if realm == 'wiki':
            old_text = model.text
        elif realm == 'milestone':
            old_text = model.description
        data = json.loads(req.args['content'])
        lineno = int(req.args['line'])
        task = data['tasks'][lineno]
        ticket_id = gantt.create_new_ticket_with_task(task).id
        task['data']['ticket'] = ticket_id

        text = gantt.replace_macro(data, old_text)
        if old_text != text:
            version = self._save_model(req, model, text, realm)

        _send_json(req, {'valid': True, 'content': gantt.export(),
                         'version': version})

    def _save_model(self, req, model, text, realm):
        if realm == 'wiki':
            now = datetime.now(utc)
            if self._in_short_term(req, model, now):
                self._update_wiki_version(req, model, text, now)
            else:
                try:
                    self._save_wiki(req, model, text, now)
                except db_exc(self.env).IntegrityError as e:
                    self.log.warning('Exception caught while saving wiki '
                                     'page: %s', exception_to_unicode(e))
                    req.send('Integrity error', status=500)
            return model.version

        if realm == 'milestone':
            model.description = text
            model.update()
            return None

    if not _has_ipnr:
        def _db_update_wiki_version(self, db, req, model, text, t):
            cursor = db.cursor()
            cursor.execute("""
                UPDATE wiki SET text=%s,time=%s WHERE name=%s AND version=%s
                """,
                (text, to_utimestamp(t), model.name, model.version))

        def _save_wiki(self, req, model, text, t):
            model.text = text
            model.save(req.authname, self._comment(), t=t)

    else:
        def _db_update_wiki_version(self, db, req, model, text, t):
            cursor = db.cursor()
            cursor.execute("""
                UPDATE wiki SET text=%s,time=%s,ipnr=%s
                WHERE name=%s AND version=%s
                """,
                (text, to_utimestamp(t), req.remote_addr, model.name,
                 model.version))

        def _save_wiki(self, req, model, text, t):
            model.text = text
            model.save(req.authname, self._comment(), req.remote_addr, t=t)

    if hasattr(Environment, 'db_transaction'):
        def _update_wiki_version(self, req, model, text, t):
            with self.env.db_transaction as db:
                self._db_update_wiki_version(db, req, model, text, t)
    else:
        def _update_wiki_version(self, req, model, text, t):
            @self.env.with_transaction()
            def do_update(db):
                self._db_update_wiki_version(db, req, model, text, t)

    def _in_short_term(self, req, model, now):
        realm = model.resource.realm
        if realm == 'wiki':
            return req.authname == model.author and \
                   model.comment == self._comment() and \
                   now - model.time < \
                       timedelta(seconds=self.short_term_updating)
        raise ValueError('invalid realm %r' % realm)

    def _comment(self):
        return unicode(_("Updated automatically by !WikiGanttChartPlugin"))
