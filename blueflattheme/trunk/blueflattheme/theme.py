# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
from trac.core import *
from trac.web.chrome import ITemplateProvider

from themeengine.api import ThemeBase


class BlueFlatTheme(ThemeBase):
    """A responsive, flat, blue theme using Bootstrap 3.3.1."""

    implements(ITemplateProvider)

    screenshot = True
    template = htdocs = True
    jinja_template = True

    # ITemplateProvider methods

    def get_templates_dirs(self):
        """Return the path of the directory containing the provided templates."""
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('blueflat', resource_filename(__name__, 'htdocs'))]
