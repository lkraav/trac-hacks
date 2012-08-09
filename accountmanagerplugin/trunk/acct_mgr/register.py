# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2010-2012 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Matthew Good <trac@matt-good.net>

import re
import time

from genshi.core import Markup
from genshi.builder import tag
from trac import perm, util
from trac.core import Component, TracError, implements
from trac.config import Configuration, BoolOption, IntOption, Option, \
                        OrderedExtensionsOption
from trac.env import open_environment
from trac.web import auth, chrome
from trac.web.main import IRequestHandler, IRequestFilter

from acct_mgr.api import AccountManager, CommonTemplateProvider, \
                         _, dgettext, ngettext, tag_
from acct_mgr.model import email_associated, set_user_attribute
from acct_mgr.util import containsAny, if_enabled, is_enabled


def _create_user(req, env, check_permissions=True):
    acctmgr = AccountManager(env)
    username = acctmgr.handle_username_casing(req.args.get('username').strip())
    name = req.args.get('name').strip()
    email = req.args.get('email').strip()
    account = {
        'username': username,
        'name': name,
        'email': email,
    }
    error = TracError('')
    error.account = account

    if not username:
        error.message = _("Username cannot be empty.")
        raise error

    # Prohibit some user names that are important for Trac and therefor
    # reserved, even if they're not in the permission store for some reason.
    if username.lower() in ['anonymous', 'authenticated']:
        error.message = Markup(_("Username %s is not allowed.")
                               % tag.b(username))
        raise error

    # NOTE: A user may exist in the password store but not in the permission
    #   store. I.e. this happens, when the user (from the password store)
    #   never logged in into Trac. So we have to perform this test here
    #   and cannot just check for the user being in the permission store.
    #   And obfuscate whether an existing user or group name
    #   was responsible for rejection of this user name.
    for store_user in acctmgr.get_users():
        # Do it carefully by disregarding case.
        if store_user.lower() == username.lower():
            error.message = Markup(_("""
                Another account or group already exists, who's name
                differs from %s only by case or is identical.
                """) % tag.b(username))
            raise error

    # Check whether there is also a user or a group with that name.
    if check_permissions:
        # NOTE: We can't use 'get_user_permissions(username)' here
        #   as this always returns a list - even if the user doesn't exist.
        #   In this case the permissions of "anonymous" are returned.
        #
        #   Also note that we can't simply compare the result of
        #   'get_user_permissions(username)' to some known set of permission,
        #   i.e. "get_user_permissions('authenticated') as this is always
        #   false when 'username' is the name of an existing permission group.
        #
        #   And again obfuscate whether an existing user or group name
        #   was responsible for rejection of this username.
        for (perm_user, perm_action) in \
                perm.PermissionSystem(env).get_all_permissions():
            if perm_user.lower() == username.lower():
                error.message = Markup(_("""
                    Another account or group already exists, who's name
                    differs from %s only by case or is identical.
                    """) % tag.b(username))
                raise error

    # Always exclude some special characters, i.e. 
    #   ':' can't be used in HtPasswdStore
    #   '[' and ']' can't be used in SvnServePasswordStore
    blacklist = acctmgr.username_char_blacklist
    if containsAny(username, blacklist):
        pretty_blacklist = ''
        for c in blacklist:
            if pretty_blacklist == '':
                pretty_blacklist = tag(' \'', tag.b(c), '\'')
            else:
                pretty_blacklist = tag(pretty_blacklist,
                                       ', \'', tag.b(c), '\'')
        error.message = tag(_(
            "The username must not contain any of these characters:"),
            pretty_blacklist)
        raise error

    # Validation of username passed.

    password = req.args.get('password')
    if not password:
        error.message = _("Password cannot be empty.")
        raise error

    if password != req.args.get('password_confirm'):
        error.message = _("The passwords must match.")
        raise error

    # Validation of password passed.

    if if_enabled(EmailVerificationModule) and acctmgr.verify_email:
        if not email:
            error.message = _("You must specify a valid email address.")
            raise error
        elif not re.match('^[A-Z0-9._%+-]+@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$',
                          email, re.IGNORECASE):
            error.message = _("""The email address specified appears to be
                              invalid. Please specify a valid email address.
                              """)
            raise error
        elif email_associated(env, email):
            error.message = _("""The email address specified is already in
                              use. Please specify a different one.
                              """)
            raise error

    # Validation of email address passed.

    acctmgr.set_password(username, password)

    # INSERT new sid, needed as foreign key in some db schemata later on,
    # at least for PostgreSQL.
    db = env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute("""
        SELECT  COUNT(*)
        FROM    session
        WHERE   sid=%s
        """, (username,))
    exists = cursor.fetchone()
    if not exists[0]:
        cursor.execute("""
            INSERT INTO session
                    (sid,authenticated,last_visit)
            VALUES  (%s,1,0)
            """, (username,))

    for attribute in ('name', 'email'):
        value = req.args.get(attribute)
        if not value:
            continue
        set_user_attribute(env, username, attribute, value)


