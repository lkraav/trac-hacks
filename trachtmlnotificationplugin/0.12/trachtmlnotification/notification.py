# -*- coding: utf-8 -*-

import os.path
import re
import sys
from pkg_resources import parse_version, resource_filename

try:
    from babel.core import Locale
except ImportError:
    Locale = None

from trac import __version__
from trac.core import Component, implements
from trac.attachment import AttachmentModule
from trac.env import Environment
from trac.notification import SmtpEmailSender, SendmailEmailSender
from trac.resource import ResourceNotFound
from trac.test import MockPerm
from trac.ticket.model import Ticket
from trac.ticket.web_ui import TicketModule
from trac.timeline.web_ui import TimelineModule
from trac.util.datefmt import get_timezone, localtz, to_utimestamp
from trac.util.text import to_unicode
from trac.util.translation import deactivate, make_activable, reactivate, tag_
from trac.web.api import Request
from trac.web.chrome import Chrome, ITemplateProvider
from trac.web.main import FakeSession

text_type = unicode if sys.version_info[0] == 2 else str

try:
    from trac.web.chrome import web_context
except ImportError:
    from trac.mimeview.api import Context
    web_context = Context.from_request

try:
    from trac.notification.api import INotificationFormatter
except ImportError:
    INotificationFormatter = None


_parsed_version = parse_version(__version__)
if _parsed_version >= parse_version('1.4'):
    _use_jinja2 = True
elif _parsed_version >= parse_version('1.3'):
    _use_jinja2 = hasattr(Chrome, 'jenv')
else:
    _use_jinja2 = False


if _use_jinja2:
    from trac.util.html import tag
    _template_dir = resource_filename(__name__, 'templates/jinja2')
else:
    _template_dir = resource_filename(__name__, 'templates/genshi')
    try:
        from trac.util.html import tag
    except ImportError:
        from genshi.builder import tag


_TICKET_URI_RE = re.compile(r'/ticket/(?P<tktid>[0-9]+)'
                            r'(?:#comment:(?P<cnum>[0-9]+))?\Z')


if Locale:
    def _parse_locale(lang):
        try:
            return Locale.parse(lang, sep='-')
        except:
            return Locale('en', 'US')
else:
    _parse_locale = lambda lang: None


