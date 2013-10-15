# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.filters.transform import Transformer
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter


class TypeClassToTicket(Component):
    """ set css-class to type on ticket. """
    implements(ITemplateStreamFilter)

    def get_resource_tags(self, req, resource):
        try:
            from tractags.wiki import WikiTagProvider
            tag_provider = self.compmgr[WikiTagProvider]
            return tag_provider.get_resource_tags(req, resource)
        except:
            return []

    def filter_stream(self, req, method, filename, stream, data):
        value = None
        if filename == 'ticket.html':
            if not 'ticket' in data:
                return stream
            ticket = data['ticket'].values
            fields = self.config.getlist('ticket', 'decorate_fields')
            value = ' '.join(['%s_is_%s' % (field, value.rstrip(' ').rstrip(',').replace('"', ''))
                              for field in fields if field in ticket for value in ticket.get(field).split(' ')]
                             + [ticket.get('type')]  # backward compatibility
                             )
        if filename == 'wiki_view.html':
            value = ' '.join(['tagged_as_%s' % tag for tag in self.get_resource_tags(req, data['context'].resource)])

        if value:
            def add(name, event):
                attrs = event[1][1]
                values = attrs.get(name)
                return values and ' '.join((values, value)) or value
            return stream | Transformer('//body').attr('class', add)
        return stream