class RegistrationModule(CommonTemplateProvider):
    """Provides users the ability to register a new account.

    Requires configuration of the AccountManager module in trac.ini.
    """

    implements(chrome.INavigationContributor, IRequestHandler)

    def __init__(self):
        self.acctmgr = AccountManager(self.env)
        self._enable_check(log=True)

    def _enable_check(self, log=False):
        env = self.env
        writable = self.acctmgr.supports('set_password')
        ignore_case = auth.LoginModule(env).ignore_case
        if log:
            if not writable:
                self.log.warn('RegistrationModule is disabled because the '
                              'password store does not support writing.')
            if ignore_case:
                self.log.debug('RegistrationModule will allow lowercase '
                               'usernames only and convert them forcefully '
                               'as required, while \'ignore_auth_case\' is '
                               'enabled in [trac] section of your trac.ini.')
        return is_enabled(env, self.__class__) and writable

    enabled = property(_enable_check)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'register'

    def get_navigation_items(self, req):
        if not self.enabled:
            return
        if req.authname == 'anonymous':
            yield 'metanav', 'register', tag.a(_("Register"),
                                               href=req.href.register())

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/register' and self._enable_check(log=True)

    def process_request(self, req):
        if req.authname != 'anonymous':
            req.redirect(req.href.prefs('account'))
        action = req.args.get('action')
        data = {
            '_dgettext': dgettext,
            'acctmgr': {
                'username': None,
                'name': None,
                'email': None,
            },
            'ignore_auth_case': self.config.getbool('trac', 'ignore_auth_case')
        }
        verify_enabled = is_enabled(self.env, EmailVerificationModule) and \
                         self.acctmgr.verify_email
        data['verify_account_enabled'] = verify_enabled
        if req.method == 'POST' and action == 'create':
            try:
                _create_user(req, self.env)
            except TracError, e:
                data['registration_error'] = e.message
                data['acctmgr'].update(getattr(e, 'account', ''))
            else:
                if verify_enabled:
                    chrome.add_notice(req, Markup(tag.span(Markup(_(
                        """Your username has been successfully registered but
                        your account still requires activation. Please login
                        as user %(user)s, and follow the instructions.
                        """, user=tag.b(req.args.get('username')))))))
                    req.redirect(req.href.login())
                chrome.add_notice(req, Markup(tag.span(Markup(_(
                     """Registration has been finished successfully.
                     You may log in as user %(user)s now.""",
                     user=tag.b(req.args.get('username')))))))
                req.redirect(req.href.login())
        from acct_mgr.web_ui import AccountModule
        data['reset_password_enabled'] = AccountModule(self.env
                                                      ).reset_password_enabled
        return 'register.html', data, None


