# -*- coding: utf-8 -*-
"""
    Movie plugin for Trac.

    Embeds various online movies.
"""
import mimetypes
from posixpath import join as pathjoin
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from pkg_resources import resource_filename
from trac.core import TracError
from trac.core import implements
from trac.resource import Resource, get_resource_url
from trac.util import hex_entropy
from trac.util.html import html as tag
from trac.util.presentation import to_json
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase

from movie.model import MovieMacroConfig
from movie.utils import parse_imagemacro_style
from movie.utils import set_default_parameters
from movie.utils import string_keys
from movie.utils import xform_query
from movie.utils import xform_style
from movie.video_sites import get_embed_video_site_player


EMBED_PATH_FLOWPLAYER = {
    'js': 'movie/js/flowplayer.min.js',
    'css': 'movie/js/skin/minimalist.css',
    'swf': 'movie/swf/flowplayer.swf',
}

_EMBED_FLOWPLAYER_DEFAULT_PARAMETERS = {
    'adaptiveRatio': True,
    'bufferTime': '0.1',
    'debug': False,
    'disabled': False,
    'engine': 'html5',
    'flashfit': False,
    'fullscreen': True,
    'errors': 'array',
    'keyboard': True,
    'live': False,
    'muted': False,
    'native_fullscreen': False,
    'preload': None,
    'ratio': None,  # use adaptiveRatio by default
    'rtmp': None,
    'speeds': [0.25, 0.5, 1, 1.5, 2],
    'swf': None,  # set swf path on server-side
    'splash': False,
    'subscribe': False,
    'tooltip': True,
    'volume': '1',
}


class MovieMacro(WikiMacroBase):
    """ Embed online movies from 
        YouTube, 
        Vimeo, 
        Dailymotion, 
        Brighteon, 
        Frankspeech, 
        Rumble 
        and 
        Bitchute, 
        and local movies via FlowPlayer.

        The movie link or URL is the first and only required parameter.
        Simply use the browser URL for most online movie links. 
        For Frankspeech use the link found inside the HTML provided by the '''Embed''' button.
        For Rumble use the the ''Embed IFRAME URL'' provided by the '''EMBED''' button.

        Use the following link forms for local files:
         * from an attachment on a ticket or wiki page (''simplest''): `sample.webm`
         * from an attachment on a ticket (''simple''): `ticket:123:sample.mp4`
         * from an attachment on a wiki page (''simple''): `wiki:test/sub/sample.mp4`
         * from the project's htdocs: `htdocs://site/filename.flv`
         * from a plugin's htdocs: `htdocs://plugin/dir/filename.flv`
         * from an attachment on ticket `#123`: `ticket://123/filename.flv`
         * from an attachment on a wiki page: `wiki://WikiWord/filename.flv`
         * from the SVN repository revision `[1024]` (`HEAD` can also as the revision): `source://1024/trunk/docs/filename.flv`

        An optional, named parameter is `style`, e.g. `style=width:320px; height:240px;`.

        '''Note:''' For local files, Flowplayer tries to resolve to an appropriate size, 
        ignoring width/height settings. This is because Flowplayer settings have `adaptiveRatio=true` 
        by default in MovieMacro. It is preferred to allow the player to adjust the size automatically, 
        rather than select a particular size, in almost every case. If that behavior is not desired, 
        pass `adaptiveRatio=false` as a query string and use the `style` parameter.
    """
    implements(IRequestFilter, ITemplateProvider)

    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content, strict=True)
        if len(args) == 0:
            raise TracError('URL to a movie at least required.')

        url = self._get_absolute_url(formatter.req, args[0])
        scheme, netloc, path, params, query, fragment = urlparse(url)

        try:
            style_dict = xform_style(string_keys(kwargs).get('style', ''))
        except Exception as e:
            raise TracError('Double check the `style` argument: ' + str(e))

        self.log.debug('moviemacro style_dict: %s', style_dict)
        config = MovieMacroConfig(self.env, self.config)
        style = {
            'width': style_dict.get('width', config.width),
            'height': style_dict.get('height', config.height),
            'border': style_dict.get('border', 'none'),
            'margin': style_dict.get('margin', '0 auto'),
            'display': 'block',
            'clear': 'both'
        }
        self.log.debug('moviemacro style: %s', style)

        site_player = get_embed_video_site_player(netloc)
        if site_player is not None:
            return site_player(scheme, netloc, path, query, style)

        parse_result = urlparse(args[0])
        query = parse_result.query
        if config.splash:
            splash_url = pathjoin(formatter.href.chrome(), config.splash)
            splash_style = 'background-color:#777; '\
                           'background-image:url(%s);' % splash_url
            style['style'] = splash_style
            query += '&splash=true'
        return self.embed_player(formatter, url, query, style)

    def embed_player(self, formatter, url, query, style):
        query_dict = xform_query(query)
        set_default_parameters(
            query_dict,
            _EMBED_FLOWPLAYER_DEFAULT_PARAMETERS
        )

        player_id = self._generate_player_id()
        swf = pathjoin(formatter.href.chrome(), EMBED_PATH_FLOWPLAYER['swf'])
        style.pop('width')  # use adaptiveRatio for player-size
        style.pop('height')  # use adaptiveRatio for player-size
        attrs = {
            'id': player_id,
            'data-swf': swf,
            'style': xform_style(style),
        }
        return tag.div(
            tag.video([
                tag.source(type=mimetypes.guess_type(url)[0], src=url),
                tag.script("""
                    $(function() {
                        $('#%s').flowplayer(%s);
                    });
                """ % (player_id, to_json(query_dict))
                ),
            ]),
            **attrs
        )

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        path = req.path_info
        if path.startswith('/ticket/') or path.startswith('/wiki') \
           or path.startswith('/attachment/'):
            add_script(req, EMBED_PATH_FLOWPLAYER['js'])
            add_stylesheet(req, EMBED_PATH_FLOWPLAYER['css'])
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        yield ('movie', resource_filename('movie', 'htdocs'))

    def get_templates_dirs(self):
        return []

    # Private methods

    def _generate_player_id(self):
        return 'player-' + hex_entropy()

    def _get_absolute_url(self, req, url):
        """ Generate an absolute url from the url with the special schemes
        {htdocs,chrome,ticket,wiki,source} simply return the url if given with
        {http,https,ftp} schemes.

        Also support restricted ImageMacro format style.
        It can be specified only filename on ticket or wiki page.

        Examples:
            http://example.com/filename.ext
                ie. http://www.google.com/logo.jpg

            chrome://site/filename.ext
            htdocs://img/filename.ext
            htdocs:/img/filename.ext
                note: `chrome` is an alias for `htdocs`

            ticket://123/specification.pdf
            ticket:123:specification.pdf

            wiki://WikiWord/attachment.jpg
            wiki:WikiWord/attachment.jpg

            source://1024/path/filename.ext
        """
        if '://' in url:
            scheme, netloc, path, query, params, fragment = urlparse(url)
        else:  # suppose ImageMacro style
            scheme, netloc, path = parse_imagemacro_style(url, req.path_info)

        if scheme in ('htdocs', 'chrome'):
            return req.abs_href.chrome(netloc + path)

        if scheme in ('source',):
            return req.abs_href.export(netloc + path)

        if scheme in ('wiki', 'ticket'):
            resource = Resource(scheme, netloc).child('attachment', path)
            kwargs = {'format': 'raw'}
            return get_resource_url(self.env, resource, req.abs_href, **kwargs)

        return url
