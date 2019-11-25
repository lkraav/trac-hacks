# -*- coding: utf-8 -*-

import unittest

from trac.core import Component, implements
from trac.test import EnvironmentStub, MockRequest
from trac.ticket.model import Ticket
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import to_utimestamp
from trac.web.api import ITemplateStreamFilter, RequestDone
try:
    from trac.notification.api import IEmailSender, NotificationSystem
except ImportError:
    from trac.notification import IEmailSender, NotificationSystem

from trachtmlnotification.notification import (
    HtmlNotificationModule, INotificationFormatter, tag)


class FilterStreamComponent(Component):

    implements(ITemplateStreamFilter)

    def filter_stream(self, req, method, filename, stream, data):
        req.method
        req.path_info
        req.query_string
        def filter(stream, ctxt=None):
            for event in stream:
                yield event
            for event in tag.script('// BLAH-BLAH-BLAH'):
                yield event
        return stream | filter


class EmailSenderStub(Component):

    implements(IEmailSender)

    history = None

    def __init__(self):
        self.history = []

    def send(self, from_addr, recipients, message):
        if not INotificationFormatter:
            mod = HtmlNotificationModule(self.env)
            message = mod.substitute_message(message)
        self.history.append((from_addr, recipients, message))


class NormalTestCase(unittest.TestCase):

    users = [('joe', 'Joe User', 'joe@example.org')]

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'trachtmlnotification.*',
                                           EmailSenderStub])
        self.config = self.env.config
        section = self.config['notification']
        section.set('smtp_enabled', 'enabled')
        section.set('mime_encoding', 'none')
        section.set('email_sender', 'EmailSenderStub')
        if hasattr(NotificationSystem, 'subscribers'):
            section = self.config['notification-subscriber']
            section.set('s', 'TicketReporterSubscriber')
            section.set('s.priority', '1')
            section.set('s.adverb', 'always')
            section.set('s.format', 'text/html')
        else:
            section.set('always_notify_reporter', 'enabled')
        users = [('joe', 'Joe User', 'joe@example.org')]
        if hasattr(self.env, 'insert_users'):
            self.env.insert_users(self.users)
        else:
            self.env.known_users = users
        self.mod = HtmlNotificationModule(self.env)
        self.tktmod = TicketModule(self.env)
        self.sender = EmailSenderStub(self.env)

    def tearDown(self):
        self.env.reset_db()

    def _create_ticket(self, **kwargs):
        args = dict(('field_' + name, value)
                     for name, value in kwargs.iteritems())
        req = MockRequest(self.env, method='POST', authname=kwargs['reporter'],
                          path_info='/newticket', args=args)
        self.assertEqual(True, self.tktmod.match_request(req))
        try:
            self.tktmod.process_request(req)
            self.fail('RequestDone not raised')
        except RequestDone:
            pass

    def _comment_ticket(self, id_, author, comment):
        ticket = Ticket(self.env, id_)
        changetime = str(to_utimestamp(ticket['changetime']))
        req = MockRequest(self.env, method='POST', authname=author,
                          path_info='/ticket/%d' % id_,
                          args={'action': 'leave', 'submit': '*',
                                'comment': comment, 'start_time': changetime,
                                'view_time': changetime})
        self.assertEqual(True, self.tktmod.match_request(req))
        try:
            self.tktmod.process_request(req)
            self.fail('RequestDone not raised')
        except RequestDone:
            pass

    def test_ticket_notification(self):
        self._create_ticket(status='new', summary='Blah blah blah',
                            reporter='joe',
                            description='<<<Description>>>\r\n')
        from_addr, recipients, message = self.sender.history[-1]
        self.assertIn('\nContent-Type: text/html;', message)
        self.assertIn('&lt;&lt;&lt;Description&gt;&gt;&gt;', message)
        self._comment_ticket(1, 'joe', '`>>>first comment<<<`')
        from_addr, recipients, message = self.sender.history[-1]
        self.assertIn('\nContent-Type: text/html;', message)
        self.assertIn('&lt;&lt;&lt;Description&gt;&gt;&gt;', message)
        self.assertIn('&gt;&gt;&gt;first comment&lt;&lt;&lt;', message)
        self._comment_ticket(1, 'joe', '`>>>second comment<<<`')
        from_addr, recipients, message = self.sender.history[-1]
        self.assertIn('\nContent-Type: text/html;', message)
        self.assertIn('&lt;&lt;&lt;Description&gt;&gt;&gt;', message)
        self.assertIn('&gt;&gt;&gt;second comment&lt;&lt;&lt;', message)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NormalTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
