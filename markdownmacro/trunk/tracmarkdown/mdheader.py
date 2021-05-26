# -*- coding: utf-8 -*-
"""
Python Markdown

A Python implementation of John Gruber's Markdown.

Documentation: https://python-markdown.github.io/
GitHub: https://github.com/Python-Markdown/markdown/
PyPI: https://pypi.org/project/Markdown/

Started by Manfred Stienstra (http://www.dwerg.net/).
Maintained for a few years by Yuri Takhteyev (http://www.freewisdom.org).
Currently maintained by Waylan Limberg (https://github.com/waylan),
Dmitry Shachnev (https://github.com/mitya57) and Isaac Muse (https://github.com/facelessuser).

Copyright 2007-2018 The Python Markdown Project (v. 1.7 and later)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)

License: BSD (see LICENSE.md for details).
"""
# This code is taken from Python-Markdown https://github.com/Python-Markdown/markdown
import re
from markdown import util
from markdown.blockprocessors import BlockProcessor


class HashHeaderProcessor(BlockProcessor):
    """ Process Hash Headers. This one replaces the processor coming
    with markdown so a trac class can be added to the <h>-tags"""

    # Detect a header at start of any line in block
    RE = re.compile(r'(?:^|\n)(?P<level>#{1,6})(?P<header>(?:\\.|[^\\])*?)#*(?:\n|$)')

    def test(self, parent, block):
        return bool(self.RE.search(block))

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)
        if m:
            before = block[:m.start()]  # All lines before header
            after = block[m.end():]     # All lines after header
            if before:
                # As the header was not the first line of the block and the
                # lines before the header must be parsed first,
                # recursively parse this lines as a block.
                self.parser.parseBlocks(parent, [before])
            # Create header using named groups from RE
            h = util.etree.SubElement(parent, 'h%d' % len(m.group('level')),
                                      attrib={'class': 'section'})  # add Trac class
            h.text = m.group('header').strip()
            if after:
                # Insert remaining lines as first block for future parsing.
                blocks.insert(0, after)
        else:  # pragma: no cover
            # This should never happen, but just in case...
            pass
            # logger.warn("We've got a problem header: %r" % block)
