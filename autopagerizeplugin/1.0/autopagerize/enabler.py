#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.core import START, QName
from genshi.filters.transform import Transformer, ENTER
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter


def addAutoPagerizeAttribute(stream):
    for mark, (kind, data, pos) in stream:
        if mark is ENTER and kind is START and len(data) == 2:
            element, attrs = data
            attr_value = attrs.get('class', '')
            attrs |= [(QName('class'), ' '.join([attr_value, 'autopagerize_page_element']))]
            data = element, attrs
        yield mark, (kind, data, pos)


class report(Component):
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ["report_view.html"]:
            stream |= Transformer().select('//table[contains(@class,"listing")]/tbody').apply(addAutoPagerizeAttribute).end() \
                        .select('//div[contains(@class, "paging")]/span[contains(@class, "next")]/a').attr('rel', 'next').end()
        return stream


class query(Component):  # I know batch_modify doesn't work
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ["query.html"]:
            stream |= Transformer().select('//table[contains(@class,"listing")]/tbody').apply(addAutoPagerizeAttribute).end()
        return stream


class timeline(Component):
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ["timeline.html"]:
            stream |= Transformer().select('//div[@id="content"]/dl').apply(addAutoPagerizeAttribute).end() \
                        .select('//div[@id="ctxtnav"]//a[contains(@class, "prev")]').attr('rel', 'next').end()
        return stream


class search(Component):
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ["search.html"]:
            stream |= Transformer().select('//dl[@id="results"]').apply(addAutoPagerizeAttribute).end()
        return stream


class revisionlog(Component):
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ["revisionlog.html"]:
            stream |= Transformer().select('//table[contains(@class,"listing")]/tbody').apply(addAutoPagerizeAttribute).end() \
                        .select('//div[@id="ctxtnav"]//li[@class="last"]//a').attr('rel', 'next').end()
        return stream
