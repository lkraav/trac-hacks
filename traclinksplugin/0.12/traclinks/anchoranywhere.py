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
from trac.core import Component, implements, ExtensionPoint
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, ITemplateProvider, add_stylesheet
from trac.wiki.api import IWikiSyntaxProvider
from urllib import quote, unquote
from urlparse import urlparse
import re


class AnchorAnywhere(Component):
    """ Put anchor in all paragraphs """
    implements(ITemplateStreamFilter, ITemplateProvider)

    syntax_providers = ExtensionPoint(IWikiSyntaxProvider)
    title = "Keywords for search, or \n"

    def __init__(self):
        namespaces = {}
        for syntax_provider in self.syntax_providers:
            for x in syntax_provider.get_link_resolvers():
                namespaces[x] = syntax_provider
        self.title += ":\n".join([x[0] for x in namespaces.keys()]) + ":\n for quickjump"

    def filter_stream(self, req, method, filename, stream, data):
        add_script(req, 'traclinks/js/anchoranywhere.js')
        add_stylesheet(req, 'traclinks/css/anchoranywhere.css')
        return stream | Transformer('//input[@id="proj-search"]').attr('title', self.title)

    """
    #number for ticket,
    /path for source on repository,
    [number] for changeset,
    rnumber for revision,
    yyyy-mm-ddThh:mm:ss for timeline """

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return [('traclinks', ResourceManager().resource_filename(__name__, 'htdocs'))]


class Browser(Component):
    """ Anchor on dirlist or browser """
    implements(ITemplateStreamFilter)

    def filter_stream(self, req, method, filename, stream, data):
        if filename in ['browser.html', 'dir_entries.html']:
            pathinfo = req.base_path + req.path_info
            pathinfo = quote(pathinfo.encode('utf-8'))
            if req.get_header('x-requested-with') == 'XMLHttpRequest':
                referer = req.get_header('referer')
                pathinfo = referer and urlparse(referer)[2] or pathinfo
            pathinfo = re.compile("(%s/)?([^?]+)(\?.*)?" % pathinfo)
            trimmer = lambda x: re.match(pathinfo, x).groups()[1]
            # thanks to feedback! https://twitter.com/jun66j5/status/374523396857417729
            if req.get_header('user-agent').find('Firefox') > 0:
                trimmer = lambda x: unicode(unquote(re.match(pathinfo, x).groups()[1].encode('utf-8')), 'utf-8')
            stream |= Transformer('//td[@class="name"]').apply(_AttrLaterTransformation('id', '//a', trimmer))
        return stream


class _AttrLaterTransformation(object):
    """ Support class for Browser """

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
