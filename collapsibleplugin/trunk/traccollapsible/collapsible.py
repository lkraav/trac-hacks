#   Copyright 2010 Matthew Noyes
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

from io import StringIO

from trac.wiki.formatter import OneLinerFormatter
from trac.wiki.macros import WikiMacroBase

class CollapsibleStartMacro(WikiMacroBase):
    """CollapsibleStartMacro marks the start of a collapsible list

    Example:
    `[[CollapsibleStart(Title)]]`
     """

    def expand_macro(self, formatter, name, content):
        title = StringIO()
        OneLinerFormatter(self.env, formatter.context).format(content, title)
        title = title.getvalue()

        return("<div class=\"collapsed collapsibleplugin\"> " +
               "<h3 class=\"foldable\">" + title + "</h3>" +
               "<div>")

class CollapsibleEndMacro(WikiMacroBase):
    r"""CollapsibleEndMacro marks the end of a collapsible list

    Example:
    `[[CollapsibleEnd]]`
    """
    def expand_macro(self, formatter, name, content):
        return("</div></div>")