class EmailVerificationModule(CommonTemplateProvider):
    """Performs email verification on every new or changed address.

    A working email sender for Trac (!TracNotification or !TracAnnouncer)
    is strictly required to enable this module's functionality.

    Anonymous users should register and perms should be tweaked, so that
    anonymous users can't edit wiki pages and change or create tickets.
    So this email verification code won't be used on them. 
    """

    implements(IRequestFilter, IRequestHandler)

    def __init__(self, *args, **kwargs):
        self.email_enabled = True
        if self.config.getbool('announcer', 'email_enabled') != True and \
                self.config.getbool('notification', 'smtp_enabled') != True:
            self.email_enabled = False
            if is_enabled(self.env, self.__class__) == True:
                self.env.log.warn(self.__class__.__name__ + \
                    ' can\'t work because of missing email setup.')

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if not req.session.authenticated:
            # Permissions for anonymous users remain unchanged.
            return handler
        if AccountManager(self.env).verify_email and handler is not self and \
                'email_verification_token' in req.session and \
                not req.perm.has_permission('ACCTMGR_ADMIN'):
            # TRANSLATOR: Your permissions have been limited until you ...
            link = tag.a(_("verify your email address"),
                         href=req.href.verify_email())
            # TRANSLATOR: ... verify your email address
            chrome.add_warning(req, Markup(tag.span(Markup(_(
                "Your permissions have been limited until you %(link)s.",
                link=link)))))
            req.perm = perm.PermissionCache(self.env, 'anonymous')
        return handler

    def post_process_request(self, req, template, data, content_type):
        if not req.session.authenticated:
            # Don't start the email verification precedure on anonymous users.
            return template, data, content_type

        email = req.session.get('email')
        # Only send verification if the user entered an email address.
        acctmgr = AccountManager(self.env)
        if acctmgr.verify_email and self.email_enabled is True and email and \
                email != req.session.get('email_verification_sent_to') and \
                not req.perm.has_permission('ACCTMGR_ADMIN'):
            req.session['email_verification_token'] = self._gen_token()
            req.session['email_verification_sent_to'] = email
            acctmgr._notify(
                'email_verification_requested', 
                req.authname, 
                req.session['email_verification_token']
            )
            # TRANSLATOR: An email has been sent to %(email)s
            # with a token to ... (the link label for following message)
            link = tag.a(_("verify your new email address"),
                         href=req.href.verify_email())
            # TRANSLATOR: ... verify your new email address
            chrome.add_notice(req, Markup(tag.span(Markup(_(
                """An email has been sent to %(email)s with a token to
                %(link)s.""",
                email=email, link=link)))))
        return template, data, content_type

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/verify_email'

    def process_request(self, req):
        if not req.session.authenticated:
            chrome.add_warning(req, Markup(tag.span(tag_(
                "Please log in to finish email verification procedure."))))
            req.redirect(req.href.login())
        if 'email_verification_token' not in req.session:
            chrome.add_notice(req, _("Your email is already verified."))
        elif req.method == 'POST' and 'resend' in req.args:
            AccountManager(self.env)._notify(
                'email_verification_requested', 
                req.authname, 
                req.session['email_verification_token']
            )
            chrome.add_notice(req,
                    _("A notification email has been resent to <%s>."),
                    req.session.get('email'))
        elif 'verify' in req.args:
            # allow via POST or GET (the latter for email links)
            if req.args['token'] == req.session['email_verification_token']:
                del req.session['email_verification_token']
                chrome.add_notice(
                    req, _("Thank you for verifying your email address."))
                req.redirect(req.href.prefs())
            else:
                chrome.add_warning(req, _("Invalid verification token"))
        data = {'_dgettext': dgettext}
        if 'token' in req.args:
            data['token'] = req.args['token']
        if 'email_verification_token' not in req.session:
            data['button_state'] = { 'disabled': 'disabled' }
        return 'verify_email.html', data, None

    def _gen_token(self):
        return base64.urlsafe_b64encode(urandom(6))