# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.core import escape
from trac.core import implements
from trac.web.chrome import add_script, ITemplateProvider
from trac.wiki.macros import WikiMacroBase

class MermaidMacro(WikiMacroBase):
    implements(ITemplateProvider)

    def expand_macro(self, formatter, name, content):
        self.log.debug("content=%s" % content)
        add_script(formatter.req, 'mermaid/mermaid.min.js')
        add_script(formatter.req, 'mermaid/tracmermaid.js')
        return '<div class="mermaid">%s</div>' % escape(content)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename 
        return [('mermaid', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
