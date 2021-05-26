# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cinc-th
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
from trac.core import *
from trac.config import BoolOption
from trac.web.chrome import ITemplateStreamFilter, ITemplateProvider
from genshi.filters.transform import Transformer

from themeengine.api import ThemeBase


class BlueFlatTheme(ThemeBase):
    """A responsive, flat, blue theme using Bootstrap 3.3.1."""

    implements(ITemplateStreamFilter, ITemplateProvider)

    screenshot = True
    template = htdocs = True

    replace_jquery = BoolOption("blue-flat-theme", "replace_jquery", True, doc="Set to false if the theme plugin "
                                                                               "should not replace Tracs jQuery with "
                                                                               "the version shipping with the plugin "
                                                                               "(V1.11.2). Note that Bootstrap V3.3.1 "
                                                                               "needs jQuery >= V1.9.1")
    # ITemplateStreamFilter

    # Bootstrap needs a newer jQuery version than Trac ships. So replace the Trac jQuery with a more recent one
    def filter_stream(self, req, method, filename, stream, data):
        def repl_jquery(name, event):
            """ Replace Trac jquery.js with jquery.js coming with plugin. """
            attrs = event[1][1]
            if attrs.get(name):
                if attrs.get(name).endswith("common/js/jquery.js"):
                    return attrs.get(name) .replace("common/js/jquery.js", 'blueflat/js/jquery-1.11.2.min.js')
                elif attrs.get(name) and attrs.get(name).endswith("common/js/keyboard_nav.js"):
                    #keyboard_nav.js uses function live() which was removed with jQuery 1.9. Use a fixed script here
                    return attrs.get(name) .replace("common/js/keyboard_nav.js", 'blueflat/js/keyboard_nav.js')
            return attrs.get(name)

        if self.replace_jquery:
            stream = stream | Transformer('//head/script').attr('src', repl_jquery)
        return stream

    # ITemplateProvider methods

    def get_templates_dirs(self):
        """Return the path of the directory containing the provided templates."""
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('blueflat', resource_filename(__name__, 'htdocs'))]
