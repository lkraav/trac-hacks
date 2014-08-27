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
from genshi.core import Markup
from genshi.filters.transform import Transformer

from trac import __version__ as VERSION
from trac.core import Component, TracError, implements
from trac.config import BoolOption, ChoiceOption, IntOption
from trac.ticket.web_ui import TicketModule
from trac.util.compat import md5, partial
from trac.util.text import obfuscate_email_address
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import Chrome, ITemplateProvider, add_script, \
                            add_stylesheet


class UsernameDecorateModule(Component):

    implements(IRequestFilter, ITemplateProvider, ITemplateStreamFilter)

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
            if self.show_tooltips:
                add_stylesheet(req, 'usernamedecorate/tipsy.css')
                add_script(req, 'usernamedecorate/jquery.tipsy.js')
                add_script(req, 'usernamedecorate/base.js')
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

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if method != 'xhtml' or not self.show_gravatar_icon:
            return stream

        size = self.gravatar_icon_size
        if size < 1:
            size = 16
        if size == 16:
            return stream

        content = """\
/*<![CDATA[*/
.usernamedecorate-gravatar { padding-left: %(padding)dpx }
.usernamedecorate-gravatar > img { width: %(size)dpx; height: %(size)dpx }
/*]]>*/""" % {'padding': size + 1, 'size': size}
        def fn():
            return tag.style(Markup(content), type='text/css')
        return stream | Transformer('//head').append(fn)

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
        cache_key = author = (author or '').strip()
        if email_map and '@' in author and author in email_map:
            author = email_map[author]
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
