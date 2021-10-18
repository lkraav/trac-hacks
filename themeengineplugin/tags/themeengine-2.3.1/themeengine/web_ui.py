# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Noah Kantrowitz <noah@coderanger.net>
# Copyright (c) 2013      Olemis Lang <olemis+trac@gmail.com>
# Copyright (c) 2021      Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os.path
import sys

from pkg_resources import resource_filename

from trac.core import *
from trac.core import ComponentMeta
from trac.config import BoolOption
from trac.util.text import exception_to_unicode
from trac.web.chrome import add_script, add_stylesheet, add_warning, Chrome, \
                            ITemplateProvider
from trac.web.api import IRequestFilter

from themeengine.api import ThemeEngineSystem, ThemeNotFound
from themeengine.translation import I18N_DOC_OPTIONS


PY3 = sys.version_info.major == 3


class ThemeEngineModule(Component):
    """A module to provide the theme content."""

    custom_css = BoolOption('theme', 'enable_css', default='false',
                            doc='Enable or disable custom CSS from theme.',
                            **I18N_DOC_OPTIONS)

    implements(ITemplateProvider, IRequestFilter)

    def __init__(self):
        self.system = ThemeEngineSystem(self.env)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        try:
            theme = self.system.theme
            if theme and 'htdocs' in theme:
                theme_htdocs = theme['htdocs']
                if not os.path.isabs(theme_htdocs):
                    theme_htdocs = resource_filename(theme['module'], theme_htdocs)
                yield 'theme', theme_htdocs
        except ThemeNotFound:
            pass

    def get_templates_dirs(self):
        try:
            theme = self.system.theme
            if theme:
                if 'template' in theme:
                    theme_templates = os.path.dirname(theme['template'])
                    if not os.path.isabs(theme_templates):
                        theme_templates = resource_filename(theme['module'],
                                                            theme_templates)
                    yield theme_templates
                if 'jinja_template' in theme:
                    theme_templates = os.path.dirname(theme['jinja_template'])
                    if not os.path.isabs(theme_templates):
                        theme_templates = resource_filename(theme['module'],
                                                            theme_templates)
                    yield theme_templates

        except ThemeNotFound:
            pass

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if (template, data) != (None, None) or \
                sys.exc_info() != (None, None, None):
            try:
                theme = self.system.theme
            except ThemeNotFound as e:
                add_warning(req, "Unknown theme %s configured. Please check "
                        "your trac.ini. You may need to enable "
                        "the theme\'s plugin." % e.theme_name)
            else:
                if theme and 'css' in theme:
                    css = theme['css']
                    if isinstance(css, tuple) or isinstance(css, list):
                        for css_file in css:
                            add_stylesheet(req, 'theme/' + css_file)
                    else:
                        add_stylesheet(req, 'theme/' + theme['css'])
                if hasattr(Chrome, 'jenv'):
                    # Trac 1.4 supports Genshi and Jinja2 templates. content_type is 'None' in Trac 1.4
                    # when a Genshi template is being rendered.
                    # Trac 1.6 only supports Jinja2.
                    if content_type != None or (template, data) == (None, None):
                        # If an exception occurs, for example permission error, the content_type is always 'None'.
                        # So we need to handle exception pages here.
                        if theme and 'jinja_template' in theme:
                            req.chrome['theme'] = os.path.basename(theme['jinja_template'])
                    else:
                        # Legacy Genshi template rendering.
                        if theme and 'template' in theme:
                            req.chrome['theme'] = os.path.basename(theme['template'])
                else:
                    if theme and 'template' in theme:
                        req.chrome['theme'] = os.path.basename(theme['template'])
                if theme and 'scripts' in theme:
                    for script_def in theme['scripts']:
                        if (isinstance(script_def, tuple) and
                                1 <= len(script_def) <= 4):
                            temp = [item for item in script_def]
                            if not temp[0].startswith('theme'):
                                temp[0] = 'theme/' + temp[0].lstrip('/')
                            add_script(req, *temp)
                        else:
                            self.log.warning('Bad script def %s for theme %s. Is definition a tuple?',
                                             script_def, theme['name'])
                if theme and theme.get('disable_trac_css'):
                    links = req.chrome.get('links')
                    if links and 'stylesheet' in links:
                        for i, link in enumerate(links['stylesheet']):
                            if link.get('href', '') \
                                    .endswith('common/css/trac.css'):
                                del links['stylesheet'][i]
                                break
                if theme:
                    req.chrome['theme_info'] = theme
                    # Template overrides (since 2.2.0)
                    overrides = self._get_template_overrides(theme)
                    template, modifier = overrides.get(template,
                                                       (template, None))
                    if modifier is not None:
                        modifier(req, template, data, content_type)
            if self.custom_css:
                add_stylesheet(req, 'site/theme.css')

        return template, data, content_type

    # Protected methods
    def _get_template_overrides(self, theme):
        overrides = theme.get('template_overrides')
        if overrides is None:
            try:
                overrides = theme['provider'].get_template_overrides(
                                                    theme['name'])
            except Exception as e:
                overrides = {}
                self.log.warning('Theme %s template overrides : %s',
                                 theme['name'],
                                 exception_to_unicode(e))
            else:
                overrides = dict([old, (new, callback)]
                                 for old, new, callback in overrides)
            theme['template_overrides'] = overrides
        return overrides
