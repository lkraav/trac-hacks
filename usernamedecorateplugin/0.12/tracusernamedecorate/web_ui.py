# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Jun Omae
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.config import BoolOption, ChoiceOption, IntOption
from trac.ticket.web_ui import TicketModule
from trac.util.compat import md5, partial
from trac.util.text import obfuscate_email_address
from trac.web.api import IRequestFilter
from trac.web.chrome import Chrome, ITemplateProvider, add_script, \
                            add_script_data, add_stylesheet

try:
    from trac.util.html import Fragment, tag
except ImportError:
    from genshi.builder import Fragment, tag


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
        doc="""Show tooltips for the author information.""")

    show_gravatar_icon = BoolOption(
        'usernamedecorate', 'show_gravatar_icon', 'disabled',
        doc="""Show Gravatar icon for the author.""")

    gravatar_icon_size = IntOption(
        'usernamedecorate', 'gravatar_icon_size', '16',
        doc="""Size of Gravatar icon for the author.""")

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template and template.endswith('.html'):
            req.callbacks['_users_cache'] = self._get_users_cache
            show_tooltips = self.show_tooltips
            show_gravatar_icon = self.show_gravatar_icon
            if show_tooltips:
                add_stylesheet(req, 'usernamedecorate/tipsy.css')
                add_script(req, 'usernamedecorate/jquery.tipsy.js')
            if show_tooltips or show_gravatar_icon:
                add_script(req, 'usernamedecorate/base.js')
                script_data = {'show_tooltips': show_tooltips,
                               'show_gravatar_icon': show_gravatar_icon}
                gravatar_icon_size = self.gravatar_icon_size
                if gravatar_icon_size < 1:
                    gravatar_icon_size = 16
                if gravatar_icon_size != 16:
                    script_data['gravatar_icon_size'] = gravatar_icon_size
                add_script_data(req, {'tracusernamedecorate': script_data})
            add_stylesheet(req, 'usernamedecorate/base.css')
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
        for field in data.get('fields') or ():
            name = field['name']
            value = ticket[name] or ''
            if name == 'cc':
                rendered = tag()
                for idx, word in enumerate(re.split(r'([;,\s]+)', value)):
                    if idx % 2:
                        rendered(word)
                        continue
                    if not word:
                        continue
                    label = chrome.format_emails(req, word)
                    if label != word:
                        rendered(label)
                        continue
                    link = tktmod._query_link(req, name, '~' + word,
                                              self._authorinfo(req, word))
                    rendered(link)
                field['rendered'] = rendered
                continue

    def _authorinfo(self, req, author, email_map=None):
        cache_key = author = (author or '').strip()
        users_cache = req._users_cache
        if cache_key in users_cache:
            cache = users_cache[cache_key]
            info = cache.get('info')
            if info is not None:
                return info
            args = cache['args']
            known_user = True
        else:
            args = {'username': author}
            known_user = False
            users_cache[cache_key] = {'args': args}

        if email_map and '@' in author and author in email_map:
            author = email_map[author]
        chrome = Chrome(self.env)
        label = chrome.format_author(req, author)
        if not author or author == 'anonymous' or not known_user or \
                label != author:
            title = None
            class_ = 'usernamedecorate-anonymous'
        else:
            email_view = chrome.show_email_addresses or \
                         'EMAIL_VIEW' in req.perm
            label = self._format_authorinfo(self.authorinfo_label, args,
                                            email_view)
            title = self._format_authorinfo(self.authorinfo_title, args,
                                            email_view)
            email = args.get('email')
            if email and self.show_gravatar_icon:
                class_ = 'usernamedecorate usernamedecorate-gravatar'
                icon = self._get_gravatar_icon(md5(email.lower()).hexdigest(),
                                               self.gravatar_icon_size)
                label = tag(tag.img(src=icon), label)
            else:
                class_ = 'usernamedecorate'

        info = tag.span(label, title=title, class_=class_)
        users_cache[author]['info'] = info
        return info

    def _get_users_cache(self, req):
        cache = {}
        for username, name, email in self.env.get_known_users():
            name = (name or '').strip() or None
            email = (email or '').strip() or None
            args = {'username': username, 'fullname': name, 'email': email}
            cache[username] = {'args': args}
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

    def _get_gravatar_icon(self, hash, size):
        return '//secure.gravatar.com/avatar/%s?d=identicon&s=%d' % \
               (hash, size)
