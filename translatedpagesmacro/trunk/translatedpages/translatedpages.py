# -*- coding: utf-8 -*-

import re
import inspect
from io import StringIO

from trac.config import Option
from trac.core import *
from trac.resource import get_resource_url
from trac.util.html import Markup, tag, unescape
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.wiki.api import IWikiMacroProvider, IWikiSyntaxProvider, WikiSystem, parse_args
from trac.wiki.formatter import Formatter, OneLinerFormatter, system_message, split_url_into_path_query_fragment, concat_path_query_fragment
from trac.wiki.model import WikiPage


class TranslatedPagesMacro(Component):
    """
    Macro to show the translated pages list.
    """
    implements(IWikiMacroProvider, IWikiSyntaxProvider)

    lang_page_name = Option('translatedpages', 'languages_page', 'TracLanguages',
        """Page name of table containing available languages""")

    page_code = Option('translatedpages', 'template', '{lang}:{page}',
        """Page name template of translated pages""")

    base_lang = Option('translatedpages', 'base_language', 'En',
        """Base language to be used without prefix/suffix""")


    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('wikitr', self._format_link)

    def _format_link(self, formatter, ns, name, label):
        self._update_languages()
        res = formatter.context.resource
        prefix = ""
        base_page_name = ""
        lang_code = self.base_lang
        if res.realm == "wiki":
          prefix, base_page_name, lang_code = self._get_page_info(res.id)
        origcode = self.extensions.get(lang_code, '')
        if label == name:
          label = ""
        r = re.compile("^'(.*)':(.*)$").search(name)
        if r == None:
          r = re.compile("^\"(.*)\":(.*)$").search(name)
          if r == None:
            r = re.compile("^(.*):(.*)$").search(name)
        if r != None:
          origcode = r.group(1)
          if origcode == "":
            origcode = "{t}"
          name = r.group(2)

        name,query,fragment = split_url_into_path_query_fragment(name)
        if lang_code == self.base_lang:
          if name[0] != '/':
            i = base_page_name.rfind("/")
            if i > 0:
              name = base_page_name[:i+1] + name
          else:
            name = name[1:]
          origcode = "{t}"
        else:
          if name[0] == '/':
            oname = name[1:]
          else:
            i = base_page_name.rfind("/")
            if i > 0:
              oname = base_page_name[:i+1] + name
            else:
              oname = name
          tname = self._get_translated_page(prefix, oname, lang_code);
          if not WikiPage(self.env, tname).exists:
            name = oname
          else:
            name = tname
            origcode = "{t}"
        label = unescape(Markup(self._get_label_text(origcode, label, name)))
        p = WikiPage(self.env, name)
        url = get_resource_url(self.env, p.resource, formatter.req.href)
        url = concat_path_query_fragment(url, query, fragment)
        return tag.a(label, href=url, class_=("wiki" if p.exists else "missing wiki"))

    def _get_label_text(self, code, label, name):
        return code.replace("{t}", label if label else name) \
                   .replace("{b}", self.base_lang) \
                   .replace("{c}", self.base_lang.lower()) \
                   .replace("{n}", self.languages[self.base_lang])

    # IWikiMacroProvider methods

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        yield 'TranslatedPages'

    def get_macro_description(self, name):
        return """Macro to show the translated pages list.

Simply calling that macro in a page adds a menu linking to all available translations of a page.

A language page (usually [wiki:TracLanguages]) must provide the language codes as a table
with following entries:
{{{
||<language code>||<language name>||<english name>||<description>||<base language link indication>||
}}}
The description contains the text displayed above language links in that language
(usually a variant of 'Other languages').
A table title line starting with {{{||=}}} is not parsed.

The base language link indication is the default value for wikitr: links (see below) and describes how links to base language should be formatted. It must contain
one {t} which is replaced by the label (e.g. **{t} (en)** to append a note in brackets). Other parameters are {b} for the base language code, {c} for the base
language code in lowercase letters and {n} for the base language name.

The Macro accepts arguments as well:
 * '''revision=<num>'''   to specify the version of the base page when last translated, a negative revision indicates that a page needs updating in the status overview table
 * '''outdated=<text>'''  mark the page as outdated with given comment
 * '''silent'''           don't output empty chapter for show options when nothing is shown

 * '''showoutdated'''     to show all pages, where revision does not match base revision
 * '''showmissing'''      to show all pages, where translation is missing
 * '''showproblems'''     to show all pages which have problems
 * '''showuntranslated''' to show all untranslated pages
 * '''showstatus'''       to show one big status table
 * '''skipmissing'''      skip links to missing pages in status table (speed up display a lot)
 * '''lang=<code>'''      to restrict output of show outdated, status or missing to a specific language

 * '''label_outdated'''   label to display when using the showoutdated option
 
Use wikitr:[basetext:] in links to reference the translated form of a page when it exists, the original otherwise. In case the optional part **basetext**: is used this text
is used to indicate links to the base language (see above for format, an empty base language text, i.e. two colons, leads to unchanged text). When using these links translators do not need
to update links when they step by step add translated pages. Using this macro on the base langue pages does no harm, but may help in translation when doing copy and paste.

Links can look like {{{[[wikitr:Link|Label]]}}}, {{{[wikitr:{t} ({n}):Link|Label]]}}}, {{{[[wikitr::Link|Label]]}}}, {{{[wikitr:Link]}}}, {{{[wikitr:Link Label]}}} and so on (see TracLinks).
"""

    # Language forms:
    # De:
    # De_DE:
    # Ca-Valencia:
    # Use - instead of @ for dialects (i.e. Ca-Valencia instead of Ca@Valencia), as @ is not supported in page names
    langcode_re = Option('translatedpages', 'regexp', '([A-Z][a-z]{1,2}(?:_[A-Z]{2}|-[A-Z][a-z]+)?)',
        """Regular expression to match a language code""")

    outdated_tx = "<p style=\"background-color:rgb(253,255,221);padding: 10pt; border-color:rgb(128,128,128);border-style: solid; border-width: 1px;\">%s</p>\n"

    macro_re = re.compile("\[\[TranslatedPages(?:\((.+)\))?\]\]")
    revision_re = re.compile("\[\[TranslatedPages(?:\(.*?revision=(-?\d+).*?\))?\]\]")
    outdated_re = re.compile("\[\[TranslatedPages(?:\((?:.*,)?outdated=(.*)\))?\]\]")

    def __init__(self):
        self.langpage_re = re.compile("^\|\|"+ self.langcode_re + "\|\|(.+?)\|\|(.+?)\|\|(.+?)\|\|(?:[\"']?(.+?)[\"']?\|\|)?$")
        self.languages_page_version = 0
        self._update_languages()
        self.template_re = re.compile(self.page_code \
            .replace('{lang}', r'(?P<lang>%s)' % self.langcode_re) \
            .replace('{page}', r'(?P<page>.+?)') + '$')

    def _parse_languages_list(self, text):
        langs = {}
        descr = {}
        langse = {}
        extensions = {}
        for line in text.replace('\r','').split('\n'):
            regres = self.langpage_re.search(line)
            if regres == None:
                if not line.startswith('||=') and line.strip():
                    self.env.log.debug(
                        "Wrong line syntax while parsing languages list: %s", line)
            else:
                code = regres.group(1)
                name = regres.group(2)
                engname = regres.group(3)
                desc = regres.group(4)
                extension = regres.group(5)
                if extension == None:
                  extension = "{t}"
                self.env.log.debug("Adding language %s -> %s [%s] (%s) (%s)", code,
                                   name, engname, desc, extension)
                langs[code] = name
                descr[code] = desc
                langse[code] = engname
                extensions[code] = extension
        return (langs, descr, langse, extensions)

    def _update_languages(self):
        languages_page = WikiPage(self.env, self.lang_page_name)
        if not languages_page.exists:
            self.env.log.warn("Can't find page %s", self.lang_page_name)
            self.languages = {}
            self.languages_page_version = 0
        else:
            if languages_page.version > self.languages_page_version:
                (self.languages, self.description, self.languagesbase, self.extensions) = \
                    self._parse_languages_list(languages_page.text)
                self.languages_page_version = languages_page.version

    def _get_language_name(self, lang_code):
        self._update_languages()
        return self.languages.get(lang_code, lang_code)

    def _get_translated_page(self, prefix, name, lang_code):
        if lang_code != self.base_lang:
            name = self.page_code.replace('{lang}', lang_code) \
                                 .replace('{page}', name)
        return prefix + name

    def _get_page_info(self, page_name):
        m = self.template_re.search(page_name)
        if m:
            page, lang = m.group('page'), m.group('lang')
            prefix = m.start()
        else:
            page = page_name
            lang = self.base_lang
            prefix = 0
            pages = WikiSystem(self.env).get_pages()
            for testpage in pages:
                m = self.template_re.search(testpage)
                if m and page_name == self._get_translated_page( \
                    testpage[:m.start()], m.group('page'), lang):
                        page = m.group('page')
                        prefix = m.start()
                        break
        return (page_name[:prefix], page, lang)

    def _get_translations(self, prefix, base_page_name):
        res = []
        for l in sorted(self.languages.keys()):
            tr = self._get_translated_page(prefix, base_page_name, l);
            if WikiSystem(self.env).has_page(tr):
                res.append(l)
        return res

    def _get_outdated(self, lang, label):
        if label != None:
            res = "== %s ==\n" % label
        elif lang != None:
            langd = lang
            if lang in self.languagesbase:
                langd = self.languagesbase[lang]
            res = "== Outdated pages for %s ==\n" % langd
        else:
            res = "== Outdated pages ==\n"
        found = 0;
        for page in sorted(WikiSystem(self.env).get_pages()):
            pagetext = WikiPage(self.env, page).text
            if pagetext:
                regres = self.revision_re.search(pagetext)
                out = self.outdated_re.search(pagetext)
                outcode = ""
                outver = ""
                prefix, base_page_name, lang_code = self._get_page_info(page)
                if out != None and out.group(1) != None and (lang == None \
                or lang == lang_code or lang_code == self.base_lang):
                    outcode = "{{{%s}}}" % out.group(1).replace("\,",",")
                if regres != None and regres.group(1) != None:
                    if lang_code != self.base_lang and (lang == None or lang == lang_code):
                        newver = WikiPage(self.env, base_page_name).version
                        oldver = abs(int(regres.group(1)))
                        if(newver != oldver):
                            outver = "[[wiki:/%s?action=diff&old_version=%s|@%s-@%s]]" \
                            % (base_page_name, oldver, oldver, newver)
                if outcode != "" or outver != "":
                    res += "|| [[wiki:/%s]] || %s || %s ||\n" % (page, outver, outcode)
                    found += 1

        if found == 0:
            res += 'none\n'
        return res

    def _get_missing(self, lang):
        res = ""
        base_pages = []
        for page in sorted(WikiSystem(self.env).get_pages()):
            text = WikiPage(self.env, page).text
            if text:
                for line in text.replace('\r','').split('\n'):
                    regres = self.macro_re.search(line)
                    if regres != None:
                        (prefix, base_page_name, lang_code) = self._get_page_info(page)
                        basename = self._get_translated_page(prefix, \
                            base_page_name, self.base_lang)
                        if not basename in base_pages:
                            base_pages.append(basename)
        langs = []
        if lang != None:
            langs = [lang]
        else:
            langs = list(self.languages.keys())
            langs.sort()
        for l in langs:
            reslang = ""
            for base_page in base_pages:
                (prefix, page, lang_code) = self._get_page_info(base_page)
                tr = self._get_translated_page(prefix, page, l);
                if not WikiSystem(self.env).has_page(tr):
                    reslang += " * [[wiki:/%s]]\n" % tr
            if len(reslang) > 0:
                langd = l
                if l in self.languagesbase:
                    langd = self.languagesbase[l]
                res += "== Missing pages for %s ==\n%s" % (langd, reslang)

        if len(res) == 0:
            res += '== Missing pages ==\nnone\n'
        return res

    def _get_untranslated(self, silent):
        res = ""
        for page in sorted(WikiSystem(self.env).get_pages()):
            text = WikiPage(self.env, page).text
            if text and self.macro_re.search(text) == None:
                res += " * [[wiki:/%s]]\n" % page

        if len(res) == 0:
            if(silent):
                return " "
            res = 'none\n'
        return "== Untranslated pages ==\n"+res

    def _check_args(self, page, argstr, lang_code):
        if argstr == None or len(argstr) == 0:
            if lang_code != self.base_lang:
                return "||[[wiki:/%s]]|| ||No revision specified for translated page\n" \
                    % page
            else:
                return ""
        resargs = ""
        args, kw = parse_args(argstr)
        show = False
        for arg in args:
            if arg == 'showoutdated' or arg == 'showuntranslated' or \
                arg == 'showmissing' or arg == 'showstatus' or arg == 'showproblems':
                    show = True;
            elif arg != 'silent' and arg != 'skipmissing':
                resargs += "||[wiki:/%s]||%s||unknown argument '%s'||\n" % (page, argstr, arg)
        for arg in list(kw.keys()):
            if arg == 'lang':
                if not ('showoutdated' in args or 'showmissing' in args or \
                    'showstatus' in args):
                        resargs += "||[[wiki:/%s]]||%s||'lang' argument without proper show argument'||\n" \
                            % (page, argstr)
                elif kw[arg] not in self.languages:
                    resargs += "||[[wiki:/%s]]||%s||'lang'='%s' argument uses unknown language||\n" \
                        % (page, argstr, kw[arg])
            elif arg == 'revision':
                try:
                    int(kw[arg])
                    #if int(kw[arg]) < 0:
                    #    resargs += "||[[wiki:/%s]]||%s||'revision'='%s' is no positive value||\n" \
                    #        % (page, argstr, kw[arg])
                except:
                    resargs += "||[[wiki:/%s]]||%s||'revision'='%s' is no integer value||\n" \
                        % (page, argstr, kw[arg])
                if show:
                    resargs += "||[[wiki:/%s]]||%s||'revision'='%s' used with show argument||\n" \
                        % (page, argstr, kw[arg])
                elif lang_code == self.base_lang:
                    resargs += "||[[wiki:/%s]]||%s||Revision specified for base page\n" \
                        % (page, argstr)
            elif arg != 'outdated' and arg != 'label_outdated':
                resargs += "||[[wiki:/%s]]||%s||unknown argument '%s'='%s'||\n" \
                    % (page, argstr, arg, kw[arg])
        if lang_code != self.base_lang and 'revision' not in kw and not show:
            resargs += "||[[wiki:/%s]]||%s||No revision specified for translated page\n" \
                % (page, argstr)
        return resargs

    def _get_problems(self, silent):
        res = ""
        resargs = ""
        respages = ""
        base_pages = []
        for page in sorted(WikiSystem(self.env).get_pages()):
            text = WikiPage(self.env, page).text
            if text:
                for line in text.replace('\r','').split('\n'):
                    regres = self.macro_re.search(line)
                    if regres != None:
                        (prefix, base_page_name, lang_code) = self._get_page_info(page)
                        basename = self._get_translated_page(prefix, \
                            base_page_name, self.base_lang)
                        if not basename in base_pages:
                            base_pages.append(basename)
                        resargs += self._check_args(page, regres.group(1), lang_code)
                        if self.languages.get(lang_code, None) == None:
                            respages += "||[[wiki:/%s]]||Translated page language code unknown||\n" % page

        base_pages.sort()
        for base_page in base_pages:
            (prefix, page, lang_code) = self._get_page_info(base_page)
            translations = self._get_translations(prefix, page)
            basever = 0;
            if not self.base_lang in translations:
                respages += "||[[wiki:/%s]]||Base language is missing for translated pages||\n" % base_page
            else:
                basever = WikiPage(self.env, base_page).version
            for translation in translations:
                transpage = self._get_translated_page(prefix, page, translation)
                regres = self.macro_re.search(WikiPage(self.env, transpage).text)
                if regres != None:
                    argstr = regres.group(1)
                    if argstr != None and len(argstr) > 0:
                         args, kw = parse_args(argstr)
                         try:
                             rev = int(kw['revision'])
                             if rev != 0 and rev > basever:
                                 respages += "||[[wiki:/%s]]||Revision %s is higher than base revision %s||\n" \
                                     % (transpage, rev, basever)
                         except:
                             pass
                else:
                    respages += "||[[wiki:/%s]]||Translated page misses macro 'TranslatedPages'||\n" % transpage

        if len(resargs):
            res += "=== Errors in supplied arguments ===\n||= Page =||= Arguments =||= Issue =||\n"+resargs
        if len(respages):
            res += "=== Errors in page structure ===\n||= Page =||= Issue =||\n"+respages

        if not len(res):
            if(silent):
                return " "
            res = 'none\n'
        return "== Problem pages ==\n" + res;

    def _get_status(self, lang, skipmissing):
        res = ""

        base_pages = []
        langs = []
        errors = []
        for page in sorted(WikiSystem(self.env).get_pages()):
            text = WikiPage(self.env, page).text
            if text:
                for line in text.replace('\r','').split('\n'):
                    regres = self.macro_re.search(line)
                    if regres != None:
                        (prefix, base_page_name, lang_code) = self._get_page_info(page)
                        basename = self._get_translated_page(prefix, \
                            base_page_name, self.base_lang)
                        if not basename in base_pages:
                            base_pages.append(basename)
                        if len(self._check_args(page, regres.group(1), lang_code)) > 0:
                            errors.append(page)
                        if not lang_code in langs:
                            langs.append(lang_code)

        if lang != None:
            langs = [lang]
        else:
            langs.sort()
            res += "\n||= Page =||= " + (" =||= ".join(langs)) + "=||\n"
        base_pages.sort()

        for base_page in base_pages:
            (prefix, page, lang_code) = self._get_page_info(base_page)
            basever = 0;
            if WikiSystem(self.env).has_page(base_page):
                basever = WikiPage(self.env, base_page).version
            if lang == None:
                res += "||[[wiki:/%s]]" % base_page
            for l in langs:
                color = "green"
                transpage = self._get_translated_page(prefix, page, l)
                if transpage in errors:
                    color = "red"
                elif WikiSystem(self.env).has_page(transpage):
                    regres = self.macro_re.search(WikiPage(self.env, transpage).text)
                    if regres != None:
                         argstr = regres.group(1)
                         if argstr != None and len(argstr) > 0:
                             args, kw = parse_args(argstr)
                             if 'outdated' in kw:
                                 color = "yellow"
                             elif l != self.base_lang:
                                 try:
                                     rev = int(kw['revision'])
                                     if rev != 0 and rev > basever:
                                         color = "red"
                                     elif rev != basever:
                                         color = "yellow"
                                 except:
                                     color = "red"
                    else:
                        color = "red"
                else:
                    color = "grey"
                if lang != None:
                    res += "||$$$%s$$$[[wiki:/%s|%s]]" % (color, transpage, base_page)
                elif skipmissing and color == "grey":
                    res += "|| "
                else:
                    res += "||$$$%s$$$[[wiki:/%s|%s]]" % (color, transpage, l)
            res +="||\n"

        return res

    def expand_macro(self, formatter, name, args):
        """
        Return a list of translated pages with the native language names.
        The list of languages supported can be configured by adding new
        entries to TracLanguages page. Refer to ISO 639-1 for more information.
        """

        if formatter.resource.realm != 'wiki':
            return system_message(_("%(name)s macro can only be used in "
                                    "wiki pages.", name=name))

        args, kw = parse_args(args)
        preview = 'preview' in formatter.req.args

        # first handle special cases
        show = "";
        lang = None
        silent = 'silent' in args
        skipmissing = 'skipmissing' in args
        outdated = ""
        if 'lang' in kw:
            lang = kw['lang']
        if 'outdated' in kw:
            outdated = kw['outdated']
        if 'showproblems' in args:
            show += self._get_problems(silent)
        if 'showstatus' in args:
            show += self._get_status(lang, skipmissing)
        if 'showoutdated' in args:
            label = None
            if 'label_outdated' in kw:
              label = kw['label_outdated']
            show += self._get_outdated(lang, label)
        if 'showmissing' in args:
            show += self._get_missing(lang)
        if 'showuntranslated' in args:
            show += self._get_untranslated(silent)
        if len(show):
            outshow = StringIO()
            Formatter(self.env, formatter.context).format(show, outshow)
            val = outshow.getvalue()
            val = re.sub('>\$\$\$([a-z]+?)\$\$\$<a class=".*?"', \
                ' style="background-color:\\1"><a style="color:#151B8D"', val)
            # try again more secure in case previous fails due to Wiki engine changes
            val = re.sub('>\$\$\$([a-z]+?)\$\$\$', \
                ' style="background-color:\\1">', val)
            return val

        page_name = formatter.context.resource.id
        prefix, base_page_name, lang_code = self._get_page_info(page_name)

        lang_link_list = []
        for translation in self._get_translations(prefix, base_page_name):
            if translation != lang_code:
                page_name = self._get_translated_page(prefix, base_page_name, translation)
                lang_link_list.append("  * [[wiki:/%s|%s]]" % (page_name, \
                    self._get_language_name(translation)))
            else:
                lang_link_list.append("  * '''%s'''" % self._get_language_name(translation))

        baselink=""
        if lang_code != self.base_lang and 'revision' in kw:
            basepage = self._get_translated_page(prefix, base_page_name, self.base_lang)
            newver = WikiPage(self.env, basepage).version
            oldver = abs(int(kw['revision']))
            if oldver < newver:
                t = "[[wiki:/%s?action=diff&old_version=%s|@%s - @%s]]" \
                    % (basepage, oldver, oldver, newver)
                baselink = "\n  * " + t
                if preview:
                    out = StringIO()
                    t = "Translation not up to date: %s" % t
                    OneLinerFormatter(self.env, formatter.context).format(t, out)
                    t = out.getvalue()
                    if outdated:
                        outdated += "<br>" + t
                    else:
                        outdated = t

        if outdated:
            outdated = self.outdated_tx % outdated
        if len(lang_link_list) <= 1:
            return outdated;
        out = StringIO()
        Formatter(self.env, formatter.context).format('\n'.join(lang_link_list) \
            +baselink, out)

        desc = "Languages"
        if lang_code in self.description:
            desc = self.description[lang_code]
        return outdated + """
<div class="wiki-toc trac-nav" style="clear:both">
<h4>%s:</h4>
%s
</div>""" % (desc, out.getvalue())
