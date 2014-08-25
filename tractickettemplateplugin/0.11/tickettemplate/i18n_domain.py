# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

try:
    from trac.util.translation import domain_functions
    gettext, _, tag_, N_, add_domain = \
        domain_functions('tickettemplate', 'gettext', '_', 'tag_', 'N_',
                         'add_domain')
except ImportError:
    # ignore domain functions
    def add_domain(*args, **kwargs): pass
    try:
        from trac.util.translation import _, tag_, N_, gettext
    except ImportError:
        # skip support i18n, to work in trac 0.11
        def gettext(string, **kwargs): return string
        def _(string, **kwargs): return string
        def tag_(string, **kwargs): return string
        def N_(string, **kwargs): return string
