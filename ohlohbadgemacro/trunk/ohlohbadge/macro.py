# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Noah Kantrowitz <noah+pypi@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.util.html import html
from trac.wiki.macros import WikiMacroBase


class OhlohBadgeMacro(WikiMacroBase):
    """A small macro for displaying Ohloh (http://ohloh.net)
    statistics badges."""

    SCRIPT_LOCATION = 'https://www.ohloh.net/p/%s/widgets/project_thin_badge'

    def expand_macro(self, formatter, name, content, args=None):
        content = content.strip()
        return html.script('', src=self.SCRIPT_LOCATION % content,
                           type='text/javascript')
