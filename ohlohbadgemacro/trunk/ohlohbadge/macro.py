# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Noah Kantrowitz <noah+pypi@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag 
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import system_message


class OhlohBadgeMacro(WikiMacroBase):
    """A small macro for displaying Ohloh (http://ohloh.net)
    statistics badges."""
    
    SCRIPT_LOCATION = 'http://www.ohloh.net/p/%s/widgets/project_thin_badge'
    
    def expand_macro(self, formatter, name, content, args=None):
        content = content.strip()
        if not content.isdigit():
            return system_message('Invalid Ohloh project ID',
                                  '%s is not a number' % content)
        return tag.script('', src=self.SCRIPT_LOCATION % content,
                          type='text/javascript')
