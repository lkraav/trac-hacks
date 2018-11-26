# -*- coding: utf-8 -*-

from __future__ import with_statement

import pkg_resources
import re

from trac.core import Component, TracError, implements
from trac.attachment import Attachment
from trac.mimeview.api import Mimeview
from trac.resource import Resource
from trac.ticket.model import MilestoneCache, Ticket
from trac.util import lazy
from trac.util.text import to_unicode
from trac.util.translation import dgettext
from trac.versioncontrol.api import RepositoryManager
from trac.web import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_script_data, add_stylesheet, web_context
from trac.wiki.api import WikiSystem
from trac.wiki.interwiki import InterWikiMap
from trac.wiki.formatter import format_to_html, format_to_oneliner


try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        json = None
if json:
    def to_json(data):
        return json.dumps(data)
else:
    def to_json(data):
        from trac.util.presentation import to_json
        text = to_json(data)
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        return text


class WikiAutoCompleteModule(Component):
    """Auto-completes wiki formatting."""

    implements(IRequestFilter, IRequestHandler, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template:
            script_data = {
                'url': req.href('wikiautocomplete'),
                'strategies': self._get_strategies(),
            }
            context_or_page = data.get('context') or data.get('page')
            if (context_or_page and hasattr(context_or_page, 'resource')
                and context_or_page.resource):
                script_data['realm'] = context_or_page.resource.realm
                script_data['id'] = context_or_page.resource.id
            add_script_data(req, {'wikiautocomplete': script_data})
            add_script(req, 'wikiautocomplete/js/jquery.textcomplete.min.js')
            add_script(req, 'wikiautocomplete/js/wikiautocomplete.js')
            add_stylesheet(req, 'wikiautocomplete/css/jquery.textcomplete.css')
        return template, data, content_type

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/wikiautocomplete/(.+)$', req.path_info)
        if match:
            req.args['strategy'] = match.group(1)
            return True

    def process_request(self, req):
        strategy = req.args.get('strategy')
        term = req.args.get('q', '')
        if strategy == 'linkresolvers':
            completions = self._suggest_linkresolvers(req)
        elif strategy == 'ticket':
            completions = self._suggest_ticket(req, term)
        elif strategy == 'wikipage':
            completions = self._suggest_wikipage(req)
        elif strategy == 'attachment':
            completions = self._suggest_attachment(req, term)
        elif strategy == 'macro':
            completions = self._suggest_macro(req)
        elif strategy == 'processor':
            completions = self._suggest_processor(req)
        elif strategy == 'source':
            completions = self._suggest_source(req, term)
        elif strategy == 'milestone':
            completions = self._suggest_milestone(req)
        elif strategy == 'report':
            completions = self._suggest_report(req)
        else:
            completions = None
        if completions is None:
            raise TracError('Invalid operation: %r, %r' % (strategy, term))
        else:
            self._send_json(req, completions)

    def _get_strategies(self):
       return [
            { # Processors
                "match": r"^(\s*\{{3}#!)(.*)(?!\n)$",
                "match_flags": 'm',
                "name": 'processor',
                "index": 2,
                "replace_prefix": '$1',
                "cache": True,
            },

            { # Attachment
                "match": r"(\b(?:raw-)?attachment:|\[\[Image\()(\S*)$",
                "name": 'attachment',
                "index": 2,
                "quote_whitespace": True,
                "replace_prefix": '$1',
                "cache": False,
            },

            { # TracLinks, InterTrac and InterWiki
                "match": r"(^|[^[])\[(\w*)$",
                "name": 'linkresolvers',
                "index": 2,
                "replace_prefix": '$1[',
                "replace_suffix": ':',
                "replace_end": ']',
                "cache": True,
            },

            { # Tickets
                "match": r"((?:^|[^{])#|\bticket:|\bbug:|\bissue:)(\d*)$",
                "name": 'ticket',
                "index": 2,
                "template_prefix": '#',
                "replace_prefix": '$1',
                "cache": False,
            },

            { # Wiki pages
                "match": r"\bwiki:(\S*)$",
                "name": 'wikipage',
                "index": 1,
                "quote_whitespace": True,
                "replace_prefix": 'wiki:',
                "cache": True,
            },

            { # Macros
                "match": r"\[\[(\w*)(?:\(([^)]*))?$",
                "name": 'macro',
                "index": 1,
                "replace_prefix": '[[',
                "replace_suffix": '($2',
                "replace_end": ')]]',
                "cache": True,
            },

            { # Source
                "match": r"\b(source:|browser:|repos:|log:|export:)([^@\s]*(?:@\S*)?)$",
                "name": 'source',
                "index": 2,
                "replace_prefix": '$1',
                "cache": False,
            },

            { # Milestone
                "match": r"\bmilestone:(\S*)$",
                "name": 'milestone',
                "index": 1,
                "quote_whitespace": True,
                "replace_prefix": 'milestone:',
                "cache": True,
            },

            { # Report - {\d+}
                "match": r"(^|[^{])\{(\d*)$",
                "name": 'report',
                "index": 2,
                "template_prefix": '{',
                "template_suffix": '}',
                "replace_prefix": '$1{',
                "replace_end": '}',
                "cache": True,
            },

            { # Report - report:\d+
                "match": r"\breport:(\d*)$",
                "name": 'report',
                "index": 1,
                "template_prefix": '{',
                "template_suffix": '}',
                "replace_prefix": 'report:',
                "cache": True,
            }
        ]

    def _suggest_linkresolvers(self, req):
        links = {}
        links.update((name, (2, name, url, title))
                     for name, url, title
                     in InterWikiMap(self.env).interwiki_map.itervalues())
        links.update((name, (1, name, url, title))
                     for name, url, title in self._get_intertracs())
        links.update((name, (0, name, None, None))
                     for provider in WikiSystem(self.env).syntax_providers
                     for name, resolver in provider.get_link_resolvers())
        return [{'value': name, 'title': title if name != title else url}
                for order, name, url, title
                in sorted(links.itervalues(),
                          key=lambda item: (item[0], item[1]))]

    def _suggest_ticket(self, req, term):
        args = self._get_num_ranges(term, Ticket.id_is_valid)
        if args:
            expr = ' OR '.join(['id>=%s AND id<%s'] * (len(args) / 2))
            rows = self.env.db_query("""
                SELECT id, summary FROM ticket
                WHERE %(expr)s
                ORDER BY changetime DESC
                LIMIT 100
                """ % {'expr': expr}, args)
        else:
            rows = self.env.db_query("""
                SELECT id, summary FROM ticket
                ORDER BY changetime DESC
                LIMIT 100
                """)
        return [{'value': row[0], 'title': row[1]}
                for row in rows if 'TICKET_VIEW' in req.perm('ticket', row[0])]

    def _suggest_wikipage(self, req):
        return [{'value': page}
                for page in sorted(page for page in WikiSystem(self.env).pages
                                   if 'WIKI_VIEW' in req.perm('wiki', page))]

    def _suggest_attachment(self, req, term):
        tokens = term.split(':', 2)
        if len(tokens) == 2:  # "realm:..."
            realm = tokens[0]
            term = tokens[1]
            rows = self.env.db_query("""
                SELECT DISTINCT id FROM attachment
                WHERE type=%s ORDER BY id""", (realm,))
            completions = [realm + ':' + row[0] + ':'
                           for row in rows if row[0].startswith(term)]
        else:
            completions = []
            if len(tokens) == 3:  # "realm:id:..."
                realm = tokens[0]
                id = tokens[1]
                term = tokens[2]
            else:
                completions.extend(
                    row[0] + ':'
                    for row in self.env.db_query(
                        "SELECT DISTINCT type FROM attachment ORDER BY type")
                    if row[0].startswith(term))
                realm = req.args.get('realm')
                id = req.args.get('id')
            filenames = sorted(
                att.filename for att in Attachment.select(self.env, realm, id)
                             if att.filename.startswith(term) and
                                'ATTACHMENT_VIEW' in req.perm(att.resource))
            if len(tokens) == 3:
                completions.extend('%s:%s:%s' % (realm, id, filename)
                                   for filename in filenames)
            else:
                completions.extend(filenames)
        return [{'value': value} for value in completions]

    def _suggest_macro(self, req):
        resource = Resource(req.args.get('realm'), req.args.get('id'))
        context = web_context(req, resource)
        completions = []
        for name, descr in self._get_macros().iteritems():
            details_html = self._format_to_html(context, descr)
            title_html = self._format_to_oneliner(context, descr, shorten=True)
            completions.append({'value': name,
                                'title_html': title_html,
                                'details_html': details_html})
        return sorted(completions, key=lambda entry: entry['value'])

    def _suggest_processor(self, req):
        resource = Resource(req.args.get('realm'), req.args.get('id'))
        context = web_context(req, resource)
        macros = self._get_macros()
        mimetypes = set()
        for name, mimetype in Mimeview(self.env).mime_map.iteritems():
            if name not in macros:
                mimetypes.add(name)
            mimetypes.add(mimetype)

        completions = []
        for name, descr in macros.iteritems():
            details_html = self._format_to_html(context, descr)
            title_html = self._format_to_oneliner(context, descr, shorten=True)
            completions.append({'value': name,
                                'title_html': title_html,
                                'details_html': details_html})
        completions.extend({'value': mimetype}
                           for mimetype in mimetypes)
        return sorted(completions, key=lambda item: item['value'])

    def _suggest_source(self, req, term):

        def suggest_revs(repos, node, search_rev):
            if search_rev:
                for category, names, path, rev in repos.get_quickjump_entries(None):
                    if path and path != '/':
                        # skip jumps to other paths
                        # (like SVN's 'trunk', 'branches/...', 'tags/...' folders)
                        continue
                    # Multiple Mercurial tags on same revision are comma-separated:
                    for name in names.split(', '):
                        if ' ' in name:
                            # use first token, e.g. '1.0' from '1.0 (tip)'
                            name = name.split(' ', 1)[0]
                        if name.startswith(search_rev):
                            yield name
            for r in node.get_history(10):
                rev = repos.short_rev(r[1])
                if str(rev).startswith(search_rev):
                    yield rev

        rm = RepositoryManager(self.env)
        if term.find('/') == -1 and term.find('@') == -1:
            lower_term = term.lower()
            completions = sorted(
                reponame + '/'
                for reponame in rm.get_all_repositories()
                if reponame.lower().startswith(lower_term) and
                    'BROWSER_VIEW' in req.perm('repository', reponame))
        else:
            pos = term.find('/')
            if pos == -1:
                pos = term.find('@')
            reponame, path = term[:pos], term[pos:]
            repos = rm.get_repository(reponame)
            completions = []
            if repos is not None:
                if path.find('@') != -1:
                    path, search_rev = path.rsplit('@', 1)
                    node = repos.get_node(path, repos.youngest_rev)
                    if node.can_view(req.perm):
                        completions.extend(
                            '%s%s@%s' % (reponame, path, rev)
                            for rev in suggest_revs(repos, node, search_rev))
                else:
                    dir, filename = path.rsplit('/', 1)
                    node = repos.get_node(dir or '/', repos.youngest_rev)
                    completions = sorted(
                        '%s/%s%s' % (reponame, n.path.lstrip('/'), '/' if n.isdir else '')
                        for n in node.get_entries()
                        if n.name.startswith(filename) and n.can_view(req.perm))
        return [{'value': value} for value in completions]

    def _suggest_milestone(self, req):
        return [{'value': name}
                for name in sorted(MilestoneCache(self.env).milestones)
                if 'MILESTONE_VIEW' in req.perm('milestone', name)]

    def _suggest_report(self, req):
        return [{'value': id, 'title': title}
                for id, title in self.env.db_query(
                                    "SELECT id, title FROM report ORDER BY id")
                if 'REPORT_VIEW' in req.perm('report', id)]

    def _get_num_ranges(self, term, validate):
        try:
            num = int(term)
        except:
            return []
        ranges = []
        mul = 1
        while num > 0 and validate(num):
            ranges.append(num)
            ranges.append(num + mul)
            num *= 10
            mul *= 10
        return ranges

    def _get_intertracs(self):
        has_trac = False
        for name, value in self.config.options('intertrac'):
            if name.endswith('.url'):
                name = name[:-4]
                title = self.config.get('intertrac', name + '.title')
                yield name, value, title
                if name == 'trac':
                    has_trac = True

        if not has_trac:
            yield ('trac', 'http://trac.edgewall.org',
                   dgettext('messages', 'The Trac Project'))

    _builtin_macros = ('html', 'htmlcomment', 'default', 'comment', 'div',
                       'rtl', 'span', 'Span', 'td', 'th', 'tr', 'table')

    @lazy
    def _known_macros(self):
        macros = {}
        macros.update((name, '(built-in)') for name in self._builtin_macros)
        macros.update((name, provider.get_macro_description(name))
                      for provider in WikiSystem(self.env).macro_providers
                      for name in provider.get_macros() or ()
                      if name not in macros)
        return macros

    def _get_macros(self):
        macros = {}
        for name, descr in self._known_macros.iteritems():
            if isinstance(descr, (tuple, list)):
                descr = dgettext(descr[0], to_unicode(descr[1]))
            macros[name] = descr
        return macros

    def _format_to_html(self, context, wikidom, **options):
        return format_to_html(self.env, context, wikidom, **options)

    def _format_to_oneliner(self, context, wikidom, **options):
        return format_to_oneliner(self.env, context, wikidom, **options)

    def _send_json(self, req, data):
        req.send(to_json(data), 'application/json')

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('wikiautocomplete', pkg_resources.resource_filename('wikiautocomplete', 'htdocs'))]

    def get_templates_dirs(self):
        return []
