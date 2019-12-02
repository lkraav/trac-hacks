# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 ERCIM
# Copyright (C) 2009 Jean-Guilhem Rouel <jean-guilhem.rouel@ercim.org>
# Copyright (C) 2009 Vivien Lacourba <vivien.lacourba@ercim.org>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.ticket.api import ITicketManipulator
from trac.web.chrome import Chrome

from defaultcc.model import DefaultCC


class TicketDefaultCC(Component):
    """Automatically adds a default CC list when new tickets are created.

    Tickets are modified at the time of creation by adding the component's
    default CC list to the ticket's CC list.
    """

    implements(ITicketManipulator)

    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        if 'preview' not in req.args:
            chrome = Chrome(self.env)
            cc = chrome.cc_list(ticket['cc'])
            if 'component' in ticket._old and ticket._old['component']:
                old_comp = ticket._old['component']
                old_comp_default_cc = DefaultCC(self.env, old_comp)
                old_comp_cc = chrome.cc_list(old_comp_default_cc.cc)
                for entry in old_comp_cc:
                    try:
                        cc.remove(entry)
                    except ValueError:
                        pass
            comp_default_cc = DefaultCC(self.env, ticket['component'])
            if comp_default_cc:
                comp_cc = chrome.cc_list(comp_default_cc.cc)
                if comp_cc:
                    cc.extend(comp_cc)
            if cc:
                ticket['cc'] = ', '.join(cc)

        return []
