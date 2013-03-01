# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Zack Shahan <zshahan@dig-inc.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener
import re

class TracComponentAlias(Component):
    implements(ITicketChangeListener)

    def __init__(self):
        self.defin_patt = re.compile(r'(\w+)\.(\w+)')
        self._calias = self._get_calias_config()
        
    def _validate(self, val, ticket, calias):
        if val in ticket.values \
        and ticket.values[val] != '' \
        and str(ticket.values[val]).lower() == str(calias['name']).lower():
            return True
        else:
            return False
        return False
        
    def _update_component(self, ticket, calias):
        if self._validate(calias['custom_field'], ticket, calias):
            with self.env.db_transaction as db:
                cursor = db.cursor()
                cursor.execute("update ticket set component = %s where id = %s",
                               (calias['alias'], ticket.id))
                        
    def ticket_created(self, ticket):
        for v in self._calias.keys():
            calias = self._calias[v]
            self._update_component(ticket, calias)
        
    def ticket_changed(self, ticket, comment, author, old_values):
        for v in self._calias.keys():
            calias = self._calias[v]
            if calias['custom_field'] in old_values \
            and 'status' in ticket.values \
            and ticket.values['status'] != 'closed':
                self._update_component(ticket, calias)

    def ticket_deleted(self, ticket):
        pass
        
    def _get_calias_config(self):
        config = self.config['component_alias']
        calias = {}
        for key, val in config.options():
            m = self.defin_patt.match(key)
            if m:
                prefix, attribute = m.groups()
                alias = calias.setdefault(prefix, {})
                alias[attribute] = val
            else:
                calias[key] = val     
        return calias
