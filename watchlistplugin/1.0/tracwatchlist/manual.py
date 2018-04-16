# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2010 by Martin Scharrer <martin@scharrer-online.de>
# All rights reserved.
#
# The i18n support was added by Steffen Hoffmann <hoff.st@web.de>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# For a copy of the GNU General Public License see
# <http://www.gnu.org/licenses/>.

import functools
import os
import pkg_resources

from trac.core import Component, implements
from trac.util.text import to_unicode
from trac.web.api import IRequestHandler, HTTPNotFound
from trac.web.chrome import web_context
from trac.wiki.formatter import format_to_html


class WatchlistManual(Component):
    implements(IRequestHandler)

    manuals = {}

    def __init__(self):
        dir_ = pkg_resources.resource_filename('tracwatchlist', 'manuals')
        for page in os.listdir(dir_):
            if page == '.svn':
                continue
            language = page.strip('.txt').replace('_', '-')
            filename = os.path.join(dir_, page)
            if os.path.isfile(filename):
                self.manuals[language] = filename

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith("/watchlist/manual")

    def process_request(self, req):
        path = req.path_info[len("/watchlist/manual"):].strip('/')
        if path.startswith('attachments'):
            return self.handle_attachment(req, path)

        language = path
        if not language:
            language = req.session.get('language', 'en-US')

        # Try to find a suitable language if no manual exists
        # in the requested one.
        if language not in self.manuals:
            # Try to find a main language,
            # e.g. 'xy' instead of 'xy-ZV'
            lang = language.split('-')[0]
            language = 'en-US'  # fallback if no other is found
            if lang in self.manuals:
                language = lang
            else:
                # Prefer 'en-US' before any other English dialect
                if lang == 'en' and 'en-US' in self.manuals:
                    language = 'en-US'
                else:
                    # If there is none try to find
                    # any other 'xy-*' language
                    lang += '-'
                    for lang in sorted(self.manuals.keys()):
                        if lang.startswith(lang):
                            language = lang
                            break
            req.redirect(req.href.watchlist('manual', language))

        try:
            with open(self.manuals[language]) as f:
                text = to_unicode(f.read())
        except Exception as e:
            raise HTTPNotFound(e)

        context = web_context(req)
        format_text = functools.partial(format_to_html, self.env, context)
        wldict = {
            'format_text': format_text,
            'text': text,
        }
        return "watchlist_manual.html", wldict, "text/html"

    def handle_attachment(self, req, path):
        path = path[len('attachments'):].strip('/')
        dir_ = pkg_resources.resource_filename('tracwatchlist',
                                               'manuals/attachments')
        filename = os.path.join(dir_, path)
        if os.path.isfile(filename):
            req.send_file(filename)
        else:
            raise HTTPNotFound(path)
