#-*- coding: utf-8 -*-
#
# Copyright (C) 2007 Ole Trenner, <ole@jayotee.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from trac.web.chrome import Chrome

from genshi.template import NewTextTemplate, TemplateLoader

from announcer.api import AnnouncementSystem, AnnouncementEvent
from announcer.api import IAnnouncementFormatter, IAnnouncementSubscriber
from announcer.api import IAnnouncementPreferenceProvider
from announcer.distributors.mail import IAnnouncementEmailDecorator
from announcer.util.mail import set_header, next_decorator

from acct_mgr.api import IAccountChangeListener

class AccountChangeEvent(AnnouncementEvent):
    def __init__(self, category, username, password=None, token=None):
        AnnouncementEvent.__init__(self, 'acct_mgr', category, None)
        self.username = username
        self.password = password
        self.token = token

class AccountManagerAnnouncement(Component):
    """Send announcements on account changes."""

    implements(
        IAccountChangeListener,
        IAnnouncementSubscriber, 
        IAnnouncementFormatter,
        IAnnouncementEmailDecorator,
        IAnnouncementPreferenceProvider
    )

    # IAccountChangeListener interface
    def user_created(self, username, password):
        self._notify('created', username, password)

    def user_password_changed(self, username, password):
        self._notify('change', username, password)

    def user_deleted(self, username):
        self._notify('delete', username)

    def user_password_reset(self, username, email, password):
        self._notify('reset', username, password)

    def user_email_verification_requested(self, username, token):
        self._notify('verify', username, token=token)

    # IAnnouncementSubscriber interface
    def subscriptions(self, event):
        if event.realm == 'acct_mgr':
            for subscriber in self._get_membership(event):
                self.log.debug("AccountManagerAnnouncement added '%s " \
                        "(%s)'", subscriber[1], subscriber[2])
                yield subscriber

    # IAnnouncementFormatter interface
    def styles(self, transport, realm):
        if realm == 'acct_mgr':
            yield 'text/plain'

    def alternative_style_for(self, transport, realm, style):
        if realm == 'acct_mgr' and style != 'text/plain':
            return 'text/plain'

    def format(self, transport, realm, style, event):
        if realm == 'acct_mgr' and style == 'text/plain':
            return self._format_plaintext(event)

    # IAnnouncementEmailDecorator
    def decorate_message(self, event, message, decorates=None):
        if event.realm == "acct_mgr":
            prjname = self.env.project_name
            subject = '[%s] %s: %s' % (prjname, event.category, event.username)
            set_header(message, 'Subject', subject) 
        return next_decorator(event, message, decorates)

    # IAnnouncementPreferenceProvider interface
    def get_announcement_preference_boxes(self, req):
        if req.authname == "anonymous" and 'email' not in req.session:
            return
        yield "acct_mgr_subscription", "Account Manager Subscription"

    def render_announcement_preference_box(self, req, panel):
        if req.method == "POST":
            for category in ('created', 'change', 'delete'):
                if req.args.get('acct_mgr_%s_subscription'%category, None):
                    req.session['announcer_notify_acct_mgr_%s'%category] = '1'
                else:
                    if 'announcer_notify_acct_mgr_%s'%category in req.session:
                       del req.session['announcer_notify_acct_mgr_%s'%category]
        data = {}
        for category in ('created', 'change', 'delete'):
            data[category] = \
                req.session.get('announcer_notify_acct_mgr_%s'%category, None)
        return "prefs_announcer_acct_mgr_subscription.html", dict(**data)

    # private methods
    def _notify(self, category, username, password=None, token=None):
        try:
            announcer = AnnouncementSystem(self.env)
            announcer.send(
                AccountChangeEvent(category, username, password, token)
            )
        except Exception, e:
            self.log.exception("Failure creating announcement for account "
                               "event %s: %s", username, category)

    def _get_membership(self, event):
        if event.category in ('created', 'change', 'delete'):
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("""
                SELECT sid, authenticated
                  FROM session_attribute
                 WHERE name='announcer_notify_acct_mgr_%s'
            """%event.category)
            for result in cursor.fetchall():
                if result[1] in (1, '1', True):
                    authenticated = True
                else:
                    authenticated = False
                yield ('email', result[0], authenticated, None)
        elif event.category in ('verify', 'reset'):
            yield ('email', event.username, True, None)

    def _format_plaintext(self, event):
        acct_templates = {
            'created': 'acct_mgr_user_change_plaintext.txt', 
            'change': 'acct_mgr_user_change_plaintext.txt', 
            'delete': 'acct_mgr_user_change_plaintext.txt', 
            'reset': 'acct_mgr_reset_password_plaintext.txt', 
            'verify': 'acct_mgr_verify_plaintext.txt'
        }
        data = {
            'account': {
                'action': event.category,
                'username': event.username,
                'password': event.password,
                'token': event.token
            },
            'project': {
                'name': self.env.project_name,
                'url': self.env.abs_href(),
                'descr': self.env.project_description
            },
            'login': {
                'link': self.env.abs_href.login()
            }
        }
        if event.category == 'verify':
            data['verify'] = {
                'link': self.env.abs_href.verify_email(token=event.token)
            }
        chrome = Chrome(self.env)
        dirs = []
        for provider in chrome.template_providers:
            dirs += provider.get_templates_dirs()
        templates = TemplateLoader(dirs, variable_lookup='lenient')
        template = templates.load(acct_templates[event.category], 
                cls=NewTextTemplate)
        if template:
            stream = template.generate(**data)
            output = stream.render('text')
        return output
