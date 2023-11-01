# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2023 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import inspect
import os
import pkg_resources
import sys

from trac.core import Component, implements
from trac.config import ListOption, Option
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.util import lazy
from trac.util.translation import dgettext, domain_functions
from trac.web.chrome import Chrome


__all__ = ('TicketFieldsLayoutSetup',)


if sys.version_info[0] == 2:
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
else:
    itervalues = lambda d: d.values()
    iteritems = lambda d: d.items()

getargspec = inspect.getfullargspec \
             if hasattr(inspect, 'getfullargspec') else \
             inspect.getargspec


use_jinja2 = hasattr(Chrome, 'jenv')
_DOMAIN = 'ticketfieldslayout'


if use_jinja2:
    from ._jinja2 import make_jinja2_ext
else:
    make_jinja2_ext = None


if 'doc_domain' not in getargspec(Option.__init__)[0]:
    def _option_tx_0_12(Base):  # Trac 0.12.x
        class OptionTx(Base):
            def __getattribute__(self, name):
                if name == '__class__':
                    return Base
                val = Base.__getattribute__(self, name)
                if name == '__doc__':
                    val = dgettext(_DOMAIN, val)
                return val
        return OptionTx
    _option_tx = _option_tx_0_12
else:
    def _option_tx_1_0(Base):  # Trac 1.0 or later
        def fn(*args, **kwargs):
            kwargs['doc_domain'] = _DOMAIN
            return Base(*args, **kwargs)
        return fn
    _option_tx = _option_tx_1_0


ListOption = _option_tx(ListOption)
add_domain, _ = domain_functions(_DOMAIN, ('add_domain', '_'))

try:
    _locale_dir = pkg_resources.resource_filename(__name__, 'locale')
except KeyError:
    _locale_dir = None


class TicketFieldsLayoutSetup(Component):

    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        if _locale_dir:
            add_domain(self.env.path, _locale_dir)
        if use_jinja2:
            self._install_jinja2_ext()

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, *args):
        return False

    def upgrade_environment(self, *args):
        pass

    # Internal methods

    def _install_jinja2_ext(self):
        chrome = Chrome(self.env)
        try:
            chrome.load_template(os.devnull)
        except:
            pass
        chrome.jenv.add_extension(self._jinja2_ext)

    @lazy
    def _jinja2_ext(self):
        return make_jinja2_ext(self.env)


def get_default_fields(env):
    protected_fields = set(Ticket.protected_fields)
    names = [f['name'] for f in TicketSystem(env).get_ticket_fields()]
    return [name for name in names if name not in protected_fields]


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
