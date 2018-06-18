# -*- coding: utf-8 -*-
#
#            Copyright (C) 2009 Massive Trac Provider Project
#
#                         All rights reserved.
#
########################################################################
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. The name of the author may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at: https://trac-hacks.org/log/contactformplugin
#
# Author: Sebastian Krysmanski
#

import re

from trac.admin.api import IAdminPanelProvider
from trac.config import Option, ListOption
from trac.core import Component, implements
from trac.notification import NotifyEmail
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider, add_notice, add_warning)
from trac.util.html import html as tag
from trac.util.translation import _
from trac.web.api import IRequestHandler


class ContactFormPlugin(Component):
    """ This component provides the contact form. """

    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    recipients = ListOption(
        'contactform', 'recipients',
        doc="Recipients for the contact form.")

    intro_text = Option(
        'contactform', 'intro_text', '',
        "Introductory text to use in the email.")

    _FIELD_NAMES = {
        'name': 'Your Name',
        'email': 'Your Email',
        'subject': 'Subject',
        'message': 'Message'
    }

    _SUBJECT_PREFIX = '[TracContact] '

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'contact'

    def get_navigation_items(self, req):
        yield 'mainnav', 'contact', tag.a('Contact', href=req.href.contact())

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/contact(?:\?.*)?$', req.path_info)

    def process_request(self, req):
        data = {}

        if req.method == 'POST':
            error_msg = None
            for field in ('name', 'email', 'subject', 'message'):
                value = req.args.get(field).strip()
                if len(value) == 0:
                    error_msg = 'You must fill in the field "' + \
                        self._FIELD_NAMES[field] + '".'
                    break

                if field == 'email' and \
                        not re.match(r'^[^@]+@.+\.[a-zA-Z]{2,}$', value):
                    error_msg = 'The email address you provided is invalid.'
                    self.log.info("Invalid email address encountered: %s",
                                  value)
                    break

            if error_msg:
                # Place the previous entered information again in the
                # fields. This is necessary when an error occured so
                # that the user doesn't have to enter it all again.
                add_warning(req, error_msg)
                data = req.args
            else:
                notify = ContactNotifyEmail(
                    self.env, req.args.get('name').strip(),
                    req.args.get('email').strip(),
                    self._SUBJECT_PREFIX + req.args.get('subject').strip(),
                    req.args.get('message').strip())
                try:
                    notify.notify()
                except Exception, e:
                    add_warning(req, "Your email could not be sent due to an "
                                     "internal error.")
                    data = req.args
                    self.log.error(
                        "Failure sending mail from '%s'. Subject: '%s'. "
                        "Message: '%s'\nException: ", req.args.get('email'),
                        req.args.get('subject'), req.args.get('message'), e)
                else:
                    add_notice(req, "Your email has been sent.")

        if not ContactAdminPanel.check_config(req, self.env):
            data['sendbutton_attr'] = {'disabled': 'disabled'}

        data['intro_text'] = self.intro_text

        return 'contactform.html', data, None

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []


class ContactAdminPanel(Component):
    """This component provides the admin panel for configuring the
    contact form.
    """

    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield 'general', _('General'), 'contact', _('Contact Form')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TRAC_ADMIN')

        self.check_config(req, self.env)

        if req.method == 'POST':
            contactform = self.config['contactform']
            contactform.set('recipients', req.args.get('recipients'))
            contactform.set('intro_text', req.args.get('intro_text'))
            self.config.save()
            req.redirect(req.href.admin(cat, page))

        data = {
            'recipients': self.config.get('contactform', 'recipients'),
            'intro_text': self.config.get('contactform', 'intro_text'),
        }
        return 'admin_contactform.html', data

    @classmethod
    def check_config(cls, req, env):
        config = env.config
        if not config.getbool('notification', 'smtp_enabled'):
            add_warning(req, 'Email notification is currently disabled '
                             '(because of "notification.smtp_enabled = false" '
                             'in "trac.ini").')
            return False

        if not get_contact_recipients(env):
            add_warning(req, "Email notification is currently disabled "
                             "(because no recipients has been specified "
                             "or no mail addresses are available for these "
                             "recipients).")
            return False

        return True


class ContactNotifyEmail(NotifyEmail):

    template_name = 'contact_email.txt'

    def __init__(self, env, from_name, from_mail, subject, message):
        super(ContactNotifyEmail, self).__init__(env)
        self._from_name = from_name
        self._from_mail = from_mail
        self._subject = subject
        self._message = message

    def notify(self):
        self.data.update({'message': self._message})
        super(ContactNotifyEmail, self).notify(None, self._subject)

    def get_recipients(self, resid):
        return get_contact_recipients(self.env), []

    def send(self, torcpts, ccrcpts, hdrs={}):
        # Override fields set in "NotifyEmail.notify"
        self.from_email = self._from_mail
        self.replyto_email = self._from_mail
        self.from_name = self._from_name

        super(ContactNotifyEmail, self).send(torcpts, ccrcpts, hdrs)


def get_contact_recipients(env):
    recipients = env.config.getlist('contactform', 'recipients')
    addresses = []

    # Retrieve mail addresses for known users
    user_mail_addresses = dict((user_data[0], user_data[2])
                               for user_data in env.get_known_users()
                               if user_data[2])

    for recipient in recipients:
        if recipient in user_mail_addresses:
            addresses.append(user_mail_addresses[recipient])
        elif recipient.find('@') != -1:
            addresses.append(recipient)

    return addresses
