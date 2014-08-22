# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Jun Omae
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
from pkg_resources import resource_filename

from genshi.builder import Fragment, tag

from trac import __version__ as VERSION
from trac.core import Component, TracError, implements
from trac.config import BoolOption, ChoiceOption
from trac.ticket.web_ui import TicketModule
from trac.util.compat import partial
from trac.util.text import obfuscate_email_address
from trac.web.api import IRequestFilter
from trac.web.chrome import Chrome, ITemplateProvider, add_script, \
                            add_stylesheet


class UsernameDecorateModule(Component):

    implements(IRequestFilter, ITemplateProvider)

    _label_styles = ('$fullname',
                     '$email',
                     '$username',
                     '$username ($fullname)',
                     '$username <$email>',
                     '$fullname <$email>',
                     '$username <$email> ($fullname)',
                     '$username ($fullname) <$email>')

    _title_styles = ('$username - $fullname <$email>',
                     '$username ($fullname) <$email>',
                     '$username <$email> ($fullname)',
                     '$fullname <$email>',
                     '$username <$email>',
                     '$username ($fullname)',
                     '$fullname',
                     '$email',
                     '$username')

    _style_alternates = {
        '$fullname <$email>': {
            'fullname': '$username <$email>',
            'email': '$fullname',
        },
        '$username <$email> ($fullname)': {
            'email': '$username ($fullname)',
            'fullname': '$username <$email>',
        },
        '$username ($fullname) <$email>': {
            'fullname': '$username <$email>',
            'email': '$username ($fullname)',
        },
        '$username - $fullname <$email>': {
            'fullname': '$username - <$email>',
            'email': '$username - $fullname',
        },
    }

    authorinfo_label = ChoiceOption(
        'usernamedecorate', 'authorinfo_label', _label_styles,
        doc="""\
Author information format to display instead of username in wiki, ticket
and timeline pages. The keywords will be expanded with the following.

 - `$username`   User name
 - `$fullname`   Full name
 - `$email`      Email address""")

    authorinfo_title = ChoiceOption(
        'usernamedecorate', 'authorinfo_title', _title_styles,
        doc="""\
Title attribute in author information in wiki, ticket and timeline
pages. The keywords will be expanded with the same as authorinfo_label
option.""")

    show_tooltips = BoolOption(
        'usernamedecorate', 'show_tooltips', 'enabled',
        doc="""Show the tooltips for author information.""")

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template:
            if self.show_tooltips:
                add_stylesheet(req, 'usernamedecorate/tipsy.css')
                add_script(req, 'usernamedecorate/jquery.tipsy.js')
                add_script(req, 'usernamedecorate/base.js')
            authorinfo = partial(self._authorinfo, req)
            data['authorinfo'] = authorinfo
            if template == 'ticket.html':
                self._set_ticketbox_links(req, data)
            elif template == 'timeline.html':
                data['format_author'] = authorinfo
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('usernamedecorate', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return ()

    # Internal methods

    def _set_ticketbox_links(self, req, data):
        ticket = data['ticket']
        chrome = Chrome(self.env)
        tktmod = TicketModule(self.env)
        for name in ('reporter', 'owner'):
            value = ticket[name]
            key = '%s_link' % name
            if isinstance(data.get(key), Fragment) and \
                    chrome.format_author(req, value) == value:
                label = self._authorinfo(req, value)
                data[key] = tktmod._query_link(req, name, value, label)

    def _authorinfo(self, req, author, email_map=None):
        try:
            users_cache = req._users_cache
        except AttributeError:
            req._users_cache = users_cache = self._get_users_cache()

        if author in users_cache:
            cache = users_cache[author]
            info = cache['info']
            if info is not None:
                return info
            args = cache['args']
        else:
            args = {'username': author}
            users_cache[author] = {'args': args, 'info': None}

        chrome = Chrome(self.env)
        label = chrome.format_author(req, author)
        if label != author:
            title = None
            class_ = 'trac-author-anonymous'
        else:
            email_view = chrome.show_email_addresses or \
                         'EMAIL_VIEW' in req.perm
            label = self._format_authorinfo(self.authorinfo_label, args,
                                            email_view)
            title = self._format_authorinfo(self.authorinfo_title, args,
                                            email_view)
            class_ = 'trac-author'
        info = tag.span(label, title=title, class_=class_)
        users_cache[author]['info'] = info
        return info

    def _get_users_cache(self):
        cache = {}
        for username, name, email in self.env.get_known_users():
            name = (name or '').strip()
            email = (email or '').strip()
            cache[username] = {'args': {'username': username, 'fullname': name,
                                        'email': email},
                               'info': None}
        return cache

    _format_authorinfo_re = re.compile(r'\$(?:\w+|\{\w+\})')

    def _format_authorinfo(self, fmt, args, email_view):
        def repl(match):
            key = match.group(0)[1:]
            if key.startswith('{'):
                key = key[1:-1]
            value = args[key]
            if not value:
                raise KeyError(key)
            if not email_view and key == 'email':
                value = obfuscate_email_address(value)
            return value

        while fmt:
            try:
                return self._format_authorinfo_re.sub(repl, fmt)
            except KeyError, e:
                alternates = self._style_alternates.get(fmt)
                if alternates:
                    fmt = alternates.get(e.args[0])
                else:
                    fmt = None
        return args['username']
