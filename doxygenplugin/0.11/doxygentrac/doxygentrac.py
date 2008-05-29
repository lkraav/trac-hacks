# -*- coding: utf-8 -*-
# vim: ts=4 expandtab
#
# Copyright (C) 2005 Jason Parks <jparks@jparks.net>. All rights reserved.
# Copyright (C) 2006-2007 Christian Boos <cboos@neuf.fr>
#

import os
import time
import posixpath
import re
import mimetypes

from genshi.builder import tag
from genshi.core import Markup

from trac.config import Option
from trac.core import *
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_stylesheet, add_ctxtnav
from trac.search.api import ISearchSource
from trac.wiki.api import WikiSystem, IWikiSyntaxProvider
from trac.wiki.model import WikiPage
from trac.wiki.formatter import wiki_to_html

def compare_rank(x, y):
    if x['rank'] == y['rank']:
        return 0
    elif x['rank'] > y['rank']:
        return -1
    return 1

class DoxygenPlugin(Component):
    implements(IPermissionRequestor, INavigationContributor, IRequestHandler,
               ITemplateProvider, ISearchSource, IWikiSyntaxProvider)

    base_path = Option('doxygen', 'path', '/var/lib/trac/doxygen',
      """Directory containing doxygen generated files.""")

    default_doc = Option('doxygen', 'default_documentation', '',
      """Default documentation project, relative to `[doxygen] path`.
      When no explicit path is given in a documentation request,
      this path will be prepended to the request before looking
      for documentation files.""")

    html_output = Option('doxygen', 'html_output', None,
      """Default documentation project suffix, as generated by Doxygen
      using the HTML_OUTPUT Doxygen configuration setting.""")

    title = Option('doxygen', 'title', 'Doxygen',
      """Title to use for the main navigation tab.""")

    ext = Option('doxygen', 'ext', 'htm html png',
      """Space separated list of extensions for doxygen managed files.""")

    source_ext = Option('doxygen', 'source_ext',
      'idl odl java cs py php php4 inc phtml m '
      'cpp cxx c hpp hxx h',
      """Space separated list of source files extensions""")

    index = Option('doxygen', 'index', 'main.html',
      """Default index page to pick in the generated documentation.""")

    wiki_index = Option('doxygen', 'wiki_index', None,
      """Wiki page to use as the default page for the Doxygen main page.
      If set, supersedes the `[doxygen] index` option.""")

    encoding = Option('doxygen', 'encoding', 'iso-8859-1',
      """Default encoding used by the generated documentation files.""")

    default_namespace = Option('doxygen', 'default_namespace', '',
      """Default namespace to search for named objects in.""")

    SUMMARY_PAGES = """
    annotated classes dirs files functions globals hierarchy
    index inherits main namespaces namespacemembers
    """.split()

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
        if re.match(r'^/doxygen(?:$|/)', req.path_info):
            if 'path' not in req.args: # not coming from a `doxygen:` link
                segments = filter(None, req.path_info.split('/'))
                segments = segments[1:] # ditch 'doxygen'
                if segments:
                    action, path, link = self._doxygen_lookup(segments)
                    if action == 'search' and link:
                        req.args['query'] = link
                    elif action == 'redirect':
                        req.args['link'] = link
                else:
                    action, path = 'index', ''
                req.args['action'] = action
                req.args['path'] = path
            return True

    def process_request(self, req):
        req.perm.assert_permission('DOXYGEN_VIEW')

        # Get request arguments
        path = req.args.get('path')
        action = req.args.get('action')
        link = req.args.get('link')

        self.log.debug('Performing %s(%s,%s)"' % (action or 'default',
                                                  path, link))

        # Redirect search requests.
        if action == 'search':
            req.redirect(req.href.search(q=req.args.get('query'),
                                         doxygen='on'))
        if action == 'redirect':
            if link: # we need to really redirect if there is a link
                if path:
                    req.redirect(req.href.doxygen(path=path)+link)
                else:
                    req.redirect(req.href.doxygen(link))
            else:
                self.log.warn("redirect without link")

        if req.path_info == '/doxygen':
            req.redirect(req.href.doxygen('/'))

        # Handle /doxygen request
        if action == 'index':
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
            # use configured Doxygen index
            path = os.path.join(self.base_path, self.default_doc,
                                self.html_output, self.index)

        self.log.debug('path: %s' % (path,))

        # security check
        path = os.path.abspath(path)
        if not path.startswith(self.base_path):
            raise TracError("Can't access paths outside of " + self.base_path)

        # view
        mimetype = mimetypes.guess_type(path)[0]
        if mimetype == 'text/html':
            add_stylesheet(req, 'doxygen/css/doxygen.css')
            # Genshi can't include an unparsed file
            # data = {'doxygen_path': path}
            try:
                content = Markup(file(path).read())
                data = {'doxygen_content': content}
                return 'doxygen.html', data, 'text/html'
            except OSError, e:
                raise TracError("Can't read doxygen content: %s" % e)
        else:
            req.send_file(path, mimetype)            

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('doxygen', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # ISearchProvider methods

    def get_search_filters(self, req):
        if req.perm.has_permission('DOXYGEN_VIEW'):
            yield('doxygen', self.title)

    def get_search_results(self, req, keywords, filters):
        self.log.debug("DOXYBUG: kw=%s f=%s" % (keywords, filters))
        if not 'doxygen' in filters:
            return

        # We have to search for the raw bytes...
        keywords = [k.encode(self.encoding) for k in keywords]

        for doc in os.listdir(self.base_path):
            # Search in documentation directories
            path = os.path.join(self.base_path, doc)
            path = os.path.join(path, self.html_output)
            self.log.debug("looking in doc (%s) dir: %s:" % (doc, path))
            if os.path.isdir(path):
                index = os.path.join(path, 'search.idx')
                if os.path.exists(index):
                    creation = os.path.getctime(index)
                    for result in  self._search_in_documentation(doc, keywords):
                        result['url'] =  req.href.doxygen(doc) + '/' \
                          + result['url']
                        yield result['url'], result['name'], creation, \
                          'doxygen', None

            # Search in common documentation directory
            index = os.path.join(self.base_path, self.html_output)
            index = os.path.join(index, 'search.idx')
            self.log.debug("looking in doc (%s) search.idx: %s:" % (doc, index))
            if os.path.exists(index):
                creation = os.path.getctime(index)
                for result in self._search_in_documentation('', keywords):
                    result['url'] =  req.href.doxygen() + '/' + \
                      result['url']
                    yield result['url'], result['name'], creation, 'doxygen', \
                      None

    # IWikiSyntaxProvider

    def get_link_resolvers(self):
        def doxygen_link(formatter, ns, params, label):
            if '/' not in params:
                params = self.default_doc+'/'+params
            segments = params.split('/')
            if self.html_output:
                segments[-1:-1] = [self.html_output]
            action, path, link = self._doxygen_lookup(segments)
            if action == 'index':
                return tag.a(label, title=self.title,
                             href=formatter.href.doxygen())
            if action == 'redirect' and path:
                return tag.a(label, title="Search result for "+params,
                             href=formatter.href.doxygen(link,path=path))
            if action == 'search':
                return tag.a(label, title=params, class_='missing',
                             href=formatter.href.doxygen())
            else:
                return tag.a(label, title=params,
                             href=formatter.href.doxygen(link, path=path))
        yield ('doxygen', doxygen_link)

    def get_wiki_syntax(self):
        return []

    # internal methods

    def _doxygen_lookup(self, segments):
        """Try to interpret path components as a request for doxygen targets

        Return an `(action,path,link)` tuple, where:
         - `action` describes what should be done (one of 'view',
           'redirect', or 'search'),
         - `path` is the location on disk of the resource.
         - `link` is the link to the resource, relative to the
           req.href.doxygen base or a target in case of 'redirect'
        """
        doc, file = segments[:-1], segments and segments[-1]

        if not doc and not file:
            return ('index', None, None) 
        if doc:
            doc = os.path.join(*doc)
        else:
            if self.default_doc: # we can't stay at the 'doxygen/' level
                return 'redirect', None, '/'.join([self.default_doc,
                                                   self.html_output,
                                                   file or self.index])
            else:
                doc = self.html_output

        def lookup(file, category='undefined'):
            """Build (full path, relative link) and check if path exists."""
            path = os.path.join(self.base_path, doc, file)
            existing_path = os.path.exists(path) and path
            link = doc+'/'+file
            self.log.debug(' %s file %s' % (category, existing_path or
                                            path+" (not found)"))
            return existing_path, link

        self.log.debug('Looking up "%s" in documentation "%s"' % (file, doc))

        # Direct request for searching
        if file == 'search.php':
            return 'search', None, None # keep existing 'query' arg

        # Request for a documentation file.
        doc_ext_re = '|'.join(self.ext.split(' '))
        if re.match(r'''^(.*)[.](%s)''' % doc_ext_re, file):
            path, link = lookup(file, 'documentation')
            if path:
                return 'view', path, link
            else:
                return 'search', None, file

        # Request for source file documentation.
        source_ext_re = '|'.join(self.source_ext.split(' '))
        match = re.match(r'''^(.*)[.](%s)''' % source_ext_re, file)
        if match:
            basename, suffix = match.groups()
            basename = basename.replace('_', '__')
            path, link = lookup('%s_8%s.html' % (basename, suffix), 'source')
            if path:
                return 'view', path, link
            else:
                return 'search', None, file

        # Request for summary pages
        if file in self.SUMMARY_PAGES:
            path, link = lookup(file + '.html', 'summary')
            if path:
                return 'view', path, link

        # Request for a named object
        # TODO:
        #  - do something about dirs
        #  - expand with enum, defs, etc.
        #  - this doesn't work well with the CREATE_SUBDIRS Doxygen option

        # do doxygen-style name->file mapping
        # this is a little different than doxygen, but I don't see another way
        # way to make doxygen:Type<bool> links work, as it inserts a ' ' (or
        # '_01') after/before the type name.
        charmap = { '_':'__', ':':'_1', '/':'_2', '<':'_3_01', '>':'_01_4', \
                    '*':'_5', '&':'_6', '|':'_7', '.':'_8', '!':'_9', \
                    ',':'_00',' ':'_01' }
        mangledfile = ''
        for i in file:
            if i in charmap.keys():
                mangledfile += charmap[i]
            else:
                mangledfile += i

        path, link = lookup('class%s.html' % mangledfile, 'class')
        if not path:
            path, link = lookup('struct%s.html' % mangledfile, 'struct')
        if path:
            return 'view', path, link

        # Try in the default_namespace
        if self.default_namespace != "":
            mangledfile = self.default_namespace + '_1_1' + mangledfile
            path, link = lookup('class%s.html' % mangledfile, 'class')
            if not path:
                path, link = lookup('struct%s.html' % mangledfile, 'struct')
            if path:
                return 'view', path, link


        # Revert to search...
        results = self._search_in_documentation(doc, [file])
        class_ref = file+' Class Reference'
        for result in results:
            self.log.debug('Reverted to search, found: ' + repr(result))
            name = result['name']
            if name == file or name == class_ref:
                url = result['url']
                target = ''
                if '#' in url:
                    url, target = url.split('#', 2)
                path, link = lookup(url)
                if path:
                    return 'redirect', path, link # target # FIXME
        self.log.debug('%s not found in %s' % (file, doc))
        return 'search', None, file

    def _search_in_documentation(self, doc, keywords):
        # Open index file for documentation
        index = os.path.join(self.base_path, doc, self.html_output, 'search.idx')
        if os.path.exists(index):
            fd = open(index)

            # Search for keywords in index
            results = []
            for keyword in keywords:
                results += self._search(fd, keyword)
                results.sort(compare_rank)
                for result in results:
                    yield result

    def _search(self, fd, word):
        results = []
        index = self._computeIndex(word)
        if index != -1:
            fd.seek(index * 4 + 4, 0)
            index = self._readInt(fd)

            if index:
                fd.seek(index)
                w = self._readString(fd)
                matches = []
                while w != "":
                    statIdx = self._readInt(fd)
                    low = word.lower()
                    if w.find(low) != -1:
                        matches.append({'word': word, 'match': w,
                         'index': statIdx, 'full': len(low) == len(w)})
                    w = self._readString(fd)

                count = 0
                totalHi = 0
                totalFreqHi = 0
                totalFreqLo = 0

                for match in matches:
                    multiplier = 1
                    if match['full']:
                        multiplier = 2

                    fd.seek(match['index'])
                    numDocs = self._readInt(fd)

                    for i in range(numDocs):
                        idx = self._readInt(fd)
                        if idx == -1:
                            freq = 0
                        else:
                            freq = self._readInt(fd)
                        results.append({'idx': idx, 'freq': freq >> 1,
                          'hi': freq & 1, 'multi': multiplier})
                        if freq & 1:
                            totalHi += 1
                            totalFreqHi += freq * multiplier
                        else:
                            totalFreqLo += freq * multiplier

                    for i in range(numDocs):
                        if results[count]['idx'] == -1:
                            results[count]['name'] = ''
                            results[count]['url'] = ''
                            count += 1
                            continue
                        fd.seek(results[count]['idx'])
                        name = self._readString(fd)
                        url = self._readString(fd)
                        results[count]['name'] = name
                        results[count]['url'] = self.html_output + '/' + url
                        count += 1

                totalFreq = (totalHi + 1) * totalFreqLo + totalFreqHi
                for i in range(count):
                    freq = results[i]['freq']
                    multi = results[i]['multi']
                    if results[i]['hi']:
                        results[i]['rank'] = float(freq*multi + totalFreqLo) \
                          / float(totalFreq)
                    else:
                        results[i]['rank'] = float(freq*multi) \
                          / float(totalFreq)
        return results

    def _computeIndex(self, word):
        if len(word) < 2:
            return -1

        hi = ord(word[0].lower())
        if hi == 0:
            return -1

        lo = ord(word[1].lower())
        if lo == 0:
            return -1

        return hi * 256 + lo

    def _readInt(self, fd):
        b1 = fd.read(1)
        b2 = fd.read(1)
        b3 = fd.read(1)
        b4 = fd.read(1)
        
        if not b1 or not b2 or not b3 or not b4:
            return -1;

        return (ord(b1) << 24) | (ord(b2) << 16) | (ord(b3) << 8) | ord(b4)

    def _readString(self, fd):
        result = ''
        byte = fd.read(1)
        while byte != '\0':
            result = ''.join([result, byte])
            byte = fd.read(1)
        return result
