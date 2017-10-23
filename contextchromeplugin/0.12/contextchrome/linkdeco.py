#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013,2017 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.ticket.web_ui import TicketModule
from trac.web.api import IRequestHandler, IRequestFilter
from trac.config import ListOption, IntOption
from trac.util import Ranges, as_int
from trac.util.html import Element
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage
from datetime import datetime
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script,\
    add_script_data
from pkg_resources import ResourceManager
from trac.resource import Resource
from warnings import catch_warnings


class TicketLinkDecorator(Component):
    """ set css-class to ticket link as ticket field value. field name can
    set in [ticket]-decorate_fields in trac.ini
    """
    implements(IRequestHandler)

    wrapped = None

    decorate_fields = ListOption('ticket', 'decorate_fields', default='type',
        doc=""" comma separated List of field names to add css class of ticket link.
            (Provided by !ContextChrome.!TicketLinkDecorator) """)

    def __init__(self):
        Component.__init__(self)
        if not self.wrapped:
            self.wrap()

    def wrap(self):
        ticketsystem = self.compmgr[TicketSystem]
        ticketmodule = self.compmgr[TicketModule]

        def _format_link(*args, **kwargs):  # hook method
            element = self.wrapped[0](*args, **kwargs)
            if isinstance(element, Element):
                class_ = element.attrib.get('class')
                if class_ and element.attrib.get('href'):  # existing ticket
                    deco = self.get_ticket_deco(*args, **kwargs) or []
                    element.attrib |= [('class', ' '.join(deco + [class_]))]
            return element

        def _format_comment_link(*args, **kwargs):  # hook method
            element = self.wrapped[1](*args, **kwargs)
            if isinstance(element, Element):
                class_ = element.attrib.get('class')
                if class_ and element.attrib.get('href'):  # existing ticket
                    deco = self.get_comment_deco(*args, **kwargs) or []
                    element.attrib |= [('class', ' '.join(deco + [class_]))]
            return element
        
        def get_timeline_events(*args, **kwargs):
            events = self.wrapped[2](*args, **kwargs)
            for event in events:
                try:
                    ticket = Ticket(self.env, event[3][0].id)
                    deco = [event[0]] + (self._decorate(ticket) or [])
                    event = (' '.join(deco), ) + event[1:]
                except:
                    pass
                yield event

        self.wrapped = [
            ticketsystem._format_link,
            ticketsystem._format_comment_link,
            ticketmodule.get_timeline_events,
        ]
        ticketsystem._format_link = _format_link
        ticketsystem._format_comment_link = _format_comment_link
        ticketmodule.get_timeline_events = get_timeline_events

    def get_ticket_deco(self, formatter, ns, target, label, fullmatch=None):
        link, params, fragment = formatter.split_link(target)  # @UnusedVariable
        r = Ranges(link)
        if len(r) == 1:
            num = r.a
            ticket = formatter.resource('ticket', num)
            from trac.ticket.model import Ticket
            if Ticket.id_is_valid(num) and \
                    'TICKET_VIEW' in formatter.perm(ticket):
                ticket = Ticket(self.env, num)
                return self._decorate(ticket)

    def get_comment_deco(self, formatter, ns, target, label):
        resource = None
        if ':' in target:
            elts = target.split(':')
            if len(elts) == 3:
                cnum, realm, id = elts
                if cnum != 'description' and cnum and not cnum[0].isdigit():
                    realm, id, cnum = elts  # support old comment: style
                id = as_int(id, None)
                resource = formatter.resource(realm, id)
        else:
            resource = formatter.resource
            cnum = target

        if resource and resource.id and resource.realm == 'ticket' and \
                cnum and (cnum.isdigit() or cnum == 'description'):
            if TicketSystem(self.env).resource_exists(resource):
                from trac.ticket.model import Ticket
                ticket = Ticket(self.env, resource.id)
                return self._decorate(ticket)

    def _decorate(self, ticket):
        fields = self.config.getlist('ticket', 'decorate_fields')
        return ['%s_is_%s' % (field, ticket.values[field])
                for field in fields if field in ticket.values]

    # IRequestHandler Methods
    def match_request(self, req):
        return False

    def process_request(self, req):
        pass


class WikiLinkNewDecolator(Component):
    """ set \"new\" css-class to wiki link if the page is young. age can set in [wiki]-wiki_new_info_second in trac.ini"""
    implements(IRequestHandler)

    wrapped = None

    wiki_new_info_day = IntOption('wiki', 'wiki_new_info_second', '432000',
        doc=u"""age in seconds to add new icon. (Provided by !ContextChrome.!WikiLinkNewDecolator) """)

    def __init__(self):
        Component.__init__(self)
        if not self.wrapped:
            self.wrap()

    def wrap(self):
        wikisystem = self.compmgr[WikiSystem]

        def _format_link(*args, **kwargs):  # hook method
            element = self.wrapped(*args, **kwargs)
            if isinstance(element, Element):
                class_ = element.attrib.get('class')
                if class_ and element.attrib.get('href'):  # existing ticket
                    deco = self.get_deco(*args, **kwargs) or []
                    element.attrib = element.attrib | [('class', ' '.join(deco + [class_]))]
            return element
        self.wrapped = wikisystem._format_link
        wikisystem._format_link = _format_link

    def get_deco(self, formatter, ns, pagename, label, ignore_missing,
                     original_label=None):
        wikipage = WikiPage(self.env, pagename)
        if not wikipage.time:
            return
        now = datetime.now(formatter.req.tz)
        delta = now - wikipage.time
        limit = self.config.getint('wiki', 'wiki_new_info_second')
        if limit < delta.days * 86400 + delta.seconds:
            return
        return ['new']

    # IRequestHandler Methods
    def match_request(self, req):
        return False

    def process_request(self, req):
        pass


class InternalStylesheet(Component):
    """ Use internal stylesheet. Off to use your own site.css for \".new\" css-class."""
    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        add_stylesheet(req, "contextchrome/css/contextchrome.css")
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


class InterTracTicketLinkDecorator(Component):
    """ set css-class to type on external ticket. """
    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        add_script(req, "contextchrome/js/xdr.js")
        add_script(req, "contextchrome/js/intertracticketlinkdecorator.js")
        add_script_data(req, {'config__ticket__decolate_fields': self.config.getlist('ticket', 'decorate_fields')})
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


