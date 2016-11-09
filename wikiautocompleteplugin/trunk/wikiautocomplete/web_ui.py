# -*- coding: utf-8 -*-

from __future__ import with_statement

import pkg_resources
import re

from trac.core import Component, TracError, implements
from trac.attachment import Attachment
from trac.resource import Resource
from trac.ticket.model import Ticket
from trac.util.text import to_unicode
from trac.util.translation import dgettext
from trac.web import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_script_data, add_stylesheet, web_context
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.wiki.api import WikiSystem
from trac.versioncontrol.api import RepositoryManager


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
            script_data = {'url': req.href('wikiautocomplete')}
            context = data.get('context')
            if context and context.resource:
                script_data['realm'] = context.resource.realm
                script_data['id'] = context.resource.id
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
        term = req.args.get('q')
        if strategy == 'linkresolvers':
            completions = self._suggest_linkresolvers(req, term)
        elif strategy == 'ticket':
            completions = self._suggest_ticket(req, term)
        elif strategy == 'wikipage':
            completions = self._suggest_wikipage(req, term)
        elif strategy == 'attachment':
            completions = self._suggest_attachment(req, term)
        elif strategy == 'macro':
            completions = self._suggest_macro(req, term)
        elif strategy == 'source':
            completions = self._suggest_source(req, term)
        else:
            completions = None
        if completions is None:
            raise TracError('Invalid operation: %r, %r' % (strategy, term))
        else:
            self._send_json(req, completions)

    def _suggest_linkresolvers(self, req, term):
        wiki = WikiSystem(self.env)
        completions = set(name for provider in wiki.syntax_providers
                               for name, resolver
                                   in provider.get_link_resolvers()
                               if name.startswith(term))
        return sorted(completions)

    def _suggest_ticket(self, req, term):
        try:
            num = int(term)
        except:
            num = 0
        args = []
        mul = 1
        while num > 0 and Ticket.id_is_valid(num):
            args.append(num)
            args.append(num + mul)
            num *= 10
            mul *= 10
        if args:
            expr = ' OR '.join(['id>=%s AND id<%s'] * (len(args) / 2))
            rows = self.env.db_query("""
                SELECT id, summary FROM ticket
                WHERE %(expr)s
                ORDER BY changetime DESC
                LIMIT 10
                """ % {'expr': expr}, args)
        else:
            rows = self.env.db_query("""
                SELECT id, summary FROM ticket
                ORDER BY changetime DESC LIMIT 10""")
        return [{'id': row[0], 'summary': row[1]}
                for row in rows if 'TICKET_VIEW' in req.perm('ticket', row[0])]

    def _suggest_wikipage(self, req, term):
        return sorted(page for page in WikiSystem(self.env).pages
                           if page.startswith(term) and
                              'WIKI_VIEW' in req.perm('wiki', page))

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
        return completions

    def _suggest_macro(self, req, term):
        resource = Resource()
        context = web_context(req, resource)
        wiki = WikiSystem(self.env)
        macros = []
        for provider in wiki.macro_providers:
            names = list(provider.get_macros() or [])
            for name in names:
                if name.startswith(term):
                    macros.append((name, provider))
        if len(macros) == 1:
            name, provider = macros[0]
            descr = provider.get_macro_description(name)
            if isinstance(descr, (tuple, list)):
                descr = dgettext(descr[0], to_unicode(descr[1]))
            descr = format_to_html(self.env, context, descr)
            return [{'name': name, 'description': descr}]
        else:
            completions = []
            for name, provider in macros:
                descr = provider.get_macro_description(name)
                if isinstance(descr, (tuple, list)):
                    descr = dgettext(descr[0], to_unicode(descr[1]))
                completions.append({'name': name, 'description': descr})
            completions = sorted(completions,
                                 key=lambda entry: entry['name'])
            for entry in completions:
                entry['description'] = format_to_oneliner(
                    self.env, context, entry['description'], shorten=True)
            return completions

    def _suggest_source(self, req, term):
        rm = RepositoryManager(self.env)
        completions = []
        if term.find('/') == -1:
            for reponame, repoinfo in rm.get_all_repositories().iteritems():
                if 'BROWSER_VIEW' in req.perm(Resource('repository', reponame)):
                    if len(term) == 0 or reponame.lower().startswith(term.lower()):
                        completions.append(reponame + '/')
        else:
            reponame, path = term.split('/', 1)
            repos = rm.get_repository(reponame)
            if repos is not None:
                if path.find('@') != -1:
                    path, search_rev = path.rsplit('@', 1)
                    node = repos.get_node(path, repos.youngest_rev)
                    if node.can_view(req.perm):
                        for r in node.get_history(10):
                            if str(r[1]).startswith(search_rev):
                                completions.append('%s/%s@%s' % (reponame, path, r[1]))
                else:
                    if path.find('/') != -1:
                        dir, filename = path.rsplit('/', 1)
                    else:
                        dir, filename = '/', path
                    node = repos.get_node(dir, repos.youngest_rev)
                    completions = ['%s/%s%s' % (reponame, n.path, '/' if n.isdir else '')
                                   for n in node.get_entries()
                                   if n.can_view(req.perm) and n.name.startswith(filename)]
        return completions

    def _send_json(self, req, data):
        req.send(to_json(data), 'application/json')

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('wikiautocomplete', pkg_resources.resource_filename('wikiautocomplete', 'htdocs'))]

    def get_templates_dirs(self):
        return []
