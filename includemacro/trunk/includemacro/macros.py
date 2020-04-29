# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import urllib2
import re
from StringIO import StringIO

from genshi.filters.html import HTMLSanitizer
from genshi.input import HTMLParser, ParseError
from trac.core import TracError, implements
from trac.mimeview.api import Mimeview, get_mimetype
from trac.perm import IPermissionRequestor
from trac.resource import ResourceNotFound
from trac.ticket.model import Ticket
from trac.util import as_bool, as_int
from trac.util.html import escape
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.versioncontrol.api import NoSuchChangeset, NoSuchNode, \
    RepositoryManager
from trac.web.chrome import web_context
from trac.wiki.api import WikiSystem, parse_args
from trac.wiki.formatter import WikiParser, system_message
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage


class IncludeMacro(WikiMacroBase):
    """A macro to include other resources in wiki pages.

    More documentation to follow.
    """

    implements(IPermissionRequestor)

    # Default output formats for sources that need them.
    default_formats = {
        'wiki': 'text/x-trac-wiki',
    }

    # IWikiMacroProvider methods

    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args(content)
        if len(largs) == 1:
            largs.append(None)
        elif len(largs) != 2:
            return system_message('Invalid arguments "%s"' % content)

        # Pull out the arguments.
        source, dest_format = largs
        try:
            source_format, source_obj = source.split(':', 1)
        except ValueError:  # If no : is present, assume its a wiki page.
            source_format, source_obj = 'wiki', source

        # Apply a default format if needed.
        if dest_format is None:
            dest_format = self.default_formats.get(source_format)

        annotations = out = ctxt = None
        if source_format in ('http', 'https', 'ftp'):
            # Since I can't really do recursion checking, and because this
            # could be a source of abuse allow selectively blocking it.
            # RFE: Allow blacklist/whitelist patterns for URLS. <NPK>
            # RFE: Track page edits and prevent unauthorized users from ever
            #      entering an URL include. <NPK>
            if 'INCLUDE_URL' not in formatter.perm:
                self.log.info(
                    "IncludeMacro: Blocking attempt by %s to include URL %s "
                    "on page %s", formatter.req.authname, source,
                    formatter.req.path_info)
                return ''
            try:
                urlf = urllib2.urlopen(source)
                out = urlf.read()
            except urllib2.URLError, e:
                return system_message("Error while retrieving file", str(e))
            except TracError, e:
                return system_message("Error while previewing", str(e))
            ctxt = web_context(formatter.req)
        elif source_format == 'wiki':
            if '#' in source_obj:
                source_obj, source_section = source_obj.split('#', 1)
            else:
                source_obj, source_section = source_obj, None
            # XXX: Check for recursion in page includes. <NPK>
            page_name, page_version = _split_path(source_obj)
            # Relative link resolution adapted from Trac 1.1.2dev.
            # Hint: Only attempt this in wiki rendering context.
            if formatter.resource and formatter.resource.realm == 'wiki':
                referrer = formatter.resource.id
                ws = WikiSystem(self.env)
                if page_name.startswith('/'):
                    page_name = page_name.lstrip('/')
                elif page_name.startswith(('./', '../')) or \
                        page_name in ('.', '..'):
                    try:
                        # Trac 1.2
                        page_name = ws.resolve_relative_name(page_name,
                                                             referrer)
                    except AttributeError:
                        page_name = _resolve_relative_name(page_name,
                                                           referrer)
                else:
                    page_name = _resolve_scoped_name(ws, page_name, referrer)
            try:
                page = WikiPage(self.env, page_name, page_version)
            except (TypeError, ValueError):  # Trac < 1.2 (Trac:#11544)
                msg = _('"%(version)s" is not a valid wiki page version.',
                        version=page_version)
                return system_message(msg)
            except TracError, e:
                return system_message(e)
            if 'WIKI_VIEW' not in formatter.perm(page.resource):
                return ''
            if not page.exists:
                if page_version:
                    return system_message('No version "%s" for wiki page "%s"'
                                          % (page_version, page_name))
                else:
                    return system_message('Wiki page "%s" does not exist'
                                          % page_name)
            out = page.text
            if source_section:
                out = self._extract_section(out, source_section)
                if out is None:
                    return system_message(
                        'Section "%s" not found in wiki page "%s"'
                        % (source_section, page_name))
            ctxt = web_context(formatter.req, 'wiki', source_obj)
        elif source_format in ('source', 'browser', 'repos'):
            if 'FILE_VIEW' not in formatter.perm:
                return ''
            start = kwargs.get('start', 1)
            end = kwargs.get('end')
            lineno = as_bool(kwargs.get('lineno'))
            out, ctxt, dest_format, annotations = self._get_source(formatter, source_obj,
                                                                   dest_format, start, end, lineno)
        elif source_format == 'ticket':
            if ':' in source_obj:
                ticket_num, source_obj = source_obj.split(':', 1)
                if not Ticket.id_is_valid(ticket_num):
                    return system_message("%s is not a valid ticket id"
                                          % ticket_num)
                try:
                    ticket = Ticket(self.env, ticket_num)
                    if 'TICKET_VIEW' not in formatter.perm(ticket.resource):
                        return ''
                except ResourceNotFound:
                    return system_message("Ticket %s does not exist"
                                          % ticket_num)
                if ':' in source_obj:
                    source_format, comment_num = source_obj.split(':', 1)
                    if source_format == 'comment':
                        changelog = ticket.get_changelog()
                        out = []
                        if changelog:
                            for (ts, author, field, oldval, newval,
                                 permanent) in changelog:
                                if field == 'comment' and \
                                        oldval == comment_num:
                                    dest_format = 'text/x-trac-wiki'
                                    ctxt = web_context(formatter.req,
                                                       'ticket', ticket_num)
                                    out = newval
                                    break
                        if not out:
                            return system_message(
                                "Comment %s does not exist for Ticket %s"
                                % (comment_num, ticket_num))
                    else:
                        system_message("Unsupported ticket field %s"
                                       % source_format)
            else:
                return system_message('Ticket field must be specified')
        else:
            # RFE: Add ticket: and comment: sources. <NPK>
            # RFE: Add attachment: source. <NPK>
            return system_message('Unsupported realm %s' % source)

        # If we have a preview format, use it.
        if dest_format:
            out = Mimeview(self.env).render(ctxt, dest_format, out, '', None, annotations)

        # Escape if needed.
        if not self.config.getbool('wiki', 'render_unsafe_content', False):
            out = to_unicode(out)
            try:
                out = HTMLParser(StringIO(out)).parse() | HTMLSanitizer()
            except ParseError:
                out = escape(out)

        return out

    # IPermissionRequestor methods

    def get_permission_actions(self):
        yield 'INCLUDE_URL'

    # Private methods

    def _handle_partial_source(self, src, start, end):
        # we want to only show a certain number of lines, so we
        # break the source into lines and set our numbers for 1-based
        # line numbering.
        lines = src.split('\n')
        linecount = len(lines)

        start_regex = False
        start = as_int(start, start)
        if isinstance(start, basestring):
            start = start.strip("'\"")
            start_regex = True
            match = re.search(start, src, re.M)
            if match:
                start = src.count('\n', 0, match.start())
            else:
                raise ParseError('start regexp "%s" does not match any text' % start)

        if end:
            end = as_int(end, end)
            if isinstance(end, basestring):
                end = end.strip("'\"")
                src2 = '\n'.join(lines[start+1:linecount])
                match = re.search(end, src2, re.M)
                if match:
                    end = start + src2.count('\n', 0, match.start())
                else:
                    raise ParseError('end regexp "%s" does not match any text' % end)
            else:
                if start_regex:
                    end += start
        else:
            end = linecount
        src = lines[start - 1:end]

        # calculate actual startline for display purposes
        if start < 0:
            start = linecount + start

        return '\n'.join(src), start, end

    def _get_source(self, formatter, source_obj, dest_format, start, end, lineno):
        repos_mgr = RepositoryManager(self.env)
        repos_name, repos, source_obj = \
            repos_mgr.get_repository_by_path(source_obj)
        path, rev = _split_path(source_obj)
        try:
            node = repos.get_node(path, rev)
        except (NoSuchChangeset, NoSuchNode), e:
            return system_message(e), None, None, None
        content = node.get_content()
        out = ''
        ctxt = None
        annotations = None
        if content:
            out = content.read()
            if dest_format is None:
                dest_format = node.content_type or get_mimetype(path, out)
            try:
                out, start, end = self._handle_partial_source(out, start, end)
            except ParseError as e:
                return system_message(e), None, None, None
            annotations = lineno and ['lineno'] or None

            ctxt = web_context(formatter.req, 'source', path)
            ctxt.set_hints(lineno=start)

        return out, ctxt, dest_format, annotations

    def _extract_section(self, text, section):
        m1 = re.search("(^\s*(?P<heading>={1,6})\s(.*?)(\#%s)\s*$)" % section,
                       text, re.MULTILINE)
        if m1:
            stext = text[m1.end(0):]
            m2 = re.search("(^\s*%s\s(.*?)(\#%s)?\s*$)"
                           % (m1.group('heading'), WikiParser.XML_NAME),
                           stext, re.MULTILINE)
            if m2:
                return stext[:m2.start(0)]
            else:
                return stext


