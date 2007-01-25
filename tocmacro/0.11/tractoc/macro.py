# -*- coding: utf-8 -*-
import os
import re

from genshi.core import Markup
from genshi.builder import tag

from trac.core import *
from trac.wiki.formatter import OutlineFormatter, system_message
from trac.wiki.api import WikiSystem, parse_args
from trac.wiki.macros import WikiMacroBase 


__all__ = ['TOCMacro']

class NullOut(object):
    def write(self, *args): pass


def outline_tree(outline, context, active, min_depth, max_depth):
    if min_depth > max_depth:
        min_depth, max_depth = max_depth, min_depth
    max_depth = min(6, max_depth)
    min_depth = max(1, min_depth)
    previous_depth = min_depth
    
    stack = [None] * max_depth
    stack[previous_depth] = tag.ol()
    
    for depth, anchor, heading in outline:
        if min_depth <= depth <= max_depth:
            for d in range(previous_depth, depth):
                stack[d+1] = ol = tag.ol()
                stack[d].append(tag.li(ol))
            href = context.self_href() + '#' + anchor
            stack[depth].append(tag.li(tag.a(Markup(heading), href=href),
                                       class_=active and 'active' or None))
            previous_depth = depth
    return stack[min_depth]


class TOCMacro(WikiMacroBase):
    """
    Generate a table of contents for the current page or a set of pages.
    If no arguments are given, a table of contents is generated for the
    current page, with the top-level title stripped: 
    {{{
        [[TOC]]
    }}}
    To generate a table of contents for a set of pages, simply pass them
    as comma separated arguments to the TOC macro, e.g. as in
    {{{
    [[TOC(TracGuide, TracInstall, TracUpgrade, TracIni, TracAdmin, TracBackup,
          TracLogging, TracPermissions, TracWiki, WikiFormatting, TracBrowser,
          TracRoadmap, TracChangeset, TracTickets, TracReports, TracQuery,
          TracTimeline, TracRss, TracNotification)]]
    }}}
    The following ''control'' arguments change the default behaviour of
    the TOC macro: 
    || '''Argument'''    || '''Meaning''' ||
    || {{{heading=<x>}}} || Override the default heading of "Table of Contents" ||
    || {{{noheading}}}   || Suppress display of the heading. ||
    || {{{depth=<n>}}}   || Display headings of ''subsequent'' pages to a maximum depth of '''<n>'''. ||
    || {{{inline}}}      || Display TOC inline rather than as a side-bar. ||
    || {{{titleindex}}}  || Only display the page name and title of each page, similar to TitleIndex. ||
    
    Note that the current page must also be specified if individual wiki
    pages are given in the argument list.
    """
    
    def expand_macro(self, formatter, name, args):
        db = formatter.db
        context = formatter.context
        
        # Bail out if we are in a no-float zone
        if hasattr(formatter, 'properties') and \
               'macro_no_float' in formatter.properties:
            return ''
        
        current_page = context.id
         
        def get_page_text(pagename):
            """Return a tuple of `(text, exists)` for the given `pagename`."""
            if pagename == current_page:
                return (formatter.source, True)
            else:
                # TODO: after sandbox/security merge
                # page = context(id=pagename).resource
                from trac.wiki.model import WikiPage
                page = WikiPage(self.env, pagename, db=db)
                return (page.text, page.exists)
                
        # Split the args
        args, kw = parse_args(args)
        # Options
        inline = False
        pagenames = []
        heading = kw.pop('heading', 'Table of Contents')
        root = kw.pop('root', '')
        
        params = {'title_index': False, 'min_depth': 1, 'max_depth': 6}
        # Global options
        for arg in args:
            arg = arg.strip()
            if arg == 'inline':
                inline = True
            elif arg == 'noheading':
                heading = ''
            elif arg == 'notitle':
                params['min_depth'] = 2     # Skip page title
            elif arg == 'titleindex':
                params['title_index'] = True
                heading = ''
            elif arg == 'nofloat':
                return ''
            elif arg != '':
                pagenames.append(arg)

        if 'depth' in kw:
           params['max_depth'] = int(kw['depth'])

        # Has the user supplied a list of pages?
        if not pagenames:
            pagenames.append(current_page)
            root = ''
            params['min_depth'] = 2     # Skip page title

        base = inline and tag() or tag.div(class_='wiki-toc')
        if heading:
            base.append(tag.h4(heading))

        for pagename in pagenames:
            if params['title_index']:
                active = pagename.startswith(current_page)
                prefix = pagename.split('/')[0]
                prefix = prefix.replace("'", "''")
                all_pages = list(WikiSystem(self.env).get_pages(prefix))
                if all_pages:
                    all_pages.sort()
                    ol = tag.ol()
                    for page in all_pages:
                        ctx = context('wiki', page)
                        fmt = OutlineFormatter(ctx)
                        page_text, _ = get_page_text(page) # ctx.resource.text
                        fmt.format(page_text, NullOut())
                        title = ''
                        if fmt.outline:
                            title = ': ' + fmt.outline[0][2]
                        ol.append(tag.li(tag.a(page, href=ctx.self_href()),
                                         Markup(title),
                                         class_= active and 'active' or None))
                    base.append(ol)
                else:
                    base.append(system_message('Error: No page matching %s '
                                               'found' % prefix))
            else:
                page = root + pagename
                page_text, page_exists = get_page_text(page)
                if page_exists:
                    ctx = context('wiki', page)
                    fmt = OutlineFormatter(ctx)
                    fmt.format(page_text, NullOut())
                    base.append(outline_tree(fmt.outline, ctx,
                                             page == current_page,
                                             params['min_depth'],
                                             params['max_depth']))
                else:
                    base.append(system_message('Error: Page %s does not exist' %
                                               pagename))
        return base
