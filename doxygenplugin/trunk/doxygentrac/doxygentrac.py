# -*- coding: utf-8 -*-
# vim: ts=4 expandtab
#
# Copyright (C) 2005 Jason Parks <jparks@jparks.net>. All rights reserved.
# Copyright (C) 2006-2007 Christian Boos <cboos@neuf.fr>
# Copyright (C) 2016 Emmanuel Saint-James <esj@rezo.net>
#

import os
import time
import posixpath
import re
import mimetypes
import xml.sax

from collections import OrderedDict
from genshi.builder import tag
from genshi.core import Markup
from subprocess import Popen
from trac.admin import IAdminPanelProvider
from trac.config import Option
from trac.core import *
from trac.loader import get_plugin_info
from trac.perm import IPermissionRequestor
from trac.search.api import ISearchSource, shorten_result
from trac.util.text import to_unicode
from trac.util.datefmt import to_datetime
from trac.util.text import exception_to_unicode
from trac.util.translation import _
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_stylesheet, add_script, add_ctxtnav, \
                            add_notice, add_warning
from trac.wiki.api import WikiSystem, IWikiSyntaxProvider
from trac.wiki.model import WikiPage
from trac.wiki.formatter import wiki_to_html


class DoxygenTracHandler(xml.sax.ContentHandler):
    last_field_name = ''
    fields = {}
    multi = []

    def __init__(self, find, where, multi, date):
        self.to_where  = where
        self.to_date  = date
        self.to_multi = multi
        if multi:
            self.to_find = re.compile(r'''%s''' % find)
        else:
            self.to_find = find

    def characters(self, content):
        if self.last_field_name != "":
            self.fields[self.last_field_name] += content

    def startElement(self, name, attrs):
        if name == 'field':
            self.last_field_name = attrs['name']
            self.fields[self.last_field_name] = ''
        else: self.last_field_name = ''

    def endElement(self, name):
        self.last_field_name = ''
        if name == "doc":
            for field in self.to_where:
                if not self.to_multi:
                    p = self.to_find == self.fields[field]
                else:
                    p = self.to_find.search(self.fields[field])

                if p:
                    if '#' in self.fields['url']:
                        url, target = self.fields['url'].split('#', 2)
                        self.fields['url'] = url
                        self.fields['target'] = target
                    else:
                        self.fields['target'] = ''
                    self.fields['date'] = self.to_date
                    if not self.to_multi:
                        raise IndexFound(self.fields)
                    else:
                        self.multi.append(self.fields)
                        break;
            self.fields = {}
        else:
            if name == "add" and self.to_multi:
                raise IndexFound(self.multi)

class IndexFound(Exception):
    def __init__( self, msg ):
        Exception.__init__(self, msg)

