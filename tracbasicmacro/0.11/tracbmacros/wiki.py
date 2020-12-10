
# Copyright 2009-2011 Olemis Lang <olemis at gmail.com>
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


r"""Display information about wiki pages

Copyright 2009-2011 Olemis Lang <olemis at gmail.com>
Licensed under the Apache License
"""
__author__ = 'Olemis Lang'

from trac.core import TracError
from trac.config import ListOption, Option
from trac.resource import Resource
from trac.util.datefmt import format_datetime, localtz
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage

from genshi.builder import tag

class WikiHistoryMacro(WikiMacroBase):
    r"""Embed information about wiki changelog in wiki pages.
    If invoked without keyword arguments then full 
    changelog is shown inside a table with columns 
    `Fecha`, `Version`, `Descripcion, `Autor`. Column labels 
    may be customized using `chgtable_titles` option in `wiki` 
    section. CSS class used to render the table may be specified 
    through `chgtable_class` option in `wiki` section 
    (see TracIni if you need help). Please read below for further 
    details.
    
    Usage is as follows (all fields are optional).
    
    `[[WikiHistory(pagename, version, attr=attr_name, cols=columns)]]`
    
    ''pagename'' : the name of target Wiki page. If missing or empty 
                   and a wiki page is being rendered then it defaults to 
                   the current wiki page. If the page being rendered 
                   doesn't belong in the Wiki then 'WikiStart' is used instead.
    ''version'' :  consider changes prior to (and including) this version
    ''attr'' :     if this keyword argument is present then only the value 
                   of the version attribute identified by `attr_name` is 
                   rendered in textual form (and `cols` argument is ignored)
                   Supported values are `time`, `version`, 
                   `comment`, and `author`
    ''cols'' :     colon separated list of identifiers used to select 
                   specific columns (order matters). Identifiers are 
                   the same supported for `attr` parameter.
    """
    
    table_class = Option('wiki', 'chgtable_class', 'listing', 
                                doc=_("""CSS class to render wiki history table"""))
    labels = ListOption('wiki', 'chgtable_titles', u'Version, Date, Author, Comment', 
                                keep_empty=True,
                                doc=_("""Comma separated list of column labels for """
                                """version, time, author, and comment (in that order)"""),
                                )
    
    def expand_macro(self, formatter, name, content):
        args, kw = parse_args(content)
        attr, cols = [kw.get(k) for k in ('attr', 'cols')]
        resource = formatter.context.resource
        is_wiki = isinstance(resource, Resource) and resource.realm == 'wiki'
        try :
            pagename = args[0]
        except IndexError :
            if not is_wiki :
                raise TracError(_('You must specify page name in this context'))
            page = WikiPage(self.env, resource, version=resource.version)
        else :
            pagename = pagename or (is_wiki and resource.id or 'WikiStart')
            version = (args[1:2] or [None])[0]
            page = WikiPage(self.env, pagename, version=version)
        ALL_ATTRS = ['version', 'time', 'author', 'comment']
        ATTR_LABELS = self.labels
        ATTR_LABELS = (len(ATTR_LABELS) == len(ALL_ATTRS)) and \
                        ATTR_LABELS or [_('Version'), _('Date'), _('Author'), _('Comment')]
        
        def format_verinfo(value, attridx):
            return {
                       1 : lambda x : tag.i(format_datetime(x, '%d/%m/%Y %H:%M:%S', tzinfo=localtz)), 
                       0 : lambda x : tag.b(to_unicode(x, 'utf-8')), 
                       3 : lambda x : to_unicode(x or _('(No comments)'), 'utf-8'),
                       2 : lambda x : tag.i(to_unicode(x, 'utf-8')),
                   }.get(attridx, lambda x : tag.i(_('Atributo desconocido')) ) (value)
        
        if attr is None :
            if cols :
                cols = [ALL_ATTRS.index(x) for x in cols.split(':') if x in ALL_ATTRS ]
            else :
                cols = xrange(len(ALL_ATTRS))
            def ver_row(verinfo):
                return tag.tr([verinfo[c] for c in cols])
            return tag.table(
                            tag.thead([tag.tr(
                                        [tag.th(tag.i(h or ''))
                                            for h in (ATTR_LABELS[c] for c in cols)]
                                   )]),
                            tag.tbody([tag.tr(
                                        [tag.td(format_verinfo(x[c], c))
                                                for c in cols]
                                    ) for x in page.get_history()]), 
                            class_=self.table_class, align='center')
        else :
            try :
                attridx = ALL_ATTRS.index(attr)
            except ValueError :
                raise TracError(_('Invalid attribute name %s') % (attr,))
            else :
                return format_verinfo(getattr(page, attr, None), attridx)

