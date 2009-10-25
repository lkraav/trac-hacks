""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $URL$

    This is Free Software under the BSD license.

    Contributors:
    Joshua Hoke <joshua.hoke@sixnet.com>: Patch for PageOutline Support (th:#4521)

    The regexes XML_NAME (unchanged) and NUM_HEADLINE (added 'n'-prefix for all
    names) were taken from trac.wiki.parser and the base code of method
    `_parse_heading` was taken from trac.wiki.formatter which are:
        Copyright (C) 2003-2008 Edgewall Software
        All rights reserved.
    See http://trac.edgewall.org/wiki/TracLicense for details.

"""
from genshi.builder import tag
from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.formatter import format_to_oneliner
from genshi.util import plaintext
from trac.wiki.parser import WikiParser
from trac.config import BoolOption

from weakref import WeakKeyDictionary
import re


class NumberedHeadlinesPlugin(Component):
    """ Trac Plug-in to provide Wiki Syntax and CSS file for numbered headlines.
    """
    implements(IRequestFilter,ITemplateProvider,IWikiSyntaxProvider)
    number_outline = BoolOption('numberedheadlines','numbered_outline',True,
        "Whether or not to number the headlines in an outline (e.g. TOC)")
    use_css = BoolOption('numberedheadlines','use_css_for_numbering',True,
        "Whether or not to number the headlines using CSS styles (e.g.  TOC)")
    startatleveltwo = BoolOption('numberedheadlines','numbering_starts_at_level_two',
        False, """Whether or not to start the numbering at level two instead at 
        level one.""")

    XML_NAME = r"[\w:](?<!\d)[\w:.-]*?" # See http://www.w3.org/TR/REC-xml/#id 

    NUM_HEADLINE = \
        r"(?P<nheading>^\s*(?P<nhdepth>#+)\s.*\s(?P=nhdepth)\s*" \
        r"(?P<nhanchor>=%s)?(?:\s|$))" % XML_NAME

    outline_counters = WeakKeyDictionary()

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('numberedheadlines', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if self.use_css:
          if self.startatleveltwo:
            add_stylesheet (req, 'numberedheadlines/style2.css')
          else:
            add_stylesheet (req, 'numberedheadlines/style.css')
        return (template, data, content_type)


    # IWikiSyntaxProvider methods
    def _parse_heading(self, formatter, match, fullmatch):
        shorten = False
        match = match.strip()

        depth = min(len(fullmatch.group('nhdepth')), 6)

        ## BEGIN of code provided by Joshua Hoke, see th:#4521.
        # moved and modified by Martin

        # Figure out headline numbering for outline
        counters = self.outline_counters.get(formatter, [])

        if formatter not in self.outline_counters:
            self.outline_counters[formatter] = counters

        if len(counters) < depth:
            delta = depth - len(counters)
            counters.extend([0] * (delta - 1))
            counters.append(1)
        else:
            del counters[depth:]
            counters[-1] += 1
        ## END

        anchor = fullmatch.group('nhanchor') or ''
        heading_text = match[depth+1:-depth-1-len(anchor)]
        heading = format_to_oneliner(formatter.env, formatter.context, 
            heading_text, False)

        if anchor:
            anchor = anchor[1:]
        else:
            sans_markup = plaintext(heading, keeplinebreaks=False)
            anchor = WikiParser._anchor_re.sub('', sans_markup)
            if not anchor or anchor[0].isdigit() or anchor[0] in '.-':
                # an ID must start with a Name-start character in XHTML
                anchor = 'a' + anchor # keeping 'a' for backward compat
        i = 1
        anchor_base = anchor
        while anchor in formatter._anchors:
            anchor = anchor_base + str(i)
            i += 1
        formatter._anchors[anchor] = True

        # Add number directly if CSS is not used
        s = self.startatleveltwo and 1 or 0
        #self.env.log.debug('NHL:' + str(counters))
        while s < len(counters) and counters[s] == 0:
          s = s + 1
        num_heading_text = '.'.join(map(str, counters[s:]) + [" "]) + heading_text

        if self.number_outline:
          oheading_text = num_heading_text
        else:
          oheading_text = heading_text

        if not self.use_css:
          heading_text  = num_heading_text

        heading = format_to_oneliner(formatter.env, formatter.context, 
            heading_text, False)
        oheading = format_to_oneliner(formatter.env, formatter.context, 
            oheading_text, False)

        ## BEGIN of code provided by Joshua Hoke, see th:#4521.
        # modified by Martin

        # Strip out link tags
        oheading = re.sub(r'</?a(?: .*?)?>', '', oheading)

        try:
            # Add heading to outline
            formatter.outline.append((depth, anchor, oheading))
        except AttributeError:
            # Probably a type of formatter that doesn't build an
            # outline.
            pass
        ## END of provided code

        cssclass = self.use_css and 'numbered' or ''

        return tag.__getattr__('h' + str(depth))( heading,
                    class_ = cssclass,
                    id = anchor
              )

    def get_wiki_syntax(self):
        yield ( self.NUM_HEADLINE , self._parse_heading )

    def get_link_resolvers(self):
        return []

