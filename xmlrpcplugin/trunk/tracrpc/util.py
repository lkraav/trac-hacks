# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009-2013 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import sys


# Supported Python versions:
PY24 = sys.version_info[:2] == (2, 4)
PY25 = sys.version_info[:2] == (2, 5)
PY26 = sys.version_info[:2] == (2, 6)
PY27 = sys.version_info[:2] == (2, 7)
PY3 = sys.version_info[0] > 2


if sys.version_info[0] == 2:
    unicode = unicode
    basestring = basestring
    unichr = unichr
    from itertools import izip
    import xmlrpclib
else:
    unicode = str
    basestring = str
    unichr = chr
    izip = zip
    from xmlrpc import client as xmlrpclib


def accepts_mimetype(req, mimetype):
    if isinstance(mimetype, basestring):
      mimetype = (mimetype,)
    accept = req.get_header('Accept')
    if accept is None :
        # Don't make judgements if no MIME type expected and method is GET
        return req.method == 'GET'
    else :
        accept = accept.split(',')
        return any(x.strip().startswith(y) for x in accept for y in mimetype)


def prepare_docs(text, indent=4):
    r"""Remove leading whitespace"""
    return text and ''.join(l[indent:] for l in text.splitlines(True)) or ''
