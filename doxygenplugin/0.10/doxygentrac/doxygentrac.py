# vim: ts=4 expandtab
#
# Copyright (C) 2005 Jason Parks <jparks@jparks.net>. All rights reserved.
#

from __future__ import generators

import os
import time
import posixpath
import re
import mimetypes

from trac.config import Option
from trac.core import *
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
  add_stylesheet
from trac.Search import ISearchSource
from trac.wiki import WikiSystem, IWikiSyntaxProvider
from trac.wiki.model import WikiPage
from trac.wiki.formatter import wiki_to_html, system_message
from trac.util.html import html

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
            yield 'mainnav', 'doxygen', html.a(self.title,
                                               href=req.href.doxygen())

    # IRequestHandler methods

    def match_request(self, req):
        if re.match(r'^/doxygen(?:$|/)', req.path_info):
            segments = filter(None, req.path_info.split('/'))
            segments = segments[1:] # ditch 'doxygen'
            action, path, link = self._doxygen_lookup(segments)
            req.args['action'] = action
            if action == 'search' and link:
                req.args['query'] = link
            elif action == 'redirect':
                req.args['link'] = link
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

        # Handle /doxygen request
        if action == 'index':
            if self.wiki_index:
                if WikiSystem(self.env).has_page(self.wiki_index):
                    req.redirect(req.href.wiki(self.wiki_index))
                # Display missing wiki
                text = wiki_to_html('Doxygen index page [wiki:%s] does not '
                                    'exists' % self.wiki_index, self.env, req)
                req.hdf['doxygen.text'] = system_message('Error', text)
                return 'doxygen.cs', 'text/html'
            path = os.path.join(self.base_path, self.default_doc, self.index)

        # view 
        mimetype = mimetypes.guess_type(path)[0]
        if mimetype == 'text/html':
            add_stylesheet(req, 'doxygen/css/doxygen.css')
            req.hdf['doxygen.path'] = path
            return 'doxygen.cs', 'text/html'
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
        if not 'doxygen' in filters:
            return

        # We have to search for the raw bytes...
        keywords = [k.encode(self.encoding) for k in keywords]

        for doc in os.listdir(self.base_path):
            # Search in documentation directories
            path = os.path.join(self.base_path, doc)
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
            index = os.path.join(self.base_path, 'search.idx')
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
            action, path, link = self._doxygen_lookup(params.split('/'))
            if action == 'index':
                return html.a(label, title=self.title,
                              href=formatter.href.doxygen())
            if action == 'redirect':
                if path:
                    return html.a(label, title="Search result for "+params,
                                  href=formatter.href.doxygen(path=path)+link)
                else:
                    action = 'view'
            if action in ('view', 'index'):
                return html.a(label, title=params,
                              href=formatter.href.doxygen(link, path=path))
            else:
                return html.a(label, title=params, class_='missing',
                              href=formatter.href.doxygen())
        yield ('doxygen', doxygen_link)

    def get_wiki_syntax(self):
        return []

    # internal methods

    def _doxygen_lookup(self, segments):
        """Try to interpret path components as a request for doxygen targets

        Return an `(action,path,link)` pair, where:
         - `action` describes what should be done (one of 'view',
           'search' or 'index'),
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
                return 'redirect', None, \
                       self.default_doc + '/' + (file or self.index)
            else:
                doc = ''
        
        def lookup(file, category='undefined'):
            """Build (full path, relative link) and check if path exists."""
            path = os.path.join(self.base_path, doc, file)
            self.log.debug('%s file "%s" (at %s)' % (category, file, path))
            return os.path.exists(path) and path, doc + '/' + file

        self.log.debug('looking up "%s" in documentation "%s"' % (file, doc))

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
        path, link = lookup('class%s.html' % file, 'class')
        if not path:
            path, link = lookup('struct%s.html' % file, 'struct')
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
                    return 'redirect', path, target
        self.log.debug('%s not found in %s' % (file, doc))
        return 'search', None, file

    def _search_in_documentation(self, doc, keywords):
        # Open index file for documentation
        index = os.path.join(self.base_path, doc, 'search.idx')
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
                        freq = self._readInt(fd)
                        results.append({'idx': idx, 'freq': freq >> 1,
                          'hi': freq & 1, 'multi': multiplier})
                        if freq & 1:
                            totalHi += 1
                            totalFreqHi += freq * multiplier
                        else:
                            totalFreqLo += freq * multiplier

                    for i in range(numDocs):
                        fd.seek(results[count]['idx'])
                        name = self._readString(fd)
                        url = self._readString(fd)
                        results[count]['name'] = name
                        results[count]['url'] = url
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

        return (ord(b1) << 24) | (ord(b2) << 16) | (ord(b3) << 8) | ord(b4)

    def _readString(self, fd):
        result = ''
        byte = fd.read(1)
        while byte != '\0':
            result = ''.join([result, byte])
            byte = fd.read(1)
        return result
