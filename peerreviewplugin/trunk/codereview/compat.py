# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#

try:
    dict.iteritems
except AttributeError:
    # Python 3
    def itervalues(d):
        return iter(d.values())
    def iteritems(d):
        return iter(d.items())
    is_py3 = True
else:
    # Python 2
    is_py3 = False
    def itervalues(d):
        return d.itervalues()
    def iteritems(d):
        return d.iteritems()
