# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# ==============================================================================

__version__     = '0.1.3'
__author__      = 'Pedro Algarvio'
__email__       = 'ufs@ufsoft.org'
__packagename__ = 'TracGoogleSearch'
__license__     = 'BSD'
__url__         = 'http://google.ufsoft.org'
__summary__     = 'Google Adsense Search Plugin for Trac'

import pkg_resources
from trac.config import Option, BoolOption, IntOption
from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider

# ==============================================================================
# Google Search Config
# ==============================================================================
class GoogleSearchConfig(Component):
    google_search_active = BoolOption(
        'google.search', 'google_search_active', True,
        """Enable Google Adsense search."""
    )
    search_form_id = Option('google.search', 'search_form_id', 'search',
        """The form ID where the adsesnse for search code should be placed.

        The default is "search" which is trac's mini search form. Content will
        be replaced"""
    )
    search_form_text_input_width = IntOption(
        'google.search', 'search_form_text_input_width', 31,
        """
        Initial width(number of characters) of the search string text input.
        """
    )
    search_form_forid = Option('google.search', 'search_form_forid', '',
        """This is the value of the hidden input with the name "cof" that
        Google gives on their code, usualy something like "FORID:n" where n
        is an integer value. This cannot be empty."""
    )
    search_form_client_id = Option('google.search', 'search_form_client_id', '',
        """This is the value of the hidden input with the name "cx" that
        Google gives on their code, usualy something like
        "partner-pub-0000000000000000:0aaa0aaa00a" (this is just an example).
        This cannot be empty."""
    )
    search_iframe_initial_width = IntOption(
        'google.search', 'search_iframe_initial_width', 800,
        """
        Initial width of the IFRAME that Google returns. It will then increase
        the available width of the div by the ID "content".

        This value should not be that bigger because resizing only occurs
        correctly if initial size is smaller than the available width.
        """
    )

# ==============================================================================
# Google Search Resources
# ==============================================================================
class GoogleSearchResources(Component):
    implements(ITemplateProvider)
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        yield 'googlesearch', pkg_resources.resource_filename(__name__,
                                                              'htdocs')

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        yield pkg_resources.resource_filename(__name__, 'templates')
