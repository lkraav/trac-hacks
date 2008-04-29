import os
import inspect
import StringIO
import unittest
import difflib

from trac.core import *
from trac.mimeview import Context
from trac.test import Mock, MockPerm, EnvironmentStub
from trac.util.html import html
from trac.util.text import to_unicode
from trac.web.href import Href
from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.formatter import HtmlFormatter, InlineHtmlFormatter
from trac.wiki.macros import WikiMacroBase

# We need to supply our own macro because the real macros
# can not be loaded using our 'fake' environment.

class HelloWorldMacro(WikiMacroBase):
    """A dummy macro used by the unit test."""

    def expand_macro(self, formatter, name, content):
        return 'Hello World, args = ' + content

class DivHelloWorldMacro(WikiMacroBase):
    """A dummy macro returning a div block, used by the unit test."""

    def expand_macro(self, formatter, name, content):
        return '<div>Hello World, args = %s</div>' % content

class DivCodeMacro(WikiMacroBase):
    """A dummy macro returning a div block, used by the unit test."""

    def expand_macro(self, formatter, name, content):
        return '<div class="code">Hello World, args = %s</div>' % content

class DivCodeElementMacro(WikiMacroBase):
    """A dummy macro returning a Genshi Element, used by the unit test."""

    def expand_macro(self, formatter, name, content):
        return html.DIV('Hello World, args = ', content, class_="code")

class DivCodeStreamMacro(WikiMacroBase):
    """A dummy macro returning a Genshi Stream, used by the unit test."""

    def expand_macro(self, formatter, name, content):
        from genshi.template import MarkupTemplate
        tmpl = MarkupTemplate("""
        <div>Hello World, args = $args</div>
        """)
        return tmpl.generate(args=content)

class NoneMacro(WikiMacroBase):
    """A dummy macro returning `None`, used by the unit test."""

    def expand_macro(self, formatter, name, content):
        return None

class SampleResolver(Component):
    """A dummy macro returning a div block, used by the unit test."""

    implements(IWikiSyntaxProvider)

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('link', self._format_link)

    def _format_link(self, formatter, ns, target, label):
        kind, module = 'text', 'stuff'
        try:
            kind = int(target) % 2 and 'odd' or 'even'
            module = 'thing'
        except ValueError:
            pass
        return html.A(label, class_='%s resolver' % kind,
                      href=formatter.href(module, target))


class WikiTestCase(unittest.TestCase):

    def __init__(self, input, correct, file, line, setup=None, teardown=None,
                 context=None):
        unittest.TestCase.__init__(self, 'test')
        self.title, self.input = input.split('\n', 1)
        if self.title:
            self.title = self.title.strip()
        self.correct = correct
        self.file = file
        self.line = line
        self._setup = setup
        self._teardown = teardown

        self.env = EnvironmentStub()
        req = Mock(href=Href('/'), abs_href=Href('http://www.example.com/'),
                   authname='anonymous', perm=MockPerm(), args={})
        if context:
            if isinstance(context, tuple):
                context = Context.from_request(req, *context)
        else:
            context = Context.from_request(req, 'wiki', 'WikiStart')
        self.context = context

        # -- macros support
        self.env.path = ''
        # -- intertrac support
        self.env.config.set('intertrac', 'trac.title', "Trac's Trac")
        self.env.config.set('intertrac', 'trac.url',
                            "http://trac.edgewall.org")
        self.env.config.set('intertrac', 't', 'trac')
        self.env.config.set('intertrac', 'th.title', "Trac Hacks")
        self.env.config.set('intertrac', 'th.url',
                            "http://trac-hacks.org")
        self.env.config.set('intertrac', 'th.compat', 'false')

        # TODO: remove the following lines in order to discover
        #       all the places were we should use the req.href
        #       instead of env.href
        self.env.href = req.href
        self.env.abs_href = req.abs_href

    def setUp(self):
        if self._setup:
            self._setup(self)

    def tearDown(self):
        if self._teardown:
            self._teardown(self)

    def test(self):
        """Testing WikiFormatter"""
        formatter = self.formatter()
        v = unicode(formatter.generate()).replace('\r','')
        try:
            self.assertEquals(self.correct, v)
        except AssertionError, e:
            msg = to_unicode(e)
            import re
            match = re.match(r"u?'(.*)' != u?'(.*)'", msg)
            if match:
                sep = '-' * 15
                g1 = ["%s\n" % x for x in match.group(1).split(r'\n')]
                g2 = ["%s\n" % x for x in match.group(2).split(r'\n')]
                diff = ''.join(list(difflib.unified_diff(g1, g2)))
                msg = '\n%s expected:\n%s\n%s actual:\n%s\n%s' \
                      ' wiki text:\n%s\ndiff:\n%s' \
                      % (sep, ''.join(g1), sep, ''.join(g2), sep,
# Tip: sometimes, 'expected' and 'actual' differ only by whitespace.
#      If so, replace the above lines by those two:
#                      % (sep, match.group(1).replace(' ', '.'), sep
#                         sep, match.group(2).replace(' ', '.'), sep,
                         self.input, diff)
            raise AssertionError( # See below for details
                '%s\n\n%s:%s: "%s" (%s flavor)' \
                % (msg, self.file, self.line, self.title, formatter.flavor))

    def formatter(self):
        return HtmlFormatter(self.env, self.context, self.input)

    def shortDescription(self):
        return 'Test ' + self.title


class OneLinerTestCase(WikiTestCase):
    def formatter(self):
        return InlineHtmlFormatter(self.env, self.context, self.input)


def suite(data=None, setup=None, file=__file__, teardown=None, context=None):
    suite = unittest.TestSuite()
    if not data:
        file = os.path.join(os.path.split(file)[0], 'wiki-tests.txt')
        data = open(file, 'r').read().decode('utf-8')
    tests = data.split('=' * 30)
    next_line = 1
    line = 0
    for test in tests:
        if line != next_line:
            line = next_line
        if not test or test == '\n':
            continue
        next_line += len(test.split('\n')) - 1
        blocks = test.split('-' * 30 + '\n')
        if len(blocks) != 3:
            continue
        input, page, oneliner = blocks
        tc = WikiTestCase(input, page, file, line, setup, teardown, context)
        suite.addTest(tc)
        if oneliner:
            tc = OneLinerTestCase(input, oneliner[:-1], file, line,
                                  setup, teardown, context)
            suite.addTest(tc)
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
