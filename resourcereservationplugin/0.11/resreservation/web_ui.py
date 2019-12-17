# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Roberto Longobardi
#

import re
import math
from trac.core import *
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet, add_script, add_ctxtnav
from genshi.builder import tag
from trac.util import to_unicode
from trac.util.text import CRLF
from trac.util.compat import sorted, set, any
from trac.resource import Resource
from trac.mimeview import Context
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage

from resreservation.api import ResourceReservationSystem
from resreservation.labels import *

class ResourceReservationTemplateProvider(Component):
    """Provides templates and static resources for the Resource Reservation plugin."""

    implements(ITemplateProvider)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('resreservation', resource_filename(__name__, 'htdocs'))]


class ResourceReservation(Component):
    """Implements the Resource Reservation tab."""

    implements(INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'resreservation'

    def get_navigation_items(self, req):
        yield ('mainnav', 'resreservation',
               tag.a(LABELS['main_tab_title'], href=req.href.wiki()+'/ResourceReservation', accesskey='M'))

