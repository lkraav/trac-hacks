# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.config import ListOption, Option
from trac.env import IEnvironmentSetupParticipant
from trac.util import arity
from trac.util.translation import dgettext, domain_functions


__all__ = ['TicketFieldsLayoutTxModule']


_DOMAIN = 'ticketfieldslayout'


if arity(Option.__init__) <= 5:
    def _option_tx_0_12(Base):  # Trac 0.12.x
        class OptionTx(Base):
            def __getattribute__(self, name):
                val = Base.__getattribute__(self, name)
                if name == '__doc__':
                    val = dgettext(_DOMAIN, val)
                return val
        return OptionTx
    _option_tx = _option_tx_0_12
else:
    def _option_tx_1_0(Base):  # Trac 1.0 or later
        class OptionTx(Base):
            def __init__(self, *args, **kwargs):
                kwargs['doc_domain'] = _DOMAIN
                Base.__init__(self, *args, **kwargs)
        return OptionTx
    _option_tx = _option_tx_1_0


ListOption = _option_tx(ListOption)
add_domain, _ = domain_functions(_DOMAIN, ('add_domain', '_'))


class TicketFieldsLayoutTxModule(Component):

    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        from pkg_resources import resource_exists, resource_filename
        if resource_exists(__name__, 'locale'):
            add_domain(self.env.path, resource_filename(__name__, 'locale'))

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        return False

    def upgrade_environment(self, db):
        pass


def get_groups(config):
    section = 'ticketfieldslayout'
    names = [name[6:] for name, value in config.options(section)
                      if name.startswith('group.') and
                         len(name.split('.')) == 2]
    groups = {}
    for idx, name in enumerate(sorted(names)):
        name = name.lower()
        prefix = 'group.%s' % name
        fields = [f.lower() for f in config.getlist(section, prefix) if f]
        label = config.get(section, prefix + '.label', 'Group %d' % (idx + 1))
        collapsed = config.getbool(section, prefix + '.collapsed',
                                   'disabled')
        groups[name] = dict(name=name, fields=fields, label=label,
                            collapsed=collapsed)
    return groups
