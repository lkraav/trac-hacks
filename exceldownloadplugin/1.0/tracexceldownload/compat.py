# -*- coding: utf-8 -*-

from decimal import Decimal
import inspect
import sys


__all__ = ('PY2', 'unicode', 'bytes', 'number_types', 'string_types', 'long',
           'unichr', 'xrange', 'iteritems', 'BytesIO', 'getargspec')


PY2 = sys.version_info[0] == 2

if PY2:
    unicode = unicode
    try:
        bytes = bytes
    except NameError:
        bytes = str
    number_types = (int, long, float, Decimal)
    string_types = basestring
    long = long
    unichr = unichr
    xrange = xrange
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
else:
    unicode = str
    bytes = bytes
    number_types = (int, float, Decimal)
    string_types = str
    long = int
    unichr = chr
    xrange = range
    itervalues = lambda d: d.values()
    iteritems = lambda d: d.items()

try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

if hasattr(inspect, 'getfullargspec'):
    getargspec = inspect.getfullargspec
else:
    getargspec = inspect.getargspec
