#   Copyright 2010 Matthew Noyes <thecodingking at gmail.com>   
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

__author__ = 'Matthew Noyes'

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script
from trac.wiki.macros import WikiMacroBase


class CollapsibleStartMacro(WikiMacroBase):
    """CollapsibleStart macro marks the start of a collapsible list

    Example: `[[CollapsibleStart(Title)]]`
     """
    implements(ITemplateProvider)

    def expand_macro(self, formatter, name, content):

        # Make sure we don't call enableFolding more than once on a page.
        folding_chrome_path = 'common/js/folding.js'
        if folding_chrome_path not in formatter.req.chrome['scriptset']:
            add_script(formatter.req, folding_chrome_path)
            add_script(formatter.req, 'collapsible/collapsible.js')

        return '<div class="collapsed"><h3 class="foldable">%s</h3><div>' % content

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('collapsible', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


class CollapsibleEndMacro(WikiMacroBase):
    r"""CollapsibleEnd macro marks the end of a collapsible list

    Example: `[[CollapsibleEnd]]`
    """
    def expand_macro(self, formatter, name, content):
        return '</div></div>'