class DoxygenPlugin(Component):
    implements(IPermissionRequestor, INavigationContributor, IRequestHandler,
               ITemplateProvider, ISearchSource, IWikiSyntaxProvider,
               IAdminPanelProvider)

    base_path = Option('doxygen', 'path', '',
      """Directory containing doxygen generated files (= OUTPUT_DIRECTORY).""")

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


    # internal methods

    def _search_in_documentation(self, doc, name, where, multi):
        # Open index file for documentation
        index = os.path.join(self.base_path, doc, self.searchdata_file)
        res = {}
        if not os.path.exists(index) :
            self.log.debug('No file "%s" in Doxygen dir ', index)
        else:
            date = os.path.getctime(index)
            parser = xml.sax.make_parser()
            parser.setContentHandler(DoxygenTracHandler(name, where, multi, date))
            try:
                parser.parse(index)
            except IndexFound as a:
                res = a.args[0]
        return res

    def _merge_header(self, req, path):
        # Genshi can't include an unparsed file
        # data = {'doxygen_path': path}
        try:
            content = file(path).read()
        except (IOError, OSError), e:
            raise TracError("Can't read doxygen content: %s" % e)

        # Pick up header and body parts of the Doxygen page
        m = re.match(r'''^\s*<!DOCTYPE[^>]*>\s*<html[^>]*>\s*<head>(.*?)</head>\s*<body[^>]*>(.*)</body>\s*</html>''', content, re.S)
        if m:
            # pick up links to CSS and move them to header of the Trac Page
            l = re.findall(r'''<link[^>]*type=.text/css[^>]*>''', m.group(1), re.S)
            for i in l:
                h = re.search(r'''href=.([^ ]*)[^ /][ /]''', i)
                h = h.group(1)
                u = re.match(r'''^[./]*([^:]+)$''', h)
                if u:
                    h = os.path.join('/doxygen', u.group(1))
                self.log.debug('CSS %s', h)
                add_stylesheet(req, h)

            # pick up the title of the Doxygen page
            # since there is no API to move it in the header of the Trac page
            # we will use JQuery to do it on load
            t = re.search(r'''<title>.*?:(.*)</title>''', m.group(1), re.S)
            if t:
                t = '$(document).ready(function() { document.title+="' +  t.group(1) + '";})'
            else:
                t = ''
            # pick up the scripts
            # if it is a file, move the tag Script in the header of the Trac page
            # otherwise, keep it here
            s = re.findall(r'''<script([^>]*)>(.*?)</script>''', m.group(1), re.S)
            for i in s:
                h = re.search(r'''src=.([^ ]*).''', i[0])
                self.log.debug('Script %s %s', i[0], h)
                if not h:
                    t += i[1]
                else:
                    h = h.group(1)
                    if (h != 'jquery.js'):
                        u = re.match(r'''^[./]*([^:]+)$''', h)
                        if u:
                            h = os.path.join('/doxygen', u.group(1))
                        add_script(req, h)

            if t:
                t = "<script type='application/javascript'>" + t + "</script>\n"
            content = t + m.group(2)
        charset = (self.encoding or
                   self.env.config['trac'].get('default_charset'))
        content = to_unicode(content, charset)
        info = get_plugin_info(self.env)
        version = ('DoxygenPlugin ' + info[0]['info']['version'] + ' &amp; ').decode('ascii')
        content = re.sub(r'(<small>.*)(<a .*</small>)', r'\1' + version + r'\2', content,1,re.S)
        return {'doxygen_content': Markup(content)}

    def analyse_doxyfile(self, path, old):
        # find all the options "X = "
        # with their description just before
        # text blocs between '#----' introduce new section

        try:
            content = file(path).read()
        except (IOError, OSError), e:
            raise TracError("Can't read doxygen content: %s" % e)

        content = to_unicode(content, 'utf-8')
        # Initial text is about file, not form
        c = re.match(r'''^.*?(#-----.*)''', content, re.S)
        if c:
            self.log.debug('taking "%s" last characters out of %s in %s', len(c.group(1)), len(content), path);
            content = c.group(1)

        m = re.compile(r'''\s*(#-+\s+#(.*?)\s+#-+)?(.*?)$\s*([A-Z][A-Z0-9_-]+)\s*=([^#]*?)$''', re.S|re.M)
        s = m.findall(content)
        self.log.debug('Found "%s" options in Doxyfile', len(s));
        options = OrderedDict()
        for o in s:
            u, explain, label, id, value = o
            atclass = 'changed'
            if id == 'OUTPUT_DIRECTORY' and self.base_path:
                value = self.base_path
            else:
                if id == 'INPUT' and self.input:
                    value = self.input
                else: 
                    if id in old and value != old[id]['value']:
                        value = old[id]['value']
                    else:
                        atclass = ''

            # prepare longer input tag for long default value
            l = 20 if len(value) < 20 else len(value) + 3
            options[id] = {'explain': explain, 'label': label, 'value': value, 'size': l, 'atclass': atclass}
        return options

    def display_doxyfile(self, prev, first, sets):
        if re.match(r'''.*output$''', prev) and first == 'NO':
            display = 'none'
        else:
            display = 'block'
        return {'display': display, 'opt': sets}


    def apply_doxyfile(self, doxyfile, path_trac, req):
        f = open(doxyfile, 'w')
        for k in req.args:
            if not re.match(r'''^[A-Z]''', k):
                continue
            if req.args.get(k):
                s = req.args.get(k)
            else:
                s = '';
            o = "#\n" + k + '=' + s + "\n"
            f.write(o.encode('utf8'))
        f.close()
        fo = path_trac + 'doxygen.out'
        o = open(fo, 'w');
        fr = path_trac + 'doxygen.err'
        e = open(fr, 'w');
        if self.doxygen_args:
            arg = self.doxygen_args
        else:
            arg = doxyfile
        self.log.debug('calling ' + self.doxygen + ' ' + arg)
        dir = req.args.get('INPUT') if req.args.get('INPUT') else self.input;
        p = Popen([self.doxygen, arg], bufsize=-1, stdout=o, stderr=e, cwd=dir if dir else None)
        p.communicate();
        n = p.returncode;
        o.close()
        e.close()
        if n == 0:
            path = os.path.join(self.base_path, self.default_doc)
            p = Popen(['chmod', '-R', 'g+w', path])
            msg = "Doxygen exits successfuly\n";
            trace = file(fo).read()
        else:
            msg = ("Doxygen Error %s\n" %(n))
            trace = file(fr).read()
        os.unlink(fo)
        os.unlink(fr)
        self.log.debug("Doxygen exit for %s: %s" % (path_trac, n))
        return {'msg': msg, 'trace': trace}

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['DOXYGEN_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'doxygen'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DOXYGEN_VIEW'):
            # Return mainnav buttons.
            yield ('mainnav', 'doxygen',
                   tag.a(self.title, href=req.href.doxygen()))

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'''/doxygen(/|$)''', req.path_info)

    def process_request(self, req):
        req.perm.assert_permission('DOXYGEN_VIEW')
        if req.path_info == '/doxygen':
            req.redirect(req.href.doxygen('/'))

        self.log.debug('process_request %s', req.path_info)
        segments = filter(None, req.path_info.split('/'))
        segments = segments[1:] # ditch 'doxygen'
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
                file = self.index
                dir = ''
        else:
            file = segments[-1]
            self.log.debug('file %s in %s', file, req.path_info)
            dir = segments[:-1]
            dir = os.path.join(*dir) if dir else ''

        path = os.path.join(self.base_path, self.default_doc, self.html_output, dir, file)
        if not path or not os.path.exists(path):
            self.log.debug('%s not found in %s', file, path)
            url = req.href.search(q=req.args.get('query'), doxygen='on')
            req.redirect(url)

        self.log.debug('Process_req P %s.', path, req.path_info)

        # security check
        path = os.path.abspath(path)
        if not path.startswith(os.path.normpath(self.base_path)):
            raise TracError("Can't access paths outside of " + self.base_path)

        mimetype = mimetypes.guess_type(path)[0]
        self.log.debug('mime %s path: %s for %s.', mimetype, path, req.path_info)
        if mimetype == 'text/html':
            add_stylesheet(req, 'doxygen/css/doxygen.css')
            return 'doxygen.html', self._merge_header(req, path), 'text/html'
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
        path_trac = os.path.join(self.base_path, self.default_doc)
        if not os.path.isdir(path_trac) or not os.access(path_trac, os.W_OK):
            env = {'msg': 'Error:' + path_trac + ' not W_OK', 'trace': ''}
            path_trac = '/tmp'
        if self.doxyfile:
            doxyfile = self.doxyfile
        else:
            doxyfile = os.path.join(path_trac, 'Doxyfile')
        if req.method == 'POST':
            env = self.apply_doxyfile(doxyfile, path_trac, req)
        else:
            env = {'msg': '', 'trace': ''}
        # Read old choices if they exists
        if os.path.exists(doxyfile):
            old = self.analyse_doxyfile(doxyfile, {})
        else:
            old = {}
        # Generate the std Doxyfile
        # (newer after a doxygen command update, who knows)
        fi = os.path.join(path_trac, 'doxygen.tmp')
        fo = os.path.join(path_trac, 'doxygen.out')
        o = open(fo, 'w');
        fr = os.path.join(path_trac, 'doxygen.err')
        e = open(fr, 'w');
        if o and e:
            p = Popen([self.doxygen, '-g', fi],  bufsize=-1, stdout=o, stderr=e)
            p.communicate()
            n = p.returncode
        else:
            n = -1
        if not os.path.exists(fi) or n !=0:
            env['fieldsets'] = {};
            env['msg'] += (" Doxygen Error %s\n" %(n))
            env['trace'] = file(fr).read()
        else:
            # Read std Doxyfile and report old choices in it
            # split in fieldsets
            fieldsets = OrderedDict()
            sets = OrderedDict()
            prev = first = ''
            inputs = self.analyse_doxyfile(fi, old)
            for k,s in inputs.iteritems():
                if s['explain']:
                    if prev and sets:
                        self.log.debug("fieldset %s first '%s'" % (prev, first))
                        fieldsets[prev] = self.display_doxyfile(prev, first, sets)
                    sets = OrderedDict()
                    prev = s['explain']
                    first = s['value'].strip()
                sets[k] = s
            if prev and sets:
                fieldsets[prev] = self.display_doxyfile(prev, first, sets)
            env['fieldsets'] = fieldsets
        # try, don't cry
        try:
            os.unlink(fi)
            os.unlink(fr)
            os.unlink(fo)
        except (IOError, OSError), e:
            self.log.debug("forget temporary files")

        add_stylesheet(req, 'doxygen/css/doxygen.css')
        return 'doxygen_admin.html', env

    # ISearchProvider methods

    def get_search_filters(self, req):
        if req.perm.has_permission('DOXYGEN_VIEW'):
            yield('doxygen', self.title)

    def get_search_results(self, req, keywords, filters):
        """Return the entry  whose 'keyword' or 'text' tag contains
        one or more word among the keywords.
        """

        if not 'doxygen' in filters:
            return

        k = '|'.join(keywords).encode(self.encoding)
        doc = self.default_doc
        all = self._search_in_documentation(doc, k, ['keywords', 'text'], True)
        self.log.debug('%s search: "%s" items', all, len(all))
        for res in all:
            path = os.path.join(doc, self.html_output)
            url = req.href.doxygen(path + '/' + res['url'])  + '#' + res['target']
            t = shorten_result(res['text'])
            yield url, res['keywords'], to_datetime(res['date']), 'doxygen', t

    # IWikiSyntaxProvider

    def get_link_resolvers(self):
        def doxygen_link(formatter, ns, name, label):
            res = True
            if '/' not in name:
                doc = self.default_doc
            else:
                doc, name = name.split('/')
                if not doc:
                    doc = self.default_doc
                else:
                    res = os.path.exists(os.path.join(self.base_path, doc))

            if not name:
                if doc:
                    label = doc
                else: label = 'index'
                res = {'url':'index.html', 'target':'', 'type':'file', 'text':'index'}
            elif res:
                res = self._search_in_documentation(doc, name, ['name'], False)

            if not res:
                return tag.a(label, title=name, class_='missing',
                              href=formatter.href.doxygen())
            url = os.path.join(doc, self.html_output, res['url'])
            url = formatter.href.doxygen(url) + '#' + res['target']
            self.log.debug("doxygen_link %s" %(url))
            t = res['type']
            if (t == 'function'):
                t += ' ' + res['name'] + ' ' + res['args']
            t += ' ' + shorten_result(res['text'])
            return tag.a(label, title=t, href=url)

        yield ('doxygen', doxygen_link)

    def get_wiki_syntax(self):
        return []
