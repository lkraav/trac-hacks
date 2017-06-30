# -*- coding: utf-8 -*-
import pytest
import re

from trac.test import Mock, MockPerm
from trac.util.datefmt import utc
from trac.web.href import Href
from trac.wiki.formatter import format_to_html
try:
    from trac.web.chrome import web_context
except ImportError:
    from trac.mimeview.api import Context

    def web_context(req):
        return Context.from_request(req)


BASE_HREF = 'http://example.com/mysite'


def Request(**kwargs):
    kwargs.setdefault('locale', None)
    kwargs.setdefault('lc_time', None)
    kwargs.setdefault('tz', utc)
    kwargs.setdefault('args', {})
    kwargs.setdefault('arg_list', ())
    kwargs.setdefault('path_info', '/')
    kwargs.setdefault('href', Href('/'))
    kwargs.setdefault('abs_href', 'http://localhost/')
    kwargs.setdefault('perm', MockPerm())
    return Mock(**kwargs)


@pytest.mark.parametrize(('url', 'expected'), [
    ('http://example.com/file.ext', 'http://example.com/file.ext'),
    ('htdocs://site/test.flv', '%s/chrome/site/test.flv' % BASE_HREF),
    ('chrome://site/test.flv', '%s/chrome/site/test.flv' % BASE_HREF),
    ('ticket://123/sample.webm',
     '%s/raw-attachment/ticket/123/sample.webm' % BASE_HREF),
    ('wiki://page/sample.mp4',
     '%s/raw-attachment/wiki/page/sample.mp4' % BASE_HREF),
    ('source://repo/movie.ogv', '%s/export/repo/movie.ogv' % BASE_HREF),
])
def test_get_absolute_url(movie_macro, url, expected):
    req = Request(abs_href=Href(BASE_HREF))
    assert expected == movie_macro._get_absolute_url(req, url)


@pytest.mark.parametrize(('url', 'path_info', 'expected'), [
    ('sample.webm', u'/ticket/123',
     '%s/raw-attachment/ticket/123/sample.webm' % BASE_HREF),
    ('ticket:123:sample.webm', u'/ticket/123',
     '%s/raw-attachment/ticket/123/sample.webm' % BASE_HREF),
    ('ticket:456:sample.webm', u'/ticket/123',
     '%s/raw-attachment/ticket/456/sample.webm' % BASE_HREF),
    ('wiki:sample.mp4', u'/wiki/page',
     '%s/raw-attachment/wiki/page/sample.mp4' % BASE_HREF),
    ('wiki:page/sample.mp4', u'/wiki/page',
     '%s/raw-attachment/wiki/page/sample.mp4' % BASE_HREF),
    ('wiki:test/movie/sub/sample.mp4', u'/wiki/test/movie/sub',
     '%s/raw-attachment/wiki/test/movie/sub/sample.mp4' % BASE_HREF),
])
def test_get_absolute_url_simple(movie_macro, url, path_info, expected):
    req = Request(abs_href=Href(BASE_HREF), path_info=path_info)
    assert expected == movie_macro._get_absolute_url(req, url)


def test_unique_player_id(env):
    req = Request()
    context = web_context(req)
    n = 10
    result = format_to_html(env, context,
                            '[[Movie(http://localhost/movie.mp4)]]\n' * n)
    ids = [m.group(1) for m in re.finditer(r' id="(player-[^"]*)"', result)]
    assert sorted(ids) == sorted(set(ids))
    assert ids == ids[:n]
