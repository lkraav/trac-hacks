#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013, 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.


from datetime import datetime
from genshi.builder import tag
from genshi.filters.transform import Transformer
from trac.core import Component, implements
from trac.resource import get_resource_url, Resource
from trac.util.datefmt import format_datetime, format_time, from_utimestamp, \
    format_date
from trac.web.api import ITemplateStreamFilter
from trac.wiki.model import WikiPage


class Query(Component):
    """ add \"Save to wiki\" button in CUSTOM QUERY page.
a \"page_name\" URL Parameter uses for default name if exists."""
    implements(ITemplateStreamFilter)

    @classmethod
    def formatter(self, obj):
        return isinstance(obj, datetime) and format_datetime(obj) or unicode(obj)

    #ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'query.html':
            return stream
        query_string = 'query:' + '&'.join(['%s=%s' % (key, '|'.join([cond for cond in values]))
                                            for constraint in data['query'].constraints
                                            for key, values in constraint.items()])
        page_name = 'report_resource' in data and \
            'report:%s' % data['report_resource'].id or query_string
        if 'page_name' in req.args:
            page_name = req.args['page_name']
            query_string += '&page_name=%s' % page_name
        page = WikiPage(self.env, page_name)
        if 'WIKI_MODIFY' not in req.perm(page.resource):
            return stream
        cols = [header['name'] for header in data['headers']]
        text = '= Snapshot of [%s the query]: =\n' % query_string
        text += '{{{#!QueryResults(group=%s) \n' % data['query'].group
        text += '||= href =||= %s\n' % ' =||= '.join(cols)
        for (group_name, tickets) in data['groups']:
            text += '|| group: %s\n' % group_name
            for ticket in tickets:
                text += '|| %s || %s\n' % (ticket['href'],
                    ' || '.join([self.formatter(ticket[col]) for col in cols]))
        text += '}}}'
        if 'id' in cols:
            ticket_id_list = [str(ticket['id']) for ticket in tickets for (_, tickets) in data['groups']]
            if len(ticket_id_list) > 0:
                text += '\n([ticket:' + ','.join(ticket_id_list) + ' query by ticket id])'
        div = tag.div(tag.input(value='Save as wiki:', type='submit'),
                      tag.input(name='action', value='edit', type='hidden'),
                      tag.input(name='text', value=text, type='hidden'),
                      tag.input(name='page', value=page_name))
        return stream | Transformer('//div[@id="content"]/div[@class="buttons"]') \
            .append(tag.form(div, action=get_resource_url(self.env, Resource('wiki'), self.env.href)))


class Report(Component):
    """ add \"Save to wiki\" button in REPORT page. """

    implements(ITemplateStreamFilter)

    @classmethod
    def formatter(self, col, cell_value):
        if col == 'time':
            return cell_value != '' and format_time(from_utimestamp(long(cell_value))) or '--'
        if col in ('date', 'created', 'modified'):
            return cell_value != '' and format_date(from_utimestamp(long(cell_value))) or '--'
        if col == 'datetime':
            return cell_value != '' and format_datetime(from_utimestamp(long(cell_value))) or '--'
        return cell_value

    #ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'report_view.html':
            return stream
        page_name = 'report:%s' % data['context'].resource.id
        page_label = data['title']
        page = WikiPage(self.env, page_name)
        if 'WIKI_MODIFY' not in req.perm(page.resource):
            return stream
        text = '= Snapshot of [%s %s]: =\n' % (page_name, page_label)
        text += '{{{#!QueryResults\n'
        cols = [header['col'] for header in data.get('header_groups', [[]])[0] if not header['hidden']]
        cols_work = [t for t in cols]  # copy
        if 'ticket' in cols_work:
            cols_work[cols_work.index('ticket')] = 'id'  # replace 'ticket' to 'id'
        text += '||= href =||= %s\n' % ' =||= '.join(cols_work)
        ticket_id_list = []
        for  groupindex, row_group in data.get('row_groups', []):
            text += '|| group: %s\n' % groupindex
            for row in row_group:
                row = row['cell_groups'][0]
                ticket = {}
                for value in row:
                    ticket[value['header']['col']] = value['value']
                ticket['href'] = get_resource_url(self.env, Resource('ticket', ticket.get('ticket', 0)), self.env.href)
                text += '|| %s || %s\n' % (ticket['href'],
                    ' || '.join([self.formatter(col, ticket[col]) for col in cols]))
                if 'ticket' in ticket:
                    ticket_id_list.append(ticket['ticket'])
        text += '}}}'
        if len(ticket_id_list) > 0:
            text += '\n([ticket:' + ','.join(ticket_id_list) + ' query by ticket id])'
        div = tag.div(tag.input(value='Save as wiki:', type='submit'),
                      tag.input(name='action', value='edit', type='hidden'),
                          tag.input(name='text', value=text, type='hidden'),
                      tag.input(name='page', value=page_name))
        return stream | Transformer('//div[@id="content"]/div[@class="buttons"]') \
            .append(tag.form(div, action=get_resource_url(self.env, Resource('wiki'), self.env.href)))
