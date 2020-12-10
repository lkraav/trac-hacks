
# Copyright 2009-2011 Olemis Lang <olemis at gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


r"""Insert configuration options in wiki pages

Copyright 2009-2011 Olemis Lang <olemis at gmail.com>
Licensed under the Apache License
"""
__author__ = 'Olemis Lang'

from trac.core import TracError, Interface
from trac.config import *
from trac.config import _TRUE_VALUES
from trac.util.compat import all
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase

from tracbm.util import load_interface

from genshi.builder import tag

class ConfigOptionMacro(WikiMacroBase):
    r"""Insert configuration options in Wiki pages
    
    Usage is as follows.
    
    `[[ConfigOption(section, name, type=option_type, sep=char)]]`
    
    ''section'' :           the section in trac.ini (mandatory).
    ''name'' :              option name (mandatory).
    ''type'' :              if this keyword argument is present then 
                            the value will be rendered using an
                            appropriate format according to the option 
                            type. Supported values are `text`,
                            `bool`, `int`, `list`, `path`, `extension`,
                            `extension_list`. Default behavior is `auto` which 
                            means using the information stored in the global 
                            options cache.
    ''sep'' :               list separator (optional, ignored if 
                            `type`! = `list`).
    ''keep_empty'':         include empty list items (optional, ignored if 
                            `type`! = `list`).
    ''interface'' :         components should implement this interface. Value 
                            should be of the form `some.module:some.attribute`
                            (e.g. `trac.web:IRequestHandler`). If missing and 
                            `type` is set to `extension` or `extension_list`) 
                            then the interface type will be looked up in the 
                            options cache. If it can't be found an error is 
                            raised.
    ''include_missing'' :   if true (the default) all components implementing 
                            the interface are returned, with those specified 
                            by the option ordered first (optional if type is 
                            `extension_list`).
    
    Note: In order to render the target information the approprioate permission 
            have to be granted by specifying a (comma-separated) list of 
            permission names in options of the form `section.option`, 
            `section.*` or , `*` in `config-perm` section. For instance the 
            following configuration
            
            {{{
            [config-perm]
            * = WIKI_ADMIN, TICKET_ADMIN
            project.* = WIKI_VIEW
            project.name = *
            }}}
            
            allows users having `WIKI_ADMIN` and `TICKET_ADMIN` permissions to view 
            all configuration options, in addition all those having `WIKI_VIEW` 
            permission may see all options under `project` section, and finally 
            option `project.name` may be seen by everybody.
    """
    OPTION_MAP = {Option: 'text',
                    BoolOption: 'bool',
                    IntOption: 'int',
                    ListOption: 'list',
                    PathOption: 'path',
                    ExtensionOption: 'extension',
                    OrderedExtensionsOption: 'extension_list',
                    }
    
    def expand_macro(self, formatter, name, content):
        # TODO: Permissions for sections and individual options
        args, kw = parse_args(content)
        try :
            s, o = args
        except IndexError :
            raise TracError(_('Specify both section and option name, and nothing else'))
        else :
            s = s.strip() ; o = o.strip()
            perm_options = tuple(('%s.%s,%s.*,*' % (s, o, s)).split(','))
            req = formatter.context.req
            getlist = self.config.getlist
            if 'TRAC_ADMIN' not in req.perm and \
                    all(p != '*' and p not in req.perm for _o in perm_options \
                                            for p in getlist('config-perm', _o, \
                                                            keep_empty=False)):
                self.log.warning('Preventing user `%s` from reading option '
                                    '`%s` in `%s`', req.authname, o, s)
                raise TracError(_('Insufficient privileges '
                                    'to perform this operation.') + 
                                    _(' Check %s, %s, %s in trac.ini') % perm_options)
            opt_type = kw.get('type', 'auto')
            self.log.debug('Rendering config option %s in %s using %s', 
                            o, s, opt_type)
            return getattr(self, '_render_' + opt_type, 
                                self._do_render_unknown) (s, o, kw)
    
    # Rendering methods
    def _render_auto(self, s, o, opts):
        opt = Option.registry.get((s, o))
        if opt is not None :
            opt_type = self.OPTION_MAP.get(opt.__class__, 'unknown')
            if opt_type in ('extension', 'extension_list'):
                opts.setdefault('interface', opt.xtnpt.interface)
                cond = getattr(opt, 'include_missing', None) in _TRUE_VALUES
                opts.setdefault('include_missing', cond and 'true' or '')
            if opt_type in ('list', 'extension_list'):
                opts.setdefault('sep', opt.sep)
                opts.setdefault('keep_empty', opt.keep_empty and 'true' or '')
            opts['default'] = opt.default
            return getattr(self, '_render_' + opt_type, 
                                self._do_render_unknown) (s, o, opts)
    
    def _render_text(self, s, o, opts):
        value = self.config.get(s, o, opts.get('default'))
        if value :
            return to_unicode(value)
        else :
            return self._do_render_none(s, o, opts)
    
    def _render_bool(self, s, o, opts):
        value = self.config.getbool(s, o, opts.get('default'))
        return tag.input(type="radio", 
                        checked=value in _TRUE_VALUES and "true" or None, 
                        disabled="true")
    
    def _render_int(self, s, o, opts):
        value = self.config.getint(s, o, opts.get('default'))
        return tag.tt(str(value))
    
    def _render_list(self, s, o, opts):
        value = self.config.getlist(s, o, None, opts.get('sep', ','), 
                                        opts.get('keep_empty', 'true').lower() in _TRUE_VALUES)
        if value :
            return tag.o([tag.li(item) for item in value])
        else :
            return tag.strike('Empty list')
    
    _render_path = _render_text
    
    def _render_extension(self, s, o, opts):
        try :
            interface = opts.get('interface') or \
                        Option.registry.get((s, o)).xtnpt.interface
        except :
            raise TracError(_('Keyword argument `interface` is required'))
        if not issubclass(interface, Interface):
            interface = load_interface(interface)
        self.log.debug("Rendering extension implementing %s", interface)
        try :
            if s is not None :
                value = ExtensionOption(s, o, interface, None).__get__(self, self.__class__)
            else :
                # A component is supplied instead of option name
                value = o
        except AttributeError :
            value = self.env.config.get(s, o, None)
            if value is not None :
                return tag.span(tag.strike(value), 
                                tag.span(_('missing ?'), style="color: red;"))
            else :
                return tag.strike(_('Value not found'))
        else :
            value = value.__class__
            return tag.span(tag.tt(value.__name__), ' at ', tag.i(value.__module__))
    
    def _render_extension_list(self, s, o, opts):
        include_missing = opts.get('include_missing', 'true').lower()  in _TRUE_VALUES
        try :
            interface = opts.get('interface') or \
                        Option.registry.get((s, o)).xtnpt.interface
        except :
            raise TracError(_('Keyword argument `interface` is required'))
        if not issubclass(interface, Interface):
            interface = load_interface(interface)
        opts['interface'] = interface
        self.log.debug("Listing extensions for %s", interface)
        option = OrderedExtensionsOption(s, o, interface, include_missing=include_missing)
        components = option.__get__(self, self.__class__)
        if components :
            return tag.ol([tag.li(self._render_extension(None, c, opts))] \
                            for c in components)
        else :
            return tag.strike(_('Empty list'))
    
    def _do_render_none(self, s, o, opts):
        return tag.strike(_('Missing ?'))
    
    def _do_render_unknown(self, s, o, opts):
        raise TracError(_('Invalid configuration option type'))
    
    _render_unknown = _do_render_unknown
