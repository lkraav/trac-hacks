# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Matthew Good <trac@matt-good.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Pedro Algarvio <ufs@ufsoft.org>

from __future__ import absolute_import

import threading

try:
    import aiosmtpd
except ImportError:
    import asyncore, smtpd
    aiosmtpd = None
else:
    import asyncio
    from aiosmtpd.controller import UnthreadedController
    from aiosmtpd.handlers import Message


class NonForgetingSMTPServerStore(object):
    """
    Non forgetting store for SMTP data.
    """
    # We override trac's implementation of a mailstore because if forgets
    # the last message when a new one arrives.
    # Account Manager at times sends more than one email and we need to be
    # able to test both

    def __init__(self):
        self.messages = {}
        self.last_message = {}

    @property
    def recipients(self):
        return self.last_message.get('recipients')

    @property
    def sender(self):
        return self.last_message.get('sender')

    @property
    def message(self):
        return self.last_message.get('message')

    def process_message(self, mailfrom, rcpttos, data, **kwargs):
        message = {'recipients': rcpttos, 'sender': mailfrom, 'message': data}
        self.messages.update((recipient, message) for recipient in rcpttos)
        self.last_message = message

    def full_reset(self):
        self.messages.clear()
        self.last_message.clear()


class SMTPThreadedServerMethods(object):
    """
    Run a SMTP server for a single connection, within a dedicated thread
    """
    host = 'localhost'

    def get_sender(self, recipient=None):
        """Return the sender of a message. If recipient is passed, return the
        sender for the message sent to that recipient, else, send the sender
        for last message"""
        try:
            return self.store.messages[recipient]['sender']
        except KeyError:
            return self.store.sender

    def get_recipients(self, recipient=None):
        """Return the recipients of a message. If recipient is passed, return
        the recipients for the message sent to that recipient, else, send
        recipients for last message"""
        try:
            return self.store.messages[recipient]['recipients']
        except KeyError:
            return self.store.recipients

    def get_message(self, recipient=None):
        """Return the message of a message. If recipient is passed, return the
        actual message for the message sent to that recipient, else, send the
        last message"""
        try:
            return self.store.messages[recipient]['message']
        except KeyError:
            return self.store.message

    def get_message_parts(self, recipient):
        """Return the message parts(dict). If recipient is passed, return the
        parts for the message sent to that recipient, else, send the parts for
        last message"""
        try:
            return self.store.messages[recipient]
        except KeyError:
            return None

    def full_reset(self):
        self.store.full_reset()


if aiosmtpd:
    class Handler(Message):

        store = None

        def __init__(self, store):
            self.store = store

        def handle_message(self, message):
            pass

        def prepare_message(self, session, envelope):
            content = envelope.content
            if content.endswith(b'\r\n'):
                content = content[:-2]
            data = content.decode('utf-8')
            mailfrom = envelope.mail_from
            recipients = envelope.rcpt_tos
            self.store.process_message(mailfrom, recipients, data)
            return None

    class Controller(UnthreadedController):

        def _create_server(self):
            return self.loop.create_server(
                self._factory_invoker, host=self.hostname, port=self.port,
                ssl=self.ssl_context, reuse_address=True)

    class SMTPThreadedServer(threading.Thread, SMTPThreadedServerMethods):

        def __init__(self, port):
            self.port = port
            self.store = NonForgetingSMTPServerStore()
            loop = asyncio.new_event_loop()
            handler = Handler(self.store)
            controller = Controller(handler, loop=loop, hostname=self.host,
                                    port=port)
            self.loop = loop
            self.controller = controller
            controller.begin()
            super().__init__(target=loop.run_forever)
            self.daemon = True

        def stop(self):
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
            while self.is_alive():
                self.join(0.1)
            self.controller.end()
            self.loop.close()

else:
    class SMTPServer(smtpd.SMTPServer):

        store = None

        def __init__(self, localaddr, store):
            smtpd.SMTPServer.__init__(self, localaddr, None)
            self.store = store

        def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
            self.store.process_message(mailfrom, rcpttos, data)

    class SMTPThreadedServer(threading.Thread, SMTPThreadedServerMethods):

        def __init__(self, port):
            self.port = port
            self.store = NonForgetingSMTPServerStore()
            super(SMTPThreadedServer, self).__init__(target=asyncore.loop,
                                                     args=(0.1, True))
            self.daemon = True

        def start(self):
            self.server = SMTPServer((self.host, self.port), self.store)
            super(SMTPThreadedServer, self).start()

        def stop(self):
            self.server.close()
            self.join()
