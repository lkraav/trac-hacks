# -*- coding: utf-8 -*-
import re, time
from StringIO import StringIO

from genshi.builder import tag

from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.util.html import html, plaintext, Markup
from trac.web.chrome import add_stylesheet, add_script, Chrome, ITemplateProvider
from trac.wiki.api import parse_args, IWikiMacroProvider
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule
from trac.mimeview.api import IContentConverter, IHTMLPreviewRenderer
from pkg_resources import resource_filename
import random
import string

import fdx2fountain

class ScrippetRenderer(Component):
    implements(ITemplateProvider, IHTMLPreviewRenderer)

    ## IHTMLPreviewRenderer
    def get_quality_ratio(self, mimetype):
        self.log.debug("ScrippetRenderer quality for mimetype: %s" % mimetype)
        if mimetype == "text/fdx" or mimetype == "text/fountain":
            return 9
        
    def render(self, context, mimetype, content, filename=None, url=None):
        add_stylesheet(context.req, 'scrippets/css/fountain-js.css')
        add_stylesheet(context.req, 'scrippets/css/normalize.min.css')
        add_script(context.req, 'scrippets/js/fountain.min.js')
        add_script(context.req, 'scrippets/js/fountain-reader.js')
        if hasattr(content, 'read'):
            content = content.read()
        
        if mimetype.startswith("text/fdx"):
            fountain_content = fdx2fountain.Fdx2Fountain().fountain_from_fdx(content)
        else:
            fountain_content = content

        data = {
                'fountain': to_unicode(fountain_content),
                'inline': False,
                'fnid': "fn" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
               }
        return Chrome(self.env).render_template(context.req,
                      'fountain.html', data=data, fragment=True)
    
    ## ITemplateProvider
    def get_htdocs_dirs(self):
        return [('scrippets', resource_filename(__name__, 'htdocs'))]
                                      
    def get_templates_dirs(self):
        return [resource_filename('scrippets', 'templates')]
