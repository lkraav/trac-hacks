# vim: expandtab
import re, time
from StringIO import StringIO

from genshi.builder import tag

from trac.core import *
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util import as_bool, TracError
from trac.util.text import to_unicode
from trac.web.chrome import add_stylesheet, add_script, Chrome, ITemplateProvider
from trac.wiki.api import parse_args, IWikiMacroProvider
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule
from pkg_resources import resource_filename
import random
import string

import fdx2fountain

class ScrippetMacro(WikiMacroBase):
    """A macro to add scrippets to a page. Usage:
    """
    implements(IWikiMacroProvider, ITemplateProvider)

    def render_fdx_subset(self,fdx,start_with_scene,end_with_scene,formatter):
        fdx_obj = self._get_src(self.env, formatter.req, *fdx)
        fountain_content = fdx2fountain.Fdx2Fountain().fountain_from_fdx(fdx_obj.getStream().read(),start_with_scene,end_with_scene)
        data = {
          'fountain': to_unicode(fountain_content),
          'inline': True,
          'fnid': "fn" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        }
        return Chrome(self.env).render_template(formatter.req,
                                                'fountain.html', data=data, fragment=True)
        
    def expand_macro(self, formatter, name, content, args):
        req = formatter.req
        add_stylesheet(req, 'scrippets/css/fountain-js.css')
        add_stylesheet(req, 'scrippets/css/normalize.min.css')
        add_script(req, 'scrippets/js/fountain.min.js')
        add_script(req, 'scrippets/js/fountain-reader.js')
        if content:
            args2,kw = parse_args(content)
            self.log.debug("RENDER ARGUMENTS: %s " % args2)
            self.log.debug("RENDER KW: %s " % kw)
            self.log.debug("RENDER ARGS: %s " % args)
            pure = False
            if args != None:
                if 'pure' in args:   
                    pure = as_bool(args['pure'])
            if kw != None:
                if 'fdx' in kw:
                    fdx = self._parse_filespec(kw['fdx'].strip(), formatter.context, self.env)
                    self.log.debug("FDX: {0}".format(fdx))
                if 'start_with_scene' in kw:
                    start_with_scene = int(kw['start_with_scene'])
                    self.log.debug("START: %s" % start_with_scene)
                if 'end_with_scene' in kw:
                    end_with_scene = int(kw['end_with_scene'])
                    self.log.debug("END: %s" % end_with_scene)
                elif 'start_with_scene' in kw:
                    end_with_scene = int(kw['start_with_scene']) + 1
                    self.log.debug("END: %s" % end_with_scene)
                
            if kw != {} and fdx:
                self.log.debug("RENDER SUBSET")
                return self.render_fdx_subset(fdx,start_with_scene,end_with_scene,formatter)
            else:
                self.log.debug("PURE: %s" % pure)
                if not pure:
                    content = re.sub(r"//(.*?)//","*\g<1>*", content)
                    content = re.sub(r"'''(.*?)'''","**\g<1>**", content)
                    content = re.sub(r"''(.*?)''","*\g<1>*", content)
                    content = re.sub(r"__(.*?)__","_\g<1>_", content)
                data = {
                  'fountain': to_unicode(content),
                  'inline': True,
                  'fnid': "fn" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
                }
                return Chrome(self.env).render_template(req,
                      'fountain.html', data=data, fragment=True)
    
    ## ITemplateProvider
    def get_htdocs_dirs(self):
        return [resource_filename('scrippets', 'htdocs')]
                                      
    def get_templates_dirs(self):
        return [resource_filename('scrippets', 'templates')]

    def _parse_filespec(self, filespec, context, env):
        # parse filespec argument to get module and id if contained.
        if filespec[:5] == 'http:' or filespec[:6] == 'https:':
            parts = [ 'url', '', filespec ]
        else:
            parts = filespec.split(':', 2)

        if len(parts) == 3:                 # module:id:attachment
            if parts[0] in ['wiki', 'ticket', 'browser', 'file', 'url']:
                module, id, file = parts
            else:
                raise Exception("unknown module %s" % parts[0])

        elif len(parts) == 2:
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [link for link,_ in
                                 BrowserModule(env).get_link_resolvers()]
            except Exception:
                browser_links = []

            id, file = parts
            if id in browser_links:         # source:path
                module = 'browser'
            elif id and id[0] == '#':       # #ticket:attachment
                module = 'ticket'
                id = id[1:]
            elif id == 'htdocs':            # htdocs:path
                module = 'file'
            else:                           # WikiPage:attachment
                module = 'wiki'

        elif len(parts) == 1:               # attachment
            # determine current object
            module = context.resource.realm or 'wiki'
            id     = context.resource.id
            file   = filespec
            if module not in ['wiki', 'ticket']:
                raise Exception('Cannot reference local attachment from here')
            if not id:
                raise Exception('unknown context id')

        else:
            raise Exception('No filespec given')

        return module, id, file

    def _get_src(env, req, module, id, file):
        # check permissions first
        if module == 'wiki'    and 'WIKI_VIEW' not in req.perm   or \
           module == 'ticket'  and 'TICKET_VIEW' not in req.perm or \
           module == 'file'    and 'FILE_VIEW' not in req.perm   or \
           module == 'browser' and 'BROWSER_VIEW' not in req.perm:
            raise Exception('Permission denied: %s' % module)

        if module == 'browser':
            return BrowserSource(env, req, file)
        if module == 'file':
            return FileSource(env, id, file)
        if module == 'wiki' or module == 'ticket':
            return AttachmentSource(env, module, id, file)
        if module == 'url':
            return UrlSource(file)

        raise Exception("unsupported module '%s'" % module)

    _get_src = staticmethod(_get_src)
    
