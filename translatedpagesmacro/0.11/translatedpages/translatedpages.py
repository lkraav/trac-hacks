# -*- coding: utf-8 -*-

""" Macro to show the translated pages list. """

__author__ = 'Zhang Cong (ftofficer)'
__version__ = '1.0'

from genshi.builder import tag

from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider
from trac.wiki.api import IWikiMacroProvider
from StringIO import StringIO
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage

class TranslatedPagesMacro(Component):
    """Plugin to show the translated pages list."""

    implements(IWikiMacroProvider, IRequestHandler, ITemplateProvider)

    # IWikiMacroProvider methods

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        yield u'TranslatedPages'

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return to_unicode(inspect.getdoc(self.__class__))

    def parse_macro(self, parser, name, content):
        raise NotImplementedError


    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == u'/translations'

    def process_request(self, req):
        return u'translatedpages.cs', None


    # ITemplateProvider methods

    def get_templates_dirs(self):
        """Return a list of directories containing the provided ClearSilver
        templates.
        """

        from pkg_resources import resource_filename
        return [resource_filename(__name__, u'templates')]

    SUPPORT_LANGUAGES = {
        u'en' : u'English',
        u'ru' : u'Русский',
        u'be' : u'Беларуская мова',
        u'da' : u'dansk',
        u'es' : u'español',
        u'nl' : u'Nederlands',
        u'sv' : u'Svenska',
        u'zh' : u'中文',
        }

    def __init__(self):
        self.supported_languages = TranslatedPagesMacro.SUPPORT_LANGUAGES.keys()
        self.supported_languages.sort()

    def _get_language_name(self, lang_code):
        if TranslatedPagesMacro.SUPPORT_LANGUAGES.has_key(lang_code):
            return TranslatedPagesMacro.SUPPORT_LANGUAGES[lang_code]
        else:
            return lang_code

    def _seems_like_lang_code(self, lang_code):
        if len(lang_code) != 2 : return False
        if not lang_code.islower() : return False
        return lang_code.isalpha()

    def _get_wiki_info(self, wiki_id):
        wiki_lang_code = u'en'
        wiki_base_name = wiki_id

        wiki_lang_code_start = wiki_id.rfind(u'/')
        if wiki_lang_code_start != -1:
            wiki_lang_code = wiki_id[wiki_lang_code_start+1:]
            wiki_base_name = wiki_id[:wiki_lang_code_start]

        if wiki_lang_code not in TranslatedPagesMacro.SUPPORT_LANGUAGES.keys(): # Unknown wiki language.
            if not self._seems_like_lang_code(wiki_lang_code): # seems don't like a language code.
                wiki_lang_code = u'en'
                wiki_base_name = wiki_id

        return (wiki_base_name, wiki_lang_code)

    def _is_translated_wiki_exists(self, wiki_base_name, lang_code):
        if lang_code == u'en':
            wiki_id = wiki_base_name
        else:
            wiki_id = u'%s/%s' % (wiki_base_name, lang_code)

        wiki_page = WikiPage(self.env, wiki_id)
        return wiki_page.exists

    def _get_lang_link(self, wiki_base_name, lang_code, formatter):
        if lang_code != u'en':
            wiki_id = u'%s/%s' % (wiki_base_name, lang_code)
        else:
            wiki_id = wiki_base_name

        text = u'  * [wiki:%s %s]' % (wiki_id, self._get_language_name(lang_code))

        return text

    def expand_macro(self, formatter, name, args):
        """Return a list of translated pages with the native language names.
        The list of languages supported can be configured by the SUPPORT_LANGUAGES
        class member. Refer to iso639.1 for more information.
        """

        wiki_id = formatter.context.resource.id

        (wiki_base_name, wiki_lang_code) = self._get_wiki_info(wiki_id)

        lang_link_list = []

        for lang_code in self.supported_languages:
            if self._is_translated_wiki_exists(wiki_base_name, lang_code):
                if lang_code != wiki_lang_code:
                    lang_link_list.append(self._get_lang_link(wiki_base_name, lang_code, formatter))

        text = u'\n'.join(lang_link_list)

        out = StringIO()
        Formatter(self.env, formatter.context).format(text, out)

        return u'<div class="wiki-toc trac-nav"><h4>Other Languages:</h4>' + out.getvalue() + u'</div>'
