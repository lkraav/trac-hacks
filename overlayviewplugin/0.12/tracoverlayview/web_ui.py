# -*- coding: utf-8 -*-

import pkg_resources
import re
import sys

from trac.core import Component, implements, TracError
from trac.attachment import AttachmentModule
from trac.mimeview.api import Mimeview
from trac.perm import PermissionError
from trac.resource import ResourceNotFound
from trac.util.text import exception_to_unicode
from trac.web.api import (
    IRequestHandler, IRequestFilter, Request, RequestDone, HTTPForbidden,
    HTTPNotFound,
)
from trac.web.chrome import (
    Chrome, ITemplateProvider, add_script, add_stylesheet, add_script_data,
)

try:
    from trac.web.api import HTTPInternalServerError
except ImportError:
    from trac.web.api import HTTPInternalError as HTTPInternalServerError

try:
    from trac.util import lazy
except ImportError:
    lazy = None


__all__ = ()


_use_jinja2 = hasattr(Chrome, 'jenv')


if sys.version_info[0] != 2:
    _iteritems = lambda d: d.items()
else:
    _iteritems = lambda d: d.iteritems()


if hasattr(Request, 'is_xhr'):
    def _is_xhr(req):
        return req.is_xhr
else:
    def _is_xhr(req):
        return req.get_header('X-Requested-With') == 'XMLHttpRequest'


def _send_no_content(req):
    req.send(b'', status=204)


class OverlayViewModule(Component):

    implements(IRequestHandler, IRequestFilter, ITemplateProvider)

    # ITemplateProvider methods

    _htdocs_dirs = (
        ('overlayview', pkg_resources.resource_filename(__name__, 'htdocs')),
    )

    _templates_dirs = (
        pkg_resources.resource_filename(
            __name__,
            'templates/jinja2' if _use_jinja2 else 'templates/genshi',
        ),
    )

    def get_htdocs_dirs(self):
        return self._htdocs_dirs

    def get_templates_dirs(self):
        return self._templates_dirs

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ('timeline.html', 'wiki_view.html', 'ticket.html',
                        'milestone_view.html', 'attachment.html'):
            add_stylesheet(req, 'common/css/code.css')
            add_stylesheet(req, 'overlayview/base.css')
            add_script(req, 'common/js/folding.js')
            add_script(req, 'overlayview/jquery.colorbox.js')
            add_script(req, 'overlayview/base.js')
            script_data = self._get_script_data(req)
            add_script_data(req, {'overlayview': script_data})
        return template, data, content_type

    # IRequestHandler methods

    _match_request_re = re.compile(r'/overlayview/([^/]+)/([^/]+)(?:/(.*))?\Z')

    def match_request(self, req):
        match = self._match_request_re.match(req.path_info)
        if match:
            cmd, realm, path = match.groups()
            req.args['cmd'] = cmd
            req.args['realm'] = realm
            if path:
                req.args['path'] = path
            return True

    def process_request(self, req):
        if not _is_xhr(req):
            _send_no_content()

        cmd = req.args.get('cmd')
        try:
            if cmd == 'attachment':
                req.environ['PATH_INFO'] = req.path_info[len('/overlayview'):] \
                                           .encode('utf-8')
                rv = AttachmentModule(self.env).process_request(req)
                return ('overlayview_attachment.html',) + rv[1:]
        except RequestDone:
            raise
        except (PermissionError, HTTPForbidden):
            self._send_exception(req, 403)
        except (ResourceNotFound, HTTPNotFound):
            self._send_exception(req, 404)
        except (TracError, HTTPInternalServerError):
            self._send_exception(req, 500)

        _send_no_content()

    # Internal methods

    def _get_script_data(self, req):
        rv = {'baseurl': req.href().rstrip('/') + '/'}
        rv.update(self._mimetypes)
        return rv

    if lazy:
        @lazy
        def _mimetypes(self):
            return self._get_mimetypes()
    else:
        @property
        def _mimetypes(self):
            value = self._mimetypes = self._get_mimetypes()
            return value

    def _get_mimetypes(self):
        import mimetypes
        mimetypes.init()
        images = set()
        videos = set()
        for map_ in (Mimeview(self.env).mime_map, mimetypes.types_map):
            for ext, mimetype in _iteritems(map_):
                if not ext or '/' in ext or not mimetype:
                    continue
                ext = ext.lstrip('.')
                if mimetype.startswith('image/'):
                    images.add(ext)
                if mimetype.startswith('video/'):
                    videos.add(ext)
        return {'images': sorted(images), 'videos': sorted(videos)}

    def _send_exception(self, req, status):
        exc_info = sys.exc_info()
        message = exception_to_unicode(exc_info[1])
        self.log.warning('%s: %s', __name__, message)
        req.send(message.encode('utf-8'), status=status)
