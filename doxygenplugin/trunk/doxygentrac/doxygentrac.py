# -*- coding: utf-8 -*-
# vim: ts=4 expandtab
#
# Copyright (C) 2005 Jason Parks <jparks@jparks.net>. All rights reserved.
# Copyright (C) 2006-2007 Christian Boos <cboos@neuf.fr>
# Copyright (C) 2016 Emmanuel Saint-James <esj@rezo.net>
#

import mimetypes
import os
import re
from operator import itemgetter

from doxyfiletrac import init_doxyfile, post_doxyfile
from saxygen import search_in_doxygen
from trac.admin import IAdminPanelProvider
from trac.config import Option
from trac.core import *
from trac.loader import get_plugin_info
from trac.perm import IPermissionRequestor
from trac.search.api import ISearchSource, shorten_result
from trac.util.datefmt import to_datetime
from trac.util.html import Markup, tag
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_stylesheet, add_script, add_ctxtnav
from trac.wiki.api import WikiSystem, IWikiSyntaxProvider
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage


class DoxygenPlugin(Component):

    implements(IAdminPanelProvider, INavigationContributor,
               IPermissionRequestor, IRequestHandler, ISearchSource,
               ITemplateProvider, IWikiSyntaxProvider)

    base_path = Option('doxygen', 'path', '',
        """Directory containing doxygen generated files (= OUTPUT_DIRECTORY).
        """)

    input = Option('doxygen', 'input', '',
        """Directory containing sources.""")

    default_doc = Option('doxygen', 'default_documentation', '',
        """Default documentation project, relative to `[doxygen] path`.
        When no explicit path is given in a documentation request,
        this path will be prepended to the request before looking
        for documentation files.""")

    html_output = Option('doxygen', 'html_output', 'html',
        """Default documentation project suffix, as generated by Doxygen
        using the HTML_OUTPUT Doxygen configuration setting.""")

    title = Option('doxygen', 'title', 'Doxygen',
        """Title to use for the main navigation tab.""")

    index = Option('doxygen', 'index', 'index.html',
        """Default index page to pick in the generated documentation.""")

    searchdata_file = Option('doxygen', 'searchdata_file', 'searchdata.xml',
        """Default name of XML search file.""")

    wiki_index = Option('doxygen', 'wiki_index', None,
        """Wiki page to use as the default page for the Doxygen main page.
        If set, supersedes the `[doxygen] index` option.""")

    encoding = Option('doxygen', 'encoding', 'utf-8',
        """Default encoding used by the generated documentation files.""")

    default_namespace = Option('doxygen', 'default_namespace', '',
        """Default namespace to search for named objects in.""")

    doxyfile = Option('doxygen', 'doxyfile', '',
        """Full path of the Doxyfile to be created.""")

    doxygen = Option('doxygen', 'doxygen', '/usr/local/bin/doxygen',
         """Full path of the Doxygen command.""")

    doxygen_args = Option('doxygen', 'doxygen_args', '',
        """Arguments for the Doxygen command.""")

    def link_me(self, name):
        for plugin in get_plugin_info(self.env):
            if 'name' in plugin and plugin['name'] == name:
                info = plugin['info']
                url = info.get('home_page')
                version = info['version']
                return '<a href="' + url + '">TracDoxygen ' + version + '</a>'
        return name

    def check_documentation(self, doc):
        index = os.path.join(self.base_path, doc, self.searchdata_file)
        if not os.path.exists(index) or not os.access(index, os.R_OK):
            self.log.debug('No readable file "%s" in Doxygen dir ', index)
            return ''
        return index

    def merge_header(self, req, path):
        """Split a Doxygen HTML page in its head and body part.
        Find the references to style sheets by the Link tag
        and move them to the Trac Head part by add_stylesheet.
        Same work for the JS files referenced by the Script Tag, by 
        add_script. Move also the content of the Title Tag, by using JQuery.
        """

        try:
            content = file(path).read()
        except (IOError, OSError), e:
            raise TracError("Can't read doxygen content: %s" % e)

        m = re.match(
            r'''^\s*<!DOCTYPE[^>]*>\s*<html[^>]*>\s*<head>(.*?)</head>\s*<body[^>]*>(.*)</body>\s*</html>''',
            content, re.S)

        if not m:
            return content

        # pick up links to CSS and move them to header of the Trac Page
        l = re.findall(r'''<link[^>]*type=.text/css[^>]*>''', m.group(1),
                       re.S)
        for i in l:
            h = re.search(r'''href=.([^ ]*)[^ /][ /]''', i)
            h = h.group(1)
            u = re.match(r'''^[./]*([^:]+)$''', h)
            if u:
                h = os.path.join('/doxygen', u.group(1))
            add_stylesheet(req, h)

        # pick up the title of the Doxygen page
        # since there is no API to move it in the header of the Trac page
        # we will use JQuery to do it on load
        t = re.search(r'''<title>.*?:(.*)</title>''', m.group(1), re.S)
        if t:
            t = '$(document).ready(function() { document.title+="' + t.group(
                1) + '";})'
        else:
            t = ''
        # pick up the scripts
        # if it is a file, move the tag Script in the header of the Trac page
        # otherwise, keep it here
        s = re.findall(r'''<script([^>]*)>(.*?)</script>''', m.group(1), re.S)
        for i in s:
            h = re.search(r'''src=.([^ ]*).''', i[0])
            if not h:
                t += i[1]
            else:
                h = h.group(1)
                if h != 'jquery.js':
                    u = re.match(r'''^[./]*([^:]+)$''', h)
                    if u:
                        h = os.path.join('/doxygen', u.group(1))
                    add_script(req, h)

        if t:
            t = "<script type='application/javascript'>" + t + "</script>\n"
        return t + m.group(2)

    def rewrite_doxygen(self, req, path, doc, charset):
        def wiki_in_doxygen(m):
            return wiki_to_html(m.group(1), self.env, req)

        content = to_unicode(self.merge_header(req, path), charset)

        # Add a query string for explicit documentation
        if doc:
            href = re.compile(r'''<a.*?href=.[^"]*?[.]html''')
            content = href.sub(r'\g<0>' + '?doc=' + doc, content)

        # translate TracLink in Doxygen comments
        # (unless some HTML tags are present. Should be better)
        comment = re.compile(r'''<p>([^<>&]*?)</p>''', re.S)
        content = comment.sub(wiki_in_doxygen, content)
        comment = re.compile(r'''<dd>([^<>&]*?)</dd>''', re.S)
        content = comment.sub(wiki_in_doxygen, content)

        name = self.link_me('TracDoxygen')
        content = re.sub(r'(<small>.*)(<a .*</small>)',
                         r'\1' + name + r' &amp; \2', content, 1, re.S)
        return {'doxygen_content': Markup(content)}

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['DOXYGEN_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'doxygen'

    def get_navigation_items(self, req):
        if 'DOXYGEN_VIEW' in req.perm:
            # Return mainnav buttons.
            yield ('mainnav', 'doxygen',
                   tag.a(self.title, href=req.href.doxygen()))

    # IRequestHandler methods

    def match_request(self, req):
        self.log.debug('match_request %s', req.path_info)
        return re.match(r'''/doxygen(/|$)''', req.path_info)

    def process_request(self, req):
        req.perm.assert_permission('DOXYGEN_VIEW')
        if req.path_info == '/doxygen':
            req.redirect(req.href.doxygen('/'))

        self.log.debug('process_request %s et %s', req.path_info,
                       req.query_string)
        segments = filter(None, req.path_info.split('/'))
        segments = segments[1:]  # ditch 'doxygen'
        if not segments:
            self.log.debug('page garde from %s', req.path_info)
            # Handle /doxygen request
            wiki = self.wiki_index
            if wiki:
                if WikiSystem(self.env).has_page(wiki):
                    text = WikiPage(self.env, wiki).text
                else:
                    text = 'Doxygen index page [wiki:%s] does not exist.' % \
                           wiki
                data = {'doxygen_text': wiki_to_html(text, self.env, req)}
                add_ctxtnav(req, "View %s page" % wiki, req.href.wiki(wiki))
                return 'doxygen.html', data, 'text/html'
            else:
                # use configured Doxygen index
                file_ = self.index
                dir_ = ''
        else:
            file_ = segments[-1]
            dir_ = segments[:-1]
            dir_ = os.path.join(*dir_) if dir_ else ''

        doc = req.args.get('doc') if req.args.get('doc') else self.default_doc
        self.log.debug('file %s in doc %s', file_, doc)
        path = os.path.join(self.base_path, doc, self.html_output, dir_,
                            file_)
        if not path or not os.path.exists(path):
            self.log.debug('%s not found in %s for doc %s', file_, path, doc)
            url = req.href.search(q=req.args.get('query'), doxygen='on')
            req.redirect(url)

        self.log.debug('Process_req P %s  %s.', path, req.path_info)

        # security check
        path = os.path.abspath(path)
        if not path.startswith(os.path.normpath(self.base_path)):
            raise TracError("Can't access paths outside of " + self.base_path)

        mimetype = mimetypes.guess_type(path)[0]
        self.log.debug('mime %s path: %s for %s.', mimetype, path,
                       req.path_info)
        if mimetype == 'text/html':
            add_stylesheet(req, 'doxygen/css/doxygen.css')
            charset = (self.encoding or
                       self.env.config['trac'].get('default_charset'))
            doc = doc if req.args.get('doc') else ''
            content = self.rewrite_doxygen(req, path, doc, charset)
            return 'doxygen.html', content, 'text/html'
        else:
            req.send_file(path, mimetype)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('doxygen', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IAdminPanelProvidermethods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('general', _("General"), 'query', 'Doxyfile')

    def render_admin_panel(self, req, cat, page, info):
        req.perm.require('TRAC_ADMIN')

        if req.method == 'POST':
            # if post is ok, we dont return here:
            # a redirection to the main page of the documentation occurs
            env = post_doxyfile(req, self.doxygen, self.doxygen_args,
                                self.doxyfile, self.input, self.base_path,
                                self.log)
        else:
            env = {}

        env = init_doxyfile(env, self.doxygen, self.doxyfile, self.input,
                            self.base_path, self.default_doc, self.log)
        add_stylesheet(req, 'doxygen/css/doxygen.css')
        add_script(req, 'doxygen/js/doxygentrac.js')
        return 'doxygen_admin.html', env

    # ISearchProvider methods

    def get_search_filters(self, req):
        if 'DOXYGEN_VIEW' not in req.perm:
            return
        if not self.check_documentation(self.default_doc):
            return
        yield 'doxygen', self.title

    def get_search_results(self, req, keywords, filters):
        """Return the entry  whose 'keyword' or 'text' tag contains
        one or more word among the keywords.
        """

        if 'doxygen' not in filters:
            return

        k = '|'.join(keywords).encode(self.encoding)
        doc = self.check_documentation(self.default_doc)
        all_ = search_in_doxygen(doc, k, ['keywords', 'text'], True, self.log)
        all_ = sorted(all_, key=itemgetter('keywords'))
        all_ = sorted(all_, key=itemgetter('occ'), reverse=True)
        self.log.debug('%s search in %s: "%s" items', k, doc, len(all_))
        for res in all_:
            url = 'doxygen/' + res['url'] + '#' + res['target']
            t = shorten_result(res['text'])
            yield url, res['keywords'], to_datetime(res['date']), 'doxygen', t

    # IWikiSyntaxProvider

    def get_link_resolvers(self):
        def doxygen_link(formatter, ns, name, label):
            doc = self.default_doc
            if '/' in name:
                doc, name = name.split('/')
                if not doc:
                    doc = self.default_doc
            self.log.debug("search link for %s inc doc %s", name, doc)
            if not name:
                if doc:
                    label = doc
                else:
                    label = 'index'
                res = {'url': 'index.html', 'target': '', 'type': 'file',
                       'text': 'index'}
            else:
                file_ = self.check_documentation(doc)
                res = search_in_doxygen(file_, name, ['name'], False,
                                        self.log)
                if not res:
                    suffix = '[.:\\\\]' + name + '$'
                    res = search_in_doxygen(file_, suffix, ['name'], True,
                                            self.log)
                    if len(res) != 1:
                        self.log.debug('%s: %d occurrences in %s', suffix,
                                       len(res), file_)
                        return tag.a(label, title=name, class_='missing',
                                     href=formatter.href.doxygen())
                    else:
                        res = res[0]

            if doc != self.default_doc:
                url = formatter.href.doxygen(res['url'], doc=doc)
            else:
                url = formatter.href.doxygen(res['url'])
            url += '#' + res['target']
            self.log.debug("doxygen_link %s for %s in %s", url, name, doc)
            t = res['type']
            if t == 'function':
                t += ' ' + res['name'] + ' ' + res['args']
            t += ' ' + shorten_result(res['text'])
            return tag.a(label, title=t, href=url)

        yield 'doxygen', doxygen_link

    def get_wiki_syntax(self):
        return []
