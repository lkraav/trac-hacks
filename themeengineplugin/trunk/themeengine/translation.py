# -*- coding: utf-8 -*-
#
# Copyright (c) 2013      Olemis Lang <olemis+trac@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Translation functions and classes."""

from pkg_resources import parse_version

from trac import __version__ as trac_version
from trac.util.translation import domain_functions

#------------------------------------------------------
#    Internationalization
#------------------------------------------------------

_, ngettext, tag_, tagn_, gettext, N_, add_domain = \
   domain_functions('themeengine', ('_', 'ngettext', 'tag_', 'tagn_',
                                'gettext', 'N_', 'add_domain'))

if parse_version(trac_version) >= parse_version('1.0'):
    I18N_DOC_OPTIONS = dict(doc_domain='themeengine')
else 
    I18N_DOC_OPTIONS = {}