def _resolve_relative_name(page_name, referrer):
    base = referrer.split('/')
    components = page_name.split('/')
    for i, comp in enumerate(components):
        if comp == '..':
            if base:
                base.pop()
        elif comp != '.':
            base.extend(components[i:])
            break
    return '/'.join(base)


def _resolve_scoped_name(wiki_sys, page_name, referrer):
    referrer = referrer.split('/')
    if len(referrer) == 1:           # Non-hierarchical referrer
        return page_name
    # Test for pages with same name, higher in the hierarchy.
    for i in range(len(referrer) - 1, 0, -1):
        name = '/'.join(referrer[:i]) + '/' + page_name
        if wiki_sys.has_page(name):
            return name
    if wiki_sys.has_page(page_name):
        return page_name
    # If we are on First/Second/Third, and pagename is Second/Other,
    # resolve to First/Second/Other instead of First/Second/Second/Other
    # See http://trac.edgewall.org/ticket/4507#comment:12
    if '/' in page_name:
        (first, rest) = page_name.split('/', 1)
        for (i, part) in enumerate(referrer):
            if first == part:
                anchor = '/'.join(referrer[:i + 1])
                if wiki_sys.has_page(anchor):
                    return anchor + '/' + rest
    # Assume the user wants a sibling of referrer.
    return '/'.join(referrer[:-1]) + '/' + page_name


def _split_path(source_obj):
    if '@' in source_obj:
        path, rev = source_obj.split('@', 1)
    else:
        path, rev = source_obj, None
    return path, rev
