# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2011 Mikael Relbe <mikael@relbe.se>
# All rights reserved.
#
# Parts of this code (smileys) are
# Copyright (C) 2006 Christian Boos <cboos@neuf.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Christian Boos <cboos@neuf.fr>
#         Mikael Relbe <mikael@relbe.se>

"""Decorate wiki pages with a huge set of modern icons.

More than 3.000 icons are available using the wiki markup `(|name, size|)`, or
the equivalent `Icon` macro, and as smileys. Smiley character sequences are
defined in the `[wikiextras-smileys]` section in `trac.ini`. The icon library
contains two sets of icons, shadowed and shadowless. Which set to use is
defined in the `[wikiextras]` section in `trac.ini`.

'''Icon Library License Terms'''

The icon library contained herein is composed of the
[http://p.yusukekamiyamane.com Fugue icon library] with additional icons, and
can be used for any commercial or personal projects, but you may not lease,
license or sublicense the icons.

The [http://p.yusukekamiyamane.com Fugue icon library] is released under
[http://creativecommons.org/licenses/by/3.0/ Creative Commons Attribution 3.0 license].
[[BR]]
Some icons are Copyright (C) [http://p.yusukekamiyamane.com/ Yusuke Kamiyamane].
All rights reserved.

Additional icons are released under same
[http://trac.edgewall.org/wiki/TracLicense license terms] as Trac.
[[BR]]
Some icons are Copyright (C) [http://www.edgewall.org Edgewall Software].
All rights reserved.
"""

import fnmatch
import os
import re

from inspect import cleandoc

from pkg_resources import resource_filename

from genshi.builder import tag

from trac.config import BoolOption, ConfigSection, IntOption, ListOption
from trac.core import implements, Component
from trac.web.chrome import ITemplateProvider
from trac.wiki import IWikiMacroProvider, IWikiSyntaxProvider, format_to_html

from tracwikiextras.util import prepare_regexp, reduce_names, render_table


SIZE_DESCR = {'S': 'small', 'M': 'medium-sized', 'L': 'large'}

FUGUE_ICONS = {
    False: { # with shadow
        'S': ('wikiextras-icons-16',
              resource_filename(__name__, 'htdocs/icons/fugue/icons')),
        'M': ('wikiextras-icons-24',
              resource_filename(__name__,
                                'htdocs/icons/fugue/bonus/icons-24')),
        'L': ('wikiextras-icons-32',
              resource_filename(__name__,
                                'htdocs/icons/fugue/bonus/icons-32')),
    },
    True: { # shadowless
        'S': ('wikiextras-icons-shadowless-16',
              resource_filename(__name__,
                                'htdocs/icons/fugue/icons-shadowless')),
        'M': ('wikiextras-icons-shadowless-24',
              resource_filename(
                  __name__, 'htdocs/icons/fugue/bonus/icons-shadowless-24')),
        'L': ('wikiextras-icons-shadowless-32',
              resource_filename(
                  __name__, 'htdocs/icons/fugue/bonus/icons-shadowless-32')),
    },
}



