# -*- coding: utf-8 -*-
#
# Copyright (c) 2013      Olemis Lang <olemis+trac@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Translation functions and classes."""

from trac import __version__ as trac_version
from trac.util.translation import domain_functions

trac_version = tuple(int(x) for x in trac_version.split() 
                            if x[0] in '0123456789')

#------------------------------------------------------
#    Internationalization
#------------------------------------------------------

_, ngettext, tag_, tagn_, gettext, N_, add_domain = \
   domain_functions('themeengine', ('_', 'ngettext', 'tag_', 'tagn_',
                                'gettext', 'N_', 'add_domain'))

I18N_DOC_OPTIONS = dict(doc_domain='themeengine') \
                       if trac_version[:2] >= (1, 0) else {}

