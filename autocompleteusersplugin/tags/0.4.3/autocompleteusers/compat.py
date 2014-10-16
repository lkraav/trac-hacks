# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Jeff Hammel <jhammel@openplans.org>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Tetsuya Morimoto <tetsuya.morimoto@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

"""
for Trac-0.11 compatibility.

Thanks to jun66j5 (http://trac-hacks.org/ticket/8477#comment:13),
I copied compatible code from as below.

http://trac-hacks.org/browser/tracdragdropplugin/0.11/tracdragdrop/web_ui.py
"""

import re

_jsquote_re = re.compile(r'[\010\f\n\r\t"><&\\]')
_jsquote_chars = {'\010': r'\b', '\f': r'\f', '\n': r'\n', '\r': r'\r',
                  '\t': r'\t', '"': r'\"', '\\': r'\\',
                  '&': r'\u0026', '>': r'\u003E', '<': r'\u003C'}


def _jsquote_repl(match):
    return _jsquote_chars[match.group(0)]


def to_json(value):
    """From 0.12-stable/trac/util/presentation.py"""
    if isinstance(value, basestring):
        return '"%s"' % _jsquote_re.sub(_jsquote_repl, value)
    elif value is None:
        return 'null'
    elif value is False:
        return 'false'
    elif value is True:
        return 'true'
    elif isinstance(value, (int, long)):
        return str(value)
    elif isinstance(value, float):
        return repr(value)
    elif isinstance(value, (list, tuple)):
        return '[%s]' % ','.join(to_json(each) for each in value)
    elif isinstance(value, dict):
        return '{%s}' % ','.join('%s:%s' % (to_json(k), to_json(v))
                                 for k, v in sorted(value.iteritems()))
    else:
        raise TypeError('Cannot encode type %s' % value.__class__.__name__)
