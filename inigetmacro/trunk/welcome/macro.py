""" @package WelcomeMacro
    @file macro.py
    @brief The WelcomeMacro class

    Return a welcome heading with the project name extracted from trac.ini.

    @author Douglas Clifton <dwclifton@gmail.com>
    @date December, 2008
    @version 0.11.3
"""

import re

from trac.core import *
from trac.util.html import html as tag
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import system_message
from trac.wiki.api import parse_args

__all__ = ['WelcomeMacro']


class WelcomeMacro(WikiMacroBase):
    """Return a welcome heading with the project name extracted from trac.ini.

       * User-defined welcome string suffix and prefix.
       * Supports both standard and dictionary methods.
       * With defaults.

       Example: `[[Welcome(prefix=This is the,suffix=Project)]]` yields
       [[Welcome(prefix=This is the,suffix=Project)]]
    """

    def expand_macro(self, formatter, name, args):

        prefix = suffix = ''
        args, kw = parse_args(args)

        if args:
            prefix = args.pop(0).strip()
            if args: suffix = args.pop(0).strip()
        elif kw:
            if 'prefix' in kw: prefix = kw['prefix'].strip()
            if 'suffix' in kw: suffix = kw['suffix'].strip()

        default = {
            'prefix': 'Welcome to the',
            'suffix': 'Project'
        }
        if not prefix: prefix = default['prefix']
        if not suffix: suffix = default['suffix']

        return tag.h1('%s %s %s' % (prefix, self.env.project_name, suffix),
                      id='welcome')