class HtmlNotificationModule(Component):

    if INotificationFormatter:
        implements(INotificationFormatter, ITemplateProvider)
    else:
        implements(ITemplateProvider)

    # INotificationFormatter methods

    def get_supported_styles(self, transport):
        yield 'text/html', 'ticket'

    def format(self, transport, style, event):
        if style != 'text/html' or event.realm != 'ticket':
            return
        chrome = Chrome(self.env)
        req = self._create_request()
        ticket = event.target
        cnum = None
        if event.time:
            rows = self._db_query("""\
                SELECT field, oldvalue FROM ticket_change
                WHERE ticket=%s AND time=%s AND field='comment'
                """, (ticket.id, to_utimestamp(event.time)))
            for field, oldvalue in rows:
                if oldvalue:
                    cnum = int(oldvalue.rsplit('.', 1)[-1])
                    break
        link = self.env.abs_href.ticket(ticket.id)
        if cnum is not None:
            link += '#comment:%d' % cnum

        try:
            tx = deactivate()
            try:
                make_activable(lambda: req.locale, self.env.path)
                content = self._create_html_body(chrome, req, ticket, cnum,
                                                 link)
            finally:
                reactivate(tx)
        except:
            self.log.warning('Caught exception while generating html part',
                             exc_info=True)
            raise
        if isinstance(content, text_type):
            # avoid UnicodeEncodeError from MIMEText()
            content = content.encode('utf-8')
        return content

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return ()

    def get_templates_dirs(self):
        return [_template_dir]

    # public methods

    def substitute_message(self, message, ignore_exc=True):
        try:
            chrome = Chrome(self.env)
            req = self._create_request()
            tx = deactivate()
            try:
                make_activable(lambda: req.locale, self.env.path)
                return self._substitute_message(chrome, req, message)
            finally:
                reactivate(tx)
        except:
            self.log.warning('Caught exception while substituting message',
                             exc_info=True)
            if ignore_exc:
                return message
            raise

    # private methods

    if hasattr(Environment, 'db_query'):
        def _db_query(self, query, args=()):
            return self.env.db_query(query, args)
    else:
        def _db_query(self, query, args=()):
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute(query, args)
            return list(cursor)

    def _create_request(self):
        lang = self.config.get('trac', 'default_language')
        locale = _parse_locale(lang) if lang else None
        tzname = self.config.get('trac', 'default_timezone')
        tz = get_timezone(tzname) or localtz
        base_url = self.env.abs_href()
        if ':' in base_url:
            url_scheme = base_url.split(':', 1)[0]
        else:
            url_scheme = 'http'
        environ = {'REQUEST_METHOD': 'POST', 'REMOTE_ADDR': '127.0.0.1',
                   'SERVER_NAME': 'localhost', 'SERVER_PORT': '80',
                   'wsgi.url_scheme': url_scheme, 'trac.base_url': base_url}
        if locale:
            environ['HTTP_ACCEPT_LANGUAGE'] = str(locale).replace('_', '-')
        session = FakeSession()
        session['dateinfo'] = 'absolute'
        req = Request(environ, lambda *args, **kwargs: None)
        req.arg_list = ()
        req.args = {}
        req.authname = 'anonymous'
        req.form_token = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        req.session = session
        req.perm = MockPerm()
        req.href = req.abs_href
        req.locale = locale
        req.lc_time = locale
        req.tz = tz
        req.chrome = {'notices': [], 'warnings': []}
        return req

    def _substitute_message(self, chrome, req, message):
        from email import message_from_string
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        parsed = message_from_string(message)
        link = parsed.get('X-Trac-Ticket-URL')
        if not link:
            return message
        match = _TICKET_URI_RE.search(link)
        if not match:
            return message
        tktid = match.group('tktid')
        cnum = match.group('cnum')
        if cnum is not None:
            cnum = int(cnum)

        try:
            ticket = Ticket(self.env, tktid)
        except ResourceNotFound:
            return message

        container = MIMEMultipart('alternative')
        for header, value in parsed.items():
            lower = header.lower()
            if lower in ('content-type', 'content-transfer-encoding'):
                continue
            if lower != 'mime-version':
                container[header] = value
            del parsed[header]
        container.attach(parsed)

        html = self._create_html_body(chrome, req, ticket, cnum, link)
        part = MIMEText(html.encode('utf-8'), 'html')
        self._set_charset(part)
        container.attach(part)

        return container.as_string()

    def _create_html_body(self, chrome, req, ticket, cnum, link):
        tktmod = TicketModule(self.env)
        attmod = AttachmentModule(self.env)
        data = tktmod._prepare_data(req, ticket)
        tktmod._insert_ticket_data(req, ticket, data, req.authname, {})
        data['ticket']['link'] = link
        changes = data.get('changes')
        if cnum is None:
            changes = []
        else:
            changes = [change for change in (changes or [])
                              if change.get('cnum') == cnum]
        data['changes'] = changes
        context = web_context(req, ticket.resource, absurls=True)
        alist = attmod.attachment_data(context)
        alist['can_create'] = False
        data.update({'can_append': False,
                     'show_editor': False,
                     'start_time': ticket['changetime'],
                     'context': context,
                     'alist': alist,
                     'styles': self._get_styles(chrome),
                     'link': tag.a(link, href=link),
                     'tag_': tag_})
        template = 'htmlnotification_ticket.html'
        # use pretty_dateinfo in TimelineModule
        TimelineModule(self.env).post_process_request(req, template, data,
                                                      None)
        if _use_jinja2:
            return chrome.render_template(req, template, data,
                                          {'iterable': False})
        else:
            return text_type(chrome.render_template(req, template, data,
                             fragment=True))

    def _get_styles(self, chrome):
        for provider in chrome.template_providers:
            for prefix, dir_ in provider.get_htdocs_dirs():
                if prefix != 'common':
                    continue
                comm_re = re.compile(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', re.S)
                url_re = re.compile(r'\burl\([^\]]*\)')
                buf = ['#content > hr { display: none }']
                for name in ('trac.css', 'ticket.css'):
                    filename = os.path.join(dir_, 'css', name)
                    f = open(filename, 'rb')
                    try:
                        content = to_unicode(f.read())
                    finally:
                        f.close()
                    content = comm_re.sub('\n', content)
                    for line in content.splitlines():
                        line = line.rstrip()
                        if not line:
                            continue
                        if line.startswith(('@import', '@charset')):
                            continue
                        buf.append(url_re.sub('none', line))
                return ('/*<![CDATA[*/\n' +
                        '\n'.join(buf).replace(']]>', ']]]]><![CDATA[>') +
                        '\n/*]]>*/')
        return ''

    def _set_charset(self, mime):
        from email.charset import Charset, QP, BASE64, SHORTEST

        encoding = self.config.get('notification', 'mime_encoding').lower()
        charset = Charset()
        charset.input_charset = 'utf-8'
        charset.output_charset = 'utf-8'
        charset.input_codec = 'utf-8'
        charset.output_codec = 'utf-8'
        if encoding == 'base64':
            charset.header_encoding = BASE64
            charset.body_encoding = BASE64
        elif encoding in ('qp', 'quoted-printable'):
            charset.header_encoding = QP
            charset.body_encoding = QP
        elif encoding == 'none':
            charset.header_encoding = SHORTEST
            charset.body_encoding = None

        del mime['Content-Transfer-Encoding']
        mime.set_charset(charset)


if not INotificationFormatter:

    class HtmlNotificationSmtpEmailSender(SmtpEmailSender):

        def send(self, from_addr, recipients, message):
            mod = HtmlNotificationModule(self.env)
            message = mod.substitute_message(message)
            SmtpEmailSender.send(self, from_addr, recipients, message)


    class HtmlNotificationSendmailEmailSender(SendmailEmailSender):

        def send(self, from_addr, recipients, message):
            mod = HtmlNotificationModule(self.env)
            message = mod.substitute_message(message)
            SendmailEmailSender.send(self, from_addr, recipients, message)
