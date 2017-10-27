# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Thomas Vander Stichele <thomas at apestaart dot org>
# Copyright (C) 2010-2017 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import (
    ITemplateProvider, add_script, add_script_data, add_stylesheet)


class TracKeywordsComponent(Component):
    """
    This component allows you to add from a configured list
    of keywords to the Keywords entry field.

    The list of keywords can be configured in a [keywords] section in the
    trac configuration file.  Syntax is:

        keyword = description

    The description will show up as a tooltip when you hover over the keyword.
    """

    implements(IRequestFilter, ITemplateProvider)

    def __init__(self):
        self.keywords = self._get_keywords()
        # Test availability of TagsPlugin and specifically it's wiki page
        # tagging support.
        try:
            from tractags.wiki import WikiTagInterface
        except ImportError:
            self.tagsplugin_enabled = False
        else:
            self.tagsplugin_enabled = self.env.is_enabled(WikiTagInterface)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ('ticket.html', 'wiki_edit.html'):
            add_script_data(req, trac_keywords=self.keywords)
            add_script(req, 'keywords/trac_keywords.js')
            add_stylesheet(req, 'keywords/trac_keywords.css')
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('keywords', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    def _get_keywords(self):
        keywords = []
        section = self.env.config['keywords']
        for keyword in section:
            keywords.append((keyword, section.get(keyword)))
        if not keywords:
            # return a default set of keywords to show the plug-in works
            keywords = [
                ('patch', 'has a patch attached'),
                ('easy', 'easy to fix, good for beginners'),
            ]
        return sorted(keywords)
