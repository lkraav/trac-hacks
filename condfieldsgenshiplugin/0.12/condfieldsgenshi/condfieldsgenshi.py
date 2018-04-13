# -*- coding: utf-8 -*-
#
# Copyright (c) 2008, Stephen Hansen <shansen@advpubtech.com>
# Copyright (C) 2012-2013 Reinhard Wobst <rwobst@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

# R.Wobst, @(#) Jan 11 2013, 17:50:43
#
# New plugin based on Condfield-Patch for BlackmagicPlugin
# (http://www.trac-hacks.org/ticket/2486) which does not work for Trac 0.11 or
# later. Functionality is reduced to "cond_field" and extended by "default"
# entry:
#
# Configured fields are displayed only if the ticket type has/has not certain
# value(s).
#
# This plugin is based on Genshi, not on Javascript; can easily be extended. A
# detailed documentation can be found in condfieldsgenshi.txt.

from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer


class CondfieldTweaks(Component):
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'ticket.html':
            return stream

        ticket = data['ticket']
        ticket_type = ticket['type']
        if not ticket_type:  # New ticket with no default_type
            findex = data['fields_map']['type']
            ticket_type = data['fields'][findex]['options'][0]

        # Test if condfields shall be shown or hidden by default.
        shown_by_default = \
            self.config.getbool('condfieldsgenshi', 'default', True)

        for field in self.config.getlist('condfieldsgenshi', 'tweaks', []):

            type_cond = self.config.getlist('condfieldsgenshi',
                                            field + '.type_cond', None)

            if type_cond is None:
                continue

            if not type_cond:
                matches_type_cond = True
            else:
                matches_type_cond = False
                for cond in type_cond:
                    if cond.startswith('!'):
                        matches_type_cond |= ticket_type == cond[1:].lower()
                    else:
                        matches_type_cond |= ticket_type == cond.lower()

            if shown_by_default and matches_type_cond or \
                    not shown_by_default and not matches_type_cond:
                if field != 'type':
                    stream |= Transformer(
                        '//th[@id="h_%s"]' % field).replace(" ")
                    stream |= Transformer(
                        '//td[@headers="h_%s"]' % field).replace(" ")
                    stream |= Transformer(
                        '//label[@for="field-%s"]' % field).replace(" ")
                    stream |= Transformer(
                        '//*[@id="field-%s"]' % field).replace(" ")
                else:
                    continue
                    stream |= Transformer(
                        '//label[@for="field-type"]/text()'). \
                        replace('Type (Fixed):')
                    stream |= Transformer(
                        '//*[@id="field-type"]/option').remove()
                    stream |= Transformer(
                        '//*[@id="field-type"]').append(ticket_type)
                    stream |= Transformer(
                        '//*[@id="field-type"]/text()').wrap('option')
        return stream
