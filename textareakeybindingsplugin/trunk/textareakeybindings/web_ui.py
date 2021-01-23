# -*- coding: utf-8 -*-

import pkg_resources
import re
try:
    from StringIO import StringIO # Python 2
except ImportError:
    from io import StringIO # Python 3

from trac.core import *
from trac.web import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_script_data
from trac.wiki.interwiki import InterWikiMap


class TextareaKeyBindingsModule(Component):
    """Better keybindings for <textarea> controls."""

    implements(ITemplateProvider, IRequestFilter)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if (req.path_info.startswith('/wiki') or
            req.path_info.startswith('/ticket') or
            req.path_info.startswith('/newticket')):
            self.env.log.debug('Injecting textareakeybindings.js')

            def url_pattern_to_re(name, url):
                if not '$' in url:
                    return name + ":", re.escape(url)
                outer = [name]
                def repl(matchobj):
                    outer[0] += ":$" + matchobj.group(1)
                    return '(.+)'
                url = re.sub(r'\\\$(\d)', repl, re.escape(url))
                return outer[0], url
            def sortkey(tuple):
                name, url, title = tuple
                return len(url)
            tuples = InterWikiMap(self.env).interwiki_map.values()
            links = [url_pattern_to_re(name, url)
                     for name, url, title
                     in sorted(tuples, key=sortkey, reverse=True)]

            baseurl_pattern = '%s/(\w+)/(\S+)' % (re.escape(req.base_url),)
            script_data = {
                'baseurl_pattern': baseurl_pattern,
                'links': links,
            }
            add_script_data(req, {'textareakeybindings': script_data})
            add_script(req, 'textareakeybindings/js/textareakeybindings.js')
        return (template, data, content_type)

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return [('textareakeybindings', pkg_resources.resource_filename('textareakeybindings', 'htdocs'))]

    def get_templates_dirs(self):
        return []
