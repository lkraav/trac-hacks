# -*- coding: utf-8 -*-

import re
import hashlib

from trac.config import Option, ListOption, BoolOption
from trac.core import Component, TracError, implements
from trac.db import Table, Column, DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.mimeview.api import IHTMLPreviewRenderer
from trac.util import as_int, to_unicode
from trac.util.html import Markup, html as tag
from trac.web.api import IRequestFilter, IRequestHandler, RequestDone
from trac.web.chrome import Chrome, ITemplateProvider, add_script
from trac.wiki.api import IWikiMacroProvider, parse_args

from tracextracturl import extract_url


class MindMapMacro(Component):
    implements(IEnvironmentSetupParticipant, IHTMLPreviewRenderer,
               IRequestFilter, IRequestHandler, ITemplateProvider,
               IWikiMacroProvider)

    default_width = Option(
        'mindmap', 'default_width', '100%', 'Default width for mindmaps')

    default_height = Option(
        'mindmap', 'default_height', '600', 'Default height for mindmaps')

    default_flashvars = ListOption(
        'mindmap', 'default_flashvars',
        ['openUrl = _blank', 'startCollapsedToLevel = 5'],
        'Default flashvars for mindmaps')

    resizable = Option(
        'mindmap', 'resizable', True,
        'Allow mindmaps to be resized. Needs several script and style files.')

    default_resizable = BoolOption(
        'mindmap', 'default_resizable', True,
        'Default setting if mindmaps are resizable.')

    SCHEMA = [
        Table('mindmapcache', key='hash')[
            Column('hash'),
            Column('content'),
        ]
    ]

    DB_VERSION = 0

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        ver = dbm.get_database_version('mindmap_version')
        if not ver:
            tables = dbm.get_table_names()
            if 'mindmapcache' in tables:
                self._set_db_version()
                return False
            else:
                return True
        elif ver < self.DB_VERSION:
            return True

    def upgrade_environment(self):
        self._upgrade_db()

    def _set_db_version(self):
        DatabaseManager(self.env).set_database_version(self.DB_VERSION,
                                                       'mindmap_version')

    def _upgrade_db(self):
        DatabaseManager(self.env).create_tables(self.SCHEMA)
        self._set_db_version()

    # IHTMLPreviewRenderer methods

    supported_mimetypes = {
        'text/x-freemind': 9,
        'text/freemind': 9,
        'application/x-freemind': 9,
        'application/freemind': 9,
    }

    def get_quality_ratio(self, mimetype):
        self.env.log.debug('Mimetype: ' + mimetype)
        return self.supported_mimetypes.get(mimetype, 0)

    def render(self, context, mimetype, content, filename=None, url=None):
        return self.produce_html(context, url)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'mindmap/tools.flashembed-1.0.4.min.js',
                   mimetype='text/javascript')
        add_script(req, 'mindmap/mindmap.js', mimetype='text/javascript')
        if self.resizable:
            Chrome(self.env).add_jquery_ui(req)
        return template, data, content_type

    def _set_cache(self, hash, content):
        self.env.db_transaction("""
                INSERT INTO mindmapcache VALUES (%s,%s)
                """, (hash, unicode(content)))

    def _get_cache(self, hash, default=None):
        for content, in self.env.db_query("""
                SELECT content FROM mindmapcache WHERE hash=%s
                """, (hash,)):
            return content
        else:
            return default

    def _check_cache(self, hash):
        for count, in self.env.db_query("""
                SELECT count(content) FROM mindmapcache WHERE hash=%s
                """, (hash,)):
            return count
        else:
            return 0

    # IWikiMacroProvider methods

    def get_macros(self):
        return ['MindMap', 'Mindmap']

    def get_macro_description(self, name):
        return self.__doc__

    def expand_macro(self, formatter, name, content, args=None):
        "Produces XHTML code to display mindmaps"

        if args is None:  # Short macro
            largs, kwargs = parse_args(content)
            if not largs:
                raise TracError("File name missing!")
            file = largs[0]
            url = extract_url(self.env, formatter.context, file, raw=True)
        else:  # Long macro
            kwargs = args
            digest = hashlib.md5()
            digest.update(unicode(content).encode('utf-8'))
            hash = digest.hexdigest()
            if not self._check_cache(hash):
                mm = MindMap(content)
                self._set_cache(hash, mm)
            url = formatter.context.href.mindmap(hash + '.mm')
        return self.produce_html(formatter.context, url, kwargs)

    def produce_html(self, context, url, kwargs={}):
        attr = {
            'data': context.href.chrome('mindmap', 'visorFreemind.swf')
        }
        width = kwargs.pop('width', self.default_width)
        height = kwargs.pop('height', self.default_height)
        if as_int(width, None) is not None:
            attr['width'] = '%spx' % width
        else:
            attr['width'] = width
        if as_int(height, None) is not None:
            attr['height'] = '%spx' % height
        else:
            attr['height'] = height

        split = [kv.split('=') for kv in self.default_flashvars]
        flashvars = dict((k.strip(), v.strip()) for k, v in split)
        try:
            split = [kv.split('=')
                     for kv
                     in kwargs.get('flashvars', '').strip('"\'').split('|')]
            flashvars.update((k.strip(), v.strip()) for k, v in split)
        except ValueError:
            pass
        flashvars['initLoadFile'] = url

        css = ''
        if 'border' in kwargs:
            border = kwargs['border'].strip('"\'').replace(';', '')
            if border == '1':
                border = 'solid'
            elif border == '0':
                border = 'none'
            css = 'border: ' + border

        if self.resizable and \
                (('resizable' not in kwargs and self.default_resizable) or
                 kwargs.get('resizable', 'false').lower() == 'true'):
            class_ = 'resizablemindmap mindmap'
        else:
            class_ = 'mindmap'

        fvstr = Markup('&'.join(['='.join((k, unicode(v)))
                       for k, v in flashvars.iteritems()]))
        return tag.div(
            tag.object(
                tag.param(name='quality', value='high'),
                tag.param(name='bgcolor', value='#ffffff'),
                tag.param(name='flashvars', value=fvstr),
                type='application/x-shockwave-flash',
                **attr
            ),
            class_=class_,
            style=Markup(css),
        )

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('mindmap', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/mindmap/')

    def process_request(self, req):
        if req.path_info == '/mindmap/status':
            try:
                content = tag.html(tag.body(tag.dd([
                    [tag.dt(tag.a(k, href=req.href.mindmap(k + '.mm'))),
                     tag.dd(tag.pre(v))]
                    for k, v in self.env.db_query("""
                        SELECT hash,content FROM mindmapcache
                        """)
                ])))
            except Exception, e:
                content = tag.html(
                    tag.body(tag.strong("DB Error: " + unicode(e))))
            html = content.generate().render("xhtml").encode('utf-8')
            req.send_response(200)
            req.send_header('Cache-control', 'must-revalidate')
            req.send_header('Content-Type', 'text/html;charset=utf-8')
            req.send_header('Content-Length', len(html))
            req.end_headers()

            if req.method != 'HEAD':
                req.write(html)
            raise RequestDone

        try:
            hash = req.path_info[9:-3]
            mm = to_unicode(self._get_cache(hash)).encode('utf-8')
            req.send_response(200)
            req.send_header('Cache-control', 'must-revalidate')
            req.send_header('Content-Type', 'application/x-freemind')
            req.send_header('Content-Length', len(mm))
            req.end_headers()
            if req.method != 'HEAD':
                req.write(mm)
        except RequestDone:
            pass
        except Exception, e:
            self.log.error(e)
            req.send_response(500)
            try:
                req.end_headers()
                req.write(str(e))
            except Exception, e:
                self.log.error(e)
        raise RequestDone


mmline = re.compile(r"^( *)([*o+-]|\d+\.)(\([^\)]*\))?\s+(.*)$")


class MindMap(object):
    "Generates Freemind Mind Map file"

    def __init__(self, tree):
        if isinstance(tree, basestring):
            tree = self.decode(tree)
        if len(tree) != 2:
            raise TracError("Tree must only have one trunk!")
        name, branch = tree
        self.xml = tag.map(self.node(name, branch), version='0.8.0')

    def __repr__(self):
        return self.xml.generate().render("xml", encoding='utf-8')

    def node(self, name, content, args={}):
        if not content:
            return tag.node(TEXT=name, **args)
        else:
            return tag.node([self.node(n, c, a) for n, c, a in content],
                            TEXT=name, **args)

    def decode(self, code):
        indent = -1
        lines = code.splitlines()
        name = ''
        while not name and lines:
            name = lines.pop(0).strip()

        rec = [name, []]
        while lines:
            self._decode(rec[1], lines, indent)
        return rec

    def _decode(self, ptr, lines, indent):
        if not lines:
            return False
        if lines[0].strip() == '':
            lines.pop(0)
            return True
        m = mmline.match(lines[0])
        if not m:
            lines.pop(0)
            return False
        ind, marker, argstr, text = m.groups()
        args = self._parse_args(argstr)
        ind = len(ind)
        text = text.strip()
        if indent == -1:
            indent = ind
        if ind == indent:
            lines.pop(0)
            ptr.append([text, [], args])
            while self._decode(ptr, lines, ind):
                pass
            return True
        elif ind > indent:
            lines.pop(0)
            ptr[-1][1].append([text, [], args])
            while self._decode(ptr[-1][1], lines, ind):
                pass
            return True
        else:
            return False

    def _parse_args(self, str):
        d = dict()
        if not str:
            return d
        for pair in str[1:-1].split(','):
            try:
                key, value = pair.split('=')
            except ValueError:
                key, value = pair, ''
            key = key.strip().upper().encode()
            d[key] = value.strip()
        return d