class TransformSource(object):
    """Represents the source of an input (stylesheet or xml-doc) to the transformer"""

    def __init__(self, module, id, file, obj):
        self.module = module
        self.id     = id
        self.file   = file
        self.obj    = obj

    def isFile(self):
        return False

    def getFile(self):
        return None

    def getUrl(self):
        return "%s://%s/%s" % (self.module, str(self.id).replace("/", "%2F"), self.file)

    def get_last_modified(self):
        return to_datetime(None)

    def __str__(self):
        return str(self.obj)

    def __del__(self):
        if self.obj and hasattr(self.obj, 'close') and callable(self.obj.close):
            self.obj.close()

    class CloseableStream(object):
        """Implement close even if underlying stream doesn't"""

        def __init__(self, stream):
            self.stream = stream

        def read(self, len=None):
            return self.stream.read(len)

        def close(self):
            if hasattr(self.stream, 'close') and callable(self.stream.close):
                self.stream.close()    

class BrowserSource(TransformSource):
    def __init__(self, env, req, file):
        from trac.versioncontrol import RepositoryManager
        from trac.versioncontrol.web_ui import get_existing_node

        if hasattr(RepositoryManager, 'get_repository_by_path'): # Trac 0.12
            repo, file = RepositoryManager(env).get_repository_by_path(file)[1:3]
        else:
            repo = RepositoryManager(env).get_repository(req.authname)
        obj = get_existing_node(req, repo, file, None)

        TransformSource.__init__(self, "browser", "source", file, obj)

    def getStream(self):
        return self.CloseableStream(self.obj.get_content())

    def __str__(self):
        return self.obj.path

    def get_last_modified(self):
        return self.obj.get_last_modified()

class FileSource(TransformSource):
    def __init__(self, env, id, file):
        file = re.sub('[^a-zA-Z0-9._/-]', '', file)     # remove forbidden chars
        file = re.sub('^/+', '', file)                  # make sure it's relative
        file = os.path.normpath(file)                   # resolve ..'s
        if file.startswith('..'):                       # don't allow above doc-root
            raise Exception("illegal path '%s'" % file)

        if id != 'htdocs':
            raise Exception("unsupported file id '%s'" % id)

        obj = os.path.join(env.get_htdocs_dir(), file)

        TransformSource.__init__(self, "file", id, file, obj)

    def isFile(self):
        return True

    def getFile(self):
        return self.obj

    def getStream(self):
        import urllib
        return urllib.urlopen(self.obj)

    def get_last_modified(self):
        return to_datetime(os.stat(self.obj).st_mtime)

    def __str__(self):
        return self.obj

class AttachmentSource(TransformSource):
    def __init__(self, env, module, id, file):
        from trac.attachment import Attachment
        obj = Attachment(env, module, id, file)

        TransformSource.__init__(self, module, id, file, obj)

    def getStream(self):
        return self.obj.open()

    def get_last_modified(self):
        return to_datetime(os.stat(self.obj.path).st_mtime)

    def __str__(self):
        return self.obj.path

class UrlSource(TransformSource):
    def __init__(self, url):
        import urllib
        try:
            obj = urllib.urlopen(url)
        except Exception, e:
            raise Exception('Could not read from url "%s": %s' % (file, e))

        TransformSource.__init__(self, "url", None, url, obj)

    def getStream(self):
        return self.obj

    def getUrl(self):
        return self.file

    def get_last_modified(self):
        lm = self.obj.info().getdate('Last-modified')
        if lm:
            from datetime import datetime
            from trac.util.datefmt import FixedOffset
            return datetime(lm[0], lm[1], lm[2], lm[3], lm[4], lm[5], 0,
                            FixedOffset(lm[9], 'custom'))
        return to_datetime(None)

    def __str__(self):
        return self.obj.url