class Icons(Component):
    """Display icons in lined with text.

    The wiki markup `(|name|)`, or the equivalent `Icon` macro, shows a named
    icon that can be in line with text. During side-by-side wiki editing, the
    same wiki markup, or macro, can be used as a temporary search facility to
    find icons in the vast library. The number of icons presented to the wiki
    author can be limited to prevent exhaustive network traffic. This limit is
    defined in the `[wikiextras]` section in `trac.ini`.
    """

    implements(ITemplateProvider, IWikiMacroProvider, IWikiSyntaxProvider)

    icon_limit = IntOption('wikiextras', 'icon_limit', 32,
        """To prevent exhaustive network traffic, limit the maximum number of
        icons generated by the macro `Icon`. Set to 0 for unlimited number of
        icons (this will produce exhaustive network traffic--you have been
        warned!)""")

    shadowless = BoolOption('wikiextras', 'shadowless_icons', 'false',
                            'Use shadowless icons.')

    def icon_location(self, size='S'):
        """ Returns `(prefix, abspath)` tuple based on `size` which is one
        of `small`, `medium` or `large` (or an abbreviation thereof..

        The `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        try:
            return FUGUE_ICONS[self.shadowless][size[0].upper()]
        except Exception:
            return FUGUE_ICONS[self.shadowless]['S']

    def _render_icon(self, formatter, name, size):
        if not name:
            return
        size = size.upper()[0] if size else 'S'
        name = name.lower()
        if any(x in name for x in ['*', '?']):
            #noinspection PyArgumentList
            return ShowIcons(self.env)._render(
                    formatter, 2, name, size, True, self.icon_limit)
        else:
            loc = self.icon_location(size)
            return tag.img(src=formatter.href.chrome(loc[0], name + '.png'),
                           alt=name, style="vertical-align: text-bottom")

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        dirs = []
        for data in FUGUE_ICONS.itervalues():
            for d in data.itervalues():
                dirs.append(tuple(d))
        return dirs

    def get_templates_dirs(self):
        return []

    # IWikiSyntaxProvider methods

    wiki_pat = r'!?\(\|([-*?._a-z0-9]+)(?:,\s*(\w*))?\|\)'
    wiki_re = re.compile(wiki_pat)

    #noinspection PyUnusedLocal
    def _format_icon(self, formatter, match, fullmatch=None):
        m = Icons.wiki_re.match(match)
        name, size = m.group(1, 2)
        return self._render_icon(formatter, name, size)

    def get_wiki_syntax(self):
        yield (Icons.wiki_pat, self._format_icon)

    def get_link_resolvers(self):
        return []

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'Icon'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        return cleandoc("""Shows a named icon that can be in line with text.

                Syntax:
                {{{
                [[Icon(name, size)]]
                }}}
                where
                 * `name` is the name of the icon.  When `name` contains a
                   pattern character (`*` or `?`), a 2-column preview of
                   matching icons is presented, which should mainly be used for
                   finding and selecting an icon during wiki page editing in
                   side-by-side mode (however, no more than %d icons are
                   presented to prevent exhaustive network traffic.)
                 * `size` is optionally one of `small`, `medium` or `large` or
                   an abbreviation thereof (defaults `small`).

                Example:
                {{{
                [[Icon(smiley)]]
                }}}

                Use `ShowIcons` for static presentation of available icons.
                Smileys like `:-)` are automatically rendered as icons. Use
                `ShowSmileys` to se all available smileys.

                Following wiki markup is equivalent to using this macro:
                {{{
                (|name, size|)
                }}}
                """ % self.icon_limit)

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content):
        # content = name, size
        if not content:
            return
        args = [a.strip() for a in content.split(',')] + [None, None]
        name, size = args[0], args[1]
        return self._render_icon(formatter, name, size)


class ShowIcons(Component):
    """Macro to list available icons on a wiki page.

    The `ShowIcons` macro displays a table of available icons, matching a
    search criteria. The number of presented icons can be limited to prevent
    exhaustive network traffic. This limit is defined in the `[wikiextras]`
    section in `trac.ini`.
    """

    implements(ITemplateProvider, IWikiMacroProvider)

    showicons_limit = IntOption('wikiextras', 'showicons_limit', 96,
        """To prevent exhaustive network traffic, limit the maximum number of
        icons generated by the macro `ShowIcons`. Set to 0 for
        unlimited number of icons (this will produce exhaustive network
        traffic--you have been warned!)""")

    def _render(self, formatter, cols, name_pat, size, header, limit):
        #noinspection PyArgumentList
        icon = Icons(self.env)
        icon_dir = icon.icon_location(size)[1]
        files = fnmatch.filter(os.listdir(icon_dir), name_pat + '.png')
        icon_names = [os.path.splitext(p)[0] for p in files]
        if limit:
            displayed_icon_names = reduce_names(icon_names, limit)
        else:
            displayed_icon_names = icon_names
        icon_table = render_table(displayed_icon_names, cols,
                                  lambda name: icon._render_icon(formatter,
                                                                 name, size))
        if not len(icon_names):
            message = 'No %s icon matches %s' % (SIZE_DESCR[size], name_pat)
        elif len(icon_names) == 1:
            message = 'Showing the only %s icon matching %s' % \
                      (SIZE_DESCR[size], name_pat)
        elif len(displayed_icon_names) == len(icon_names):
            message = 'Showing all %d %s icons matching %s' % \
                      (len(icon_names), SIZE_DESCR[size], name_pat)
        else:
            message = 'Showing %d of %d %s icons matching %s' % \
                      (len(displayed_icon_names), len(icon_names),
                       SIZE_DESCR[size], name_pat)
        return tag.div(tag.p(tag.small(message)) if header else '', icon_table)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return []

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowIcons'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        #noinspection PyStringFormat
        return cleandoc("""Renders in a table a list of available icons.
                No more than %(showicons_limit)d icons are displayed to prevent
                exhaustive network traffic.

                Syntax:
                {{{
                [[ShowIcons(cols, name-pattern, size, header, limit)]]
                }}}
                where
                 * `cols` is optionally the number of columns in the table
                   (defaults 3).
                 * `name-pattern` selects which icons to list (use `*` and
                   `?`).
                 * `size` is optionally one of `small`, `medium` or `large` or
                   an abbreviation thereof (defaults `small`).
                 * `header` is optionally one of `header` and `noheader` or
                   an abbreviation thereof (header is displayed by default)
                 * `limit` specifies an optional upper limit of number of
                   displayed icons (however, no more than %(showicons_limit)d
                   will be displayed).

                The last three optional parameters (`size`, `header` and
                `limit`) can be stated in any order.

                Example:

                {{{
                [[ShowIcons(smile*)]]              # all small icons matching smile*
                [[ShowIcons(4, smile*)]]           # four columns
                [[ShowIcons(smile*, 10)]]          # limit to 10 icons
                [[ShowIcons(smile*, 10, nohead)]]  # no header
                [[ShowIcons(smile*, m)]]           # medium-size
                }}}
                """ % {'showicons_limit': self.showicons_limit})

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        # content = cols, name-pattern, size, header, limit
        args = []
        if content:
            args = [a.strip() for a in content.split(',')]
        args += [''] * 2
        a = args.pop(0)
        # cols
        if a.isdigit():
            cols = max(int(a), 1)
            a = args.pop(0)
        else:
            cols = 3
        # name_pat
        name_pat = a
        if not name_pat:
            name_pat = '*'
        # size, header and limit
        size = 'S'
        header = True
        limit = self.showicons_limit
        while args:
            a = args.pop(0).lower()
            if a.isdigit():
                limit = min(int(a), limit)
            elif a and any(d.startswith(a) for d in SIZE_DESCR.values()):
                size = a.upper()[0]
            elif a and any(d.startswith(a) for d in ['header', 'noheader']):
                header = a[0].startswith('h')
        return self._render(formatter, cols, name_pat, size, header, limit)

SMILEYS = {
    ':)': 'smiley.png',
    ':-)': 'smiley.png',
    '=)': 'smiley.png',
    ';-)': 'smiley-wink.png',
    ';)': 'smiley-wink.png',
    ':(': 'smiley-sad.png',
    ':-(': 'smiley-sad.png',
    ':|': 'smiley-neutral.png',
    ':-|': 'smiley-neutral.png',
    ':-?': 'smiley-confuse.png',
    ':?': 'smiley-confuse.png',
    ':D': 'smiley-lol.png',
    ':-D': 'smiley-lol.png',
    ':))': 'smiley-grin.png',
    ':-))': 'smiley-grin.png',
    ':-P': 'smiley-razz.png',
    ':P': 'smiley-razz.png',
    ':-O': 'smiley-red.png',
    ':O': 'smiley-red.png',
    ':-o': 'smiley-surprise.png',
    ':o': 'smiley-surprise.png',
    ':-X': 'smiley-zipper.png',
    ':X': 'smiley-zipper.png',
    'B-)': 'smiley-cool.png',
    '8-)': 'smiley-nerd.png',
    'B-O': 'smiley-eek.png',
    '8-O': 'smiley-eek.png',
    '>:>': 'smiley-evil.png',

    '(!)': 'exclamation-red.png',
    '(?)': 'question.png',
    '(I)': 'light-bulb.png',
    '(*)': 'asterisk.png',
    '(X)': 'cross-circle.png',

    '(Y)': 'thumb-up.png',
    '(OK)': 'thumb-up.png',
    '(N)': 'thumb.png',
    '(NOK)': 'thumb.png',

    '(./)': 'tick.png',
}


class Smileys(Component):
    """Replace smiley characters like `:-)` with icons.

    Smiley characters and icons are configurable in the `[wikiextras-smileys]`
    section in `trac.ini`. Use the `ShowSmileys` macro to display a list of
    currently defined smileys.
    """

    implements(IWikiMacroProvider, IWikiSyntaxProvider)

    smileys_section = ConfigSection('wikiextras-smileys',
            """The set of smileys is configurable by providing associations
            between icon names and wiki keywords. A default set of icons and
            keywords is defined, which can be revoked one-by-one (_remove) or
            all at once (_remove_defaults).

            Example:
            {{{
            [wikiextras-smileys]
            _remove_defaults = true
            _remove = :-( :(
            smiley = :-) :)
            smiley-wink = ;-) ;)
            clock = (CLOCK) (TIME)
            calendar-month = (CALENDAR) (DATE)
            chart = (CHART)
            document-excel = (EXCEL)
            document-word = (WORD)
            eye = (EYE)
            new = (NEW)
            tick = (TICK)
            }}}

            Keywords are space-separated!

            A smiley can also be removed by associating its icon with nothing:
            {{{
            smiley =
            }}}

            Use the `ShowSmileys` macro to find out the current set of icons
            and keywords.
            """)

    remove_defaults = BoolOption('wikiextras-smileys', '_remove_defaults',
                                 False, doc="Set to true to remove all "
                                            "default smileys.")

    remove = ListOption('wikiextras-smileys', '_remove', sep=' ', doc="""\
            Space-separated(!) list of keywords that shall not be interpreted
            as smileys (even if defined in this section).""")

    def __init__(self):
        self.smileys = None

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        if self.smileys is None:
            self.smileys = SMILEYS.copy()
            if self.remove_defaults:
                self.smileys = {}
            for icon_name, value in self.smileys_section.options():
                if not icon_name.startswith('_remove'):
                    icon_file = icon_name
                    if not icon_file.endswith('.png'):
                        icon_file += '.png'
                    if value:
                        for keyword in value.split():
                            self.smileys[keyword.strip()] = icon_file
                    else:
                        # no keyword, remove all smileys associated with icon
                        for k in self.smileys.keys():
                            if self.smileys[k] == icon_file:
                               del self.smileys[k]
            for keyword in self.remove:
                if keyword in self.smileys:
                    del self.smileys[keyword]

        if self.smileys:
            yield (r"(?<!\w)!?(?:%s)" % prepare_regexp(self.smileys),
                   self._format_smiley)
        else:
            yield (None, None)

    def get_link_resolvers(self):
        return []

    #noinspection PyUnusedLocal
    def _format_smiley(self, formatter, match, fullmatch=None):
        #noinspection PyArgumentList
        loc = Icons(self.env).icon_location()
        return tag.img(src=formatter.href.chrome(loc[0], self.smileys[match]),
                       alt=match, style="vertical-align: text-bottom")

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowSmileys'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        return cleandoc("""Renders in a table the list of available smileys.
                Optional argument is the number of columns in the table
                (defaults 3).

                Comment: Prefixing a character sequence with `!` prevents it
                from being interpreted as a smiley.
                """)

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        # Merge smileys for presentation
        # First collect wikitexts for each unique filename
        syelims = {} # key=filename, value=wikitext
        for wikitext, filename in self.smileys.iteritems():
            if filename not in syelims:
                syelims[filename] = [wikitext]
            else:
                syelims[filename].append(wikitext)
        # Reverse
        smileys = {}
        for filename, wikitexts in syelims.iteritems():
            wikitexts.sort()
            smileys[' '.join(wikitexts)] = filename
        return render_table(smileys.keys(), content,
                            lambda s: self._format_smiley(formatter,
                                                          s.split(' ', 1)[0]))


class AboutWikiIcons(Component):
    """Macro for displaying a wiki page on how to use icons and smileys.

    Create a wiki page `WikiIcons` and insert the following line to show
    detailed instructions to wiki authors on how to use icons and smileys in
    wiki pages:
    {{{
    [[AboutWikiIcons]]
    }}}
    """

    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'AboutWikiIcons'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        return "Display a wiki page on how to use icons."

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        help_file = resource_filename(__name__, 'doc/WikiIcons')
        fd = open(help_file, 'r')
        wiki_text = fd.read()
        fd.close()
        return format_to_html(self.env, formatter.context, wiki_text)
