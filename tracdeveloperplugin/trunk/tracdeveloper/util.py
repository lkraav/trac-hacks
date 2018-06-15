# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Ryan Ollos
# Copyright (C) 2012-2013 Olemis Lang
# Copyright (C) 2008-2009 Noah Kantrowitz
# Copyright (C) 2008 Christoper Lenz
# Copyright (C) 2007-2008 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from trac.util.html import html as tag


def linebreaks(value):
    """Converts newlines in strings into <p> and <br />s."""
    if not value:
        return ''
    value = re.sub(r'\r\n|\r|\n', '\n', value) # normalize newlines
    paras = re.split('\n{2,}', value)
    return tag(tag.p((line, tag.br) for line in para.splitlines())
               for para in paras)
