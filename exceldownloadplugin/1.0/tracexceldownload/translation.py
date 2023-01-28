# -*- coding: utf-8 -*-

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.config import ChoiceOption
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import dgettext, dngettext, domain_functions


def domain_options(domain, *options):
    def _option_with_tx(option, doc_domain):
        def fn(*args, **kwargs):
            kwargs['doc_domain'] = doc_domain
            return option(*args, **kwargs)
        return fn
    if len(options) == 1:
        return _option_with_tx(options[0], domain)
    else:
        return map(lambda option: _option_with_tx(option, domain), options)


_, N_, gettext, ngettext, add_domain = domain_functions(
    'tracexceldownload', '_', 'N_', 'gettext', 'ngettext', 'add_domain')
ChoiceOption = domain_options('tracexceldownload', ChoiceOption)


class TranslationModule(Component):

    implements(IEnvironmentSetupParticipant)

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        add_domain(self.env.path, resource_filename(__name__, 'locale'))

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db=None):
        return False

    def upgrade_environment(self, db=None):
        pass
