# -*- coding: utf-8 -*-
#
#            Copyright (C) 2009 Massive Trac Provider Project
#
#                         All rights reserved.
#
################################################################################
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. The name of the author may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
################################################################################
# 
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at: https://svn.mayastudios.de/mtpp/log/
#
# Author: Sebastian Krysmanski
#
################################################################################
#
# $Revision: 262 $
# $Date: 2009-07-24 17:17:49 +0200 (Fr, 24 Jul 2009) $
# $URL: https://svn.mayastudios.de/mtpp/repos/plugins/subscriberlist/trunk/subscriberlist/web_ui.py $
#
################################################################################

from trac.core import *

from trac.wiki.api import IWikiMacroProvider
from trac.mimeview.api import Mimeview
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.util.html import Markup

from genshi.builder import tag
from genshi.filters.transform import Transformer

# Imports from same package
from mapping import LEXERS

class CodeProcessor(Component):
  implements(IWikiMacroProvider, ITemplateProvider)

  DEFAULT_MIMETYPE = 'text/plain'
  
  LANG_NAME_TEMPLATE = '<div class="lang-name-template"><span>%s</span></div>'
  
  # IWikiMacroProvider methods
  
  def get_macros(self):
    """Return an iterable that provides the names of the provided macros.
       Yield the name of the macro based on the class name."""
    yield 'code'

  def get_macro_description(self, name):
    """Return a plain text description of the macro with the specified name.
    """
    doc = "Provides a [wiki:WikiProcessors wiki processor] for code listing that uses file " \
          "extensions for language detection rather than mimetypes. " \
          ' To use this processor type for example `#!code(lang=python)`.' \
          ' These extensions are available: \n'
    
    langs = []
    for _, name, alt_names, file_exts, _ in LEXERS.itervalues():
      lang_desc = " * [[html(<b>" + name + "</b>)]] - "
      
      extensions = []
      extensions_map = {}
      for ext in file_exts:
        idx = ext.rfind('.')
        if idx == -1:
          continue
        
        name = ext[idx+1:].lower()
        if not extensions_map.has_key(name):
          extensions.append(name)
          extensions_map[name] = 1
        
      for name in alt_names:
        name = name.lower()
        if not extensions_map.has_key(name):
          extensions.append(name)
          extensions_map[name] = 1
      
      extensions.sort()
      lang_desc += '`' + '`, `'.join(extensions) + '`'
      langs.append(lang_desc)
      
    langs.sort(cmp=lambda x,y: cmp(x.lower(), y.lower()))
      
    return doc + '\n'.join(langs)
  
  def expand_macro(self, formatter, name, content):
    add_stylesheet(formatter.req, 'codeprocessor/style.css')

    if not content: # no content
      return Markup()
      
    mimeview = Mimeview(self.env)
      
    if formatter.code_processor and formatter.code_processor.args and \
      formatter.code_processor.args.has_key('lang'):
      lang = formatter.code_processor.args['lang']
    
      mimetype = mimeview.get_mimetype('file.' + lang)
      if not mimetype:
        infos = self._get_lang_info(lang)
        if infos:
          mimetype = infos[1]
          lang_name = infos[0]
        else:
          mimetype = self.DEFAULT_MIMETYPE
          lang_name = 'unknown language (*.%s)' % lang
      else:
        # Strip away additional "parameters" such as "; charset=..."
        mimetype = mimetype.split(';')[0]
        lang_name = self._get_lang_name_for_mimetype(mimetype)
        if not lang_name:
          lang_name = 'unknown language name (%s)' % lang
    else:
      mimetype = self.DEFAULT_MIMETYPE
      lang_name = 'Text'
    
    # The argument "force_source = True" prevents the mime viewer from 
    # displaying patches in tabular representation and rather display it as
    # highlighted code.
    return mimeview.render(formatter.context, mimetype, content, force_source=True) \
           | Transformer('.').append(tag(Markup(self.LANG_NAME_TEMPLATE % lang_name)))

  # ITemplateProvider methods
  
  def get_templates_dirs(self):
    return []
      
  def get_htdocs_dirs(self):
    from pkg_resources import resource_filename
    return [('codeprocessor', resource_filename(__name__, 'htdocs'))]

  # other methods
  
  def _get_lang_name_for_mimetype(self, mimetype):
    """
    Get a languages names for a mimetype.
    """
    for _, name, _, _, mimetypes in LEXERS.itervalues():
      if mimetype in mimetypes:
        return name
    
    return None
        
  def _get_lang_info(self, file_ext):
    """
    Get a languages names for a mimetype.
    """
    file_ext = file_ext.lower()
    file_ext2 = '.' + file_ext
    for _, name, alt_names, file_exts, mimetypes in LEXERS.itervalues():
      for ext in file_exts:
        if ext.lower().endswith(file_ext2):
          return (name, mimetypes[0])
      
      for ext in alt_names:
        if ext.lower() == file_ext:
          return (name, mimetypes[0])
    
    return None
