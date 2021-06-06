#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
from trac.util.translation import _
from themeengine.api import ThemeBase


class TracTwekTheme(ThemeBase):
    """A flat Trac theme using Tracs colors."""

    screenshot = False
    htdocs = True
    template = jinja_template = True

    # IThemeProvider methods

    def get_theme_names(self):
        yield "TracFlat"
        yield "TracSidebar"
        yield "TracFlatSidebar"

    def get_theme_info(self, name):
        """Return a dict containing 0 or more of the following pairs:

         description::
           A brief description of the theme.
         template::
           The name of the Genshi theme template file.
         jinja_template::
           The name of the Jinja2 theme template file.
         css::
           The filename of the CSS file.
         disable_trac_css::
           A boolean indicating if the core Trac CSS should be diabled.
         htdocs::
           The folder containg the static content.
         screenshot::
           The name of the screenshot file.
         colors::
           A list of (name, css-property, selector) tuples.
         schemes::
           A list of (name, {color-name: value, ...}) tuples.
         scripts::
           A list of (filename, mimetype, charset, ie_if) respectively for
           script (relative | absolute) URI (mandatory),
           script MIME type (optional , defaults to 'text/javascript'),
           script charset encoding (optional, defaults to 'utf-8'),
           and a bool flag for MSIE-only shims (optional, defaults to False)
           @since 2.2.2
        """
        if name == 'TracFlat':
            return {'description': _("A flat Trac theme using Tracs colors."),
                    'css': 'css/tracflattheme.css',
                    'htdocs': 'htdocs',
                    'disable_trac_css': True}
        elif name == "TracSidebar":
            return {'description': _("A theme using a sidebar for the main navigation menu."),
                    'css': 'css/tftsidebar.css',
                    'jinja_template': 'templates/theme_jinja.html',
                    'template': 'templates/genshi/theme_genshi.html',
                    'htdocs': 'htdocs',
                    'scripts': [('js/tftsidebar.js',)],
                    'disable_trac_css': False}
        elif name == "TracFlatSidebar":
            return {'description': _("A theme using a sidebar for the main navigation menu and flat elements."),
                    'css': ['css/tracflattheme.css', 'css/tftsidebar_flat.css'],
                    'jinja_template': 'templates/theme_jinja.html',
                    'template': 'templates/genshi/theme_genshi.html',
                    'htdocs': 'htdocs',
                    'scripts': [('theme/js/tftsidebar.js',)],
                    'disable_trac_css': True}
