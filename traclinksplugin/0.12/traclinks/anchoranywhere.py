#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.


from genshi.core import QName
from genshi.filters.transform import Transformer, ENTER, OUTSIDE, EXIT
from genshi.path import Path
from pkg_resources import ResourceManager
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, ITemplateProvider, add_stylesheet
from urlparse import urlparse
import re


class AnchorAnywhere(Component):
    implements(ITemplateStreamFilter, ITemplateProvider)

    def filter_stream(self, req, method, filename, stream, data):
        add_script(req, 'traclinks/js/anchoranywhere.js')
        add_stylesheet(req, 'traclinks/css/anchoranywhere.css')
        if filename in ['browser.html', 'dir_entries.html']:
            pathinfo = req.base_path + req.path_info
            if req.get_header('x-requested-with') == 'XMLHttpRequest':
                referer = req.get_header('referer')
                pathinfo = referer and urlparse(referer)[2] or pathinfo
            trimmer = lambda x: re.match("(%s/)?([^?]+)(\?.*)?" % pathinfo, x).groups()[1]
            stream |= Transformer('//td[@class="name"]').apply(_AttrLaterTransformation('id', '//a', trimmer))
        return stream

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return [('traclinks', ResourceManager().resource_filename(__name__, 'htdocs'))]


class _AttrLaterTransformation(object):

    def __init__(self, name, pathfrom, trimmer=None):
        self.ispathfrom = Path(pathfrom).test()
        self.name = name
        self.trimmer = trimmer

    def __call__(self, stream):
        for mark, event in stream:
            if mark is OUTSIDE or mark is None:
                yield mark, event
                continue
            if mark is ENTER:
                queue = [(mark, event)]
                for mark, event in stream:
                    queue.append((mark, event))
                    if self.ispathfrom(event, {}, {}):
                        value = event[1][1].get('href')
                        if self.trimmer:
                            value = self.trimmer(value)
                    if mark is EXIT:
                        # append attr on start
                        # start.{mark, event:{kind, data:{name, attr}, pos} }}}
                        mark, (kind, data, pos) = queue[0]
                        attrs = data[1] | [(QName(self.name), value),
                                           (QName('onclick'), "javascript: document.location.hash = '%s'" % value)]
                        data = (data[0], attrs)
                        queue[0] = (mark, (kind, data, pos))
                        break
                for event in queue:
                    yield event
