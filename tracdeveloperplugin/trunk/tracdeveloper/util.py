# -*- coding: utf-8 -*-

import re

from genshi.builder import tag

def linebreaks(value):
    """Converts newlines in strings into <p> and <br />s."""
    if not value:
        return ''
    value = re.sub(r'\r\n|\r|\n', '\n', value) # normalize newlines
    paras = re.split('\n{2,}', value)
    return tag(tag.p((line, tag.br) for line in para.splitlines())
               for para in paras)
