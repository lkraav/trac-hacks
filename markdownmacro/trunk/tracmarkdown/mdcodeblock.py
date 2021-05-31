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

CORE MARKDOWN BLOCKPARSER
===========================================================================

This parser handles basic parsing of Markdown blocks.  It doesn't concern
itself with inline elements such as **bold** or *italics*, but rather just
catches blocks, lists, quotes, etc.

The BlockParser is made up of a bunch of BlockProcessors, each handling a
different type of block. Extensions may add/replace/remove BlockProcessors
as they need to alter how markdown blocks are parsed.
"""
# This code is taken from Python-Markdown https://github.com/Python-Markdown/markdown
#
# Modifications to CodeBlockProcessor so a trac class can be added to the <pre>-tags
from markdown import util
from markdown.blockprocessors import BlockProcessor

class CodeBlockProcessor(BlockProcessor):
    """ Process code blocks.  This one replaces the processor coming
    with markdown so a trac class can be added to the <pre>-tags"""

    def test(self, parent, block):
        return block.startswith(' '*self.tab_length)

    def run(self, parent, blocks):
        sibling = self.lastChild(parent)
        block = blocks.pop(0)
        theRest = ''
        if (sibling is not None and sibling.tag == "pre" and
           len(sibling) and sibling[0].tag == "code"):
            # The previous block was a code block. As blank lines do not start
            # new code blocks, append this block to the previous, adding back
            # linebreaks removed from the split into a list.
            code = sibling[0]
            block, theRest = self.detab(block)
            code.text = util.AtomicString(
                '%s\n%s\n' % (code.text, util.code_escape(block.rstrip()))
            )
        else:
            # This is a new codeblock. Create the elements and insert text.
            pre = util.etree.SubElement(parent, 'pre')
            pre.set('class', 'wiki')  # set Trac class for proper styling
            code = util.etree.SubElement(pre, 'code')
            block, theRest = self.detab(block)
            code.text = util.AtomicString('%s\n' % util.code_escape(block.rstrip()))
        if theRest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, theRest)
