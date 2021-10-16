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

#------------------------------------------------------
#    Internationalization
#------------------------------------------------------

try:
    from trac.util.translation import domain_functions
    _, ngettext, tag_, tagn_, gettext, N_, add_domain = \
        domain_functions('themeengine', ('_', 'ngettext', 'tag_', 'tagn_',
                                         'gettext', 'N_', 'add_domain'))
    dgettext = None
except ImportError:
    from genshi.builder  import tag as tag_
    from trac.util.translation  import gettext
    _ = gettext
    N_ = lambda text: text
    def add_domain(a,b,c=None):
        pass
    def dgettext(domain, string, **kwargs):
        return safefmt(string, kwargs)
    def ngettext(singular, plural, num, **kwargs):
        string = num == 1 and singular or plural
        kwargs.setdefault('num', num)
        return safefmt(string, kwargs)
    def safefmt(string, kwargs):
        if kwargs:
            try:
                return string % kwargs
            except KeyError:
                pass
        return string


if parse_version(trac_version) >= parse_version('1.0'):
    I18N_DOC_OPTIONS = dict(doc_domain='themeengine')
else:
    I18N_DOC_OPTIONS = {}
