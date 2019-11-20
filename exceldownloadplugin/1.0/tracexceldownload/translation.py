# -*- coding: utf-8 -*-

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.config import Option
from trac.env import IEnvironmentSetupParticipant
from trac.util.text import to_utf8
try:
    from trac.util.translation import domain_functions
except ImportError:
    domain_functions = None


if domain_functions:
    from trac.util.translation import dgettext, dngettext
    from trac.config import ChoiceOption

    def domain_options(domain, *options):
        import inspect
        if 'doc_domain' in inspect.getargspec(Option.__init__)[0]:
            def _option_with_tx(Option, doc_domain):  # Trac 1.0+
                def fn(*args, **kwargs):
                    kwargs['doc_domain'] = doc_domain
                    return Option(*args, **kwargs)
                return fn
        else:
            def _option_with_tx(Option, doc_domain):  # Trac 0.12.x
                class OptionTx(Option):
                    def __getattribute__(self, name):
                        if name == '__class__':
                            return Option
                        value = Option.__getattribute__(self, name)
                        if name == '__doc__':
                            value = dgettext(doc_domain, value)
                        return value
                return OptionTx
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

        def environment_needs_upgrade(self, db):
            return False

        def upgrade_environment(self, db):
            pass

else:
    from trac.util.translation import _, N_, gettext, ngettext

    class ChoiceOption(Option):
        def __init__(self, section, name, choices, doc=''):
            Option.__init__(self, section, name, to_utf8(choices[0]), doc)

    def dgettext(domain, string, **kwargs):
        if kwargs:
            return string % kwargs
        return string

    def dngettext(domain, singular, plural, num, **kwargs):
        kwargs = kwargs.copy()
        kwargs.setdefault('num', num)
        if num != 1:
            string = plural
        else:
            string = singular
        return string % kwargs
