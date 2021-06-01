# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] == 2:
    unicode = unicode
    long = long
    basestring = basestring
    reduce = reduce
    unichr = unichr
    xrange = xrange
    iteritems = lambda d: d.iteritems()
    _numtypes = (int, long, float)
else:
    unicode = str
    long = int
    basestring = str
    from functools import reduce
    unichr = chr
    xrange = range
    _numtypes = (int, float)
    iteritems = lambda d: d.items()
