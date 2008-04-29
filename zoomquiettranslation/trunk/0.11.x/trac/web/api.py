# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Edgewall Software
# Copyright (C) 2005-2006 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Christopher Lenz <cmlenz@gmx.de>

from BaseHTTPServer import BaseHTTPRequestHandler
from Cookie import CookieError, BaseCookie, SimpleCookie
import cgi
from datetime import datetime
import new
import mimetypes
import os
from StringIO import StringIO
import sys
import urlparse

from trac.core import Interface, TracError
from trac.util import get_last_traceback
from trac.util.datefmt import http_date, localtz
from trac.web.href import Href

HTTP_STATUS = dict([(code, reason.title()) for code, (reason, description)
                    in BaseHTTPRequestHandler.responses.items()])


class HTTPException(Exception):

    def __init__(self, detail, *args):
        if isinstance(detail, TracError):
            self.detail = detail.message
            self.reason = detail.title
        else:
            self.detail = detail
        if args:
            self.detail = self.detail % args
        Exception.__init__(self, '%s %s (%s)' % (self.code, self.reason,
                                                 self.detail))
    def subclass(cls, name, code):
        """Create a new Exception class representing a HTTP status code."""
        reason = HTTP_STATUS.get(code, 'Unknown')
        new_class = new.classobj(name, (HTTPException,), {
            '__doc__': 'Exception for HTTP %d %s' % (code, reason)
        })
        new_class.code = code
        new_class.reason = reason
        return new_class
    subclass = classmethod(subclass)


for code in [code for code in HTTP_STATUS if code >= 400]:
    exc_name = HTTP_STATUS[code].replace(' ', '').replace('-', '')
    # 2.5 compatibility hack:
    if exc_name == 'InternalServerError':
        exc_name = 'InternalError'
    if exc_name.lower().startswith('http'):
        exc_name = exc_name[4:]
    exc_name = 'HTTP' + exc_name        
    setattr(sys.modules[__name__], exc_name,
            HTTPException.subclass(exc_name, code))
del code, exc_name


class _RequestArgs(dict):
    """Dictionary subclass that provides convenient access to request
    parameters that may contain multiple values."""

    def getfirst(self, name, default=None):
        """Return the first value for the specified parameter, or `default` if
        the parameter was not provided.
        """
        if name not in self:
            return default
        val = self[name]
        if isinstance(val, list):
            val = val[0]
        return val

    def getlist(self, name):
        """Return a list of values for the specified parameter, even if only
        one value was provided.
        """
        if name not in self:
            return []
        val = self[name]
        if not isinstance(val, list):
            val = [val]
        return val


class RequestDone(Exception):
    """Marker exception that indicates whether request processing has completed
    and a response was sent.
    """


class Cookie(SimpleCookie):
    def load(self, rawdata, ignore_parse_errors=False):
        if ignore_parse_errors:
            self.bad_cookies = []
            self._BaseCookie__set = self._loose_set
        SimpleCookie.load(self, rawdata)
        if ignore_parse_errors:
            self._BaseCookie__set = self._strict_set
            for key in self.bad_cookies:
                del self[key]

    _strict_set = BaseCookie._BaseCookie__set

    def _loose_set(self, key, real_value, coded_value):
        try:
            self._strict_set(key, real_value, coded_value)
        except CookieError:
            self.bad_cookies.append(key)
            dict.__setitem__(self, key, None)


class Request(object):
    """Represents a HTTP request/response pair.
    
    This class provides a convenience API over WSGI.
    """

    def __init__(self, environ, start_response):
        """Create the request wrapper.
        
        @param environ: The WSGI environment dict
        @param start_response: The WSGI callback for starting the response
        @param callbacks: A dictionary of functions that are used to lazily
            evaluate attribute lookups
        """
        self.environ = environ
        self._start_response = start_response
        self._write = None
        self._status = '200 OK'
        self._response = None

        self._outheaders = []
        self._outcharset = None
        self.outcookie = Cookie()

        self.callbacks = {
            'args': Request._parse_args,
            'languages': Request._parse_languages,
            'incookie': Request._parse_cookies,
            '_inheaders': Request._parse_headers
        }

        self.base_url = self.environ.get('trac.base_url')
        if not self.base_url:
            self.base_url = self._reconstruct_url()
        self.href = Href(self.base_path)
        self.abs_href = Href(self.base_url)

    def __getattr__(self, name):
        """Performs lazy attribute lookup by delegating to the functions in the
        callbacks dictionary."""
        if name in self.callbacks:
            value = self.callbacks[name](self)
            setattr(self, name, value)
            return value
        raise AttributeError(name)

    def __repr__(self):
        return '<%s "%s %r">' % (self.__class__.__name__, self.method,
                                 self.path_info)

    # Public API

    method = property(fget=lambda self: self.environ['REQUEST_METHOD'],
                      doc='The HTTP method of the request')
    path_info = property(fget=lambda self: self.environ.get('PATH_INFO', '').decode('utf-8'),
                         doc='Path inside the application')
    remote_addr = property(fget=lambda self: self.environ.get('REMOTE_ADDR'),
                           doc='IP address of the remote user')
    remote_user = property(fget=lambda self: self.environ.get('REMOTE_USER'),
                           doc='Name of the remote user, `None` if the user'
                               'has not logged in using HTTP authentication')
    scheme = property(fget=lambda self: self.environ['wsgi.url_scheme'],
                      doc='The scheme of the request URL')
    base_path = property(fget=lambda self: self.environ.get('SCRIPT_NAME', ''),
                         doc='The root path of the application')
    server_name = property(fget=lambda self: self.environ['SERVER_NAME'],
                           doc='Name of the server')
    server_port = property(fget=lambda self: int(self.environ['SERVER_PORT']),
                           doc='Port number the server is bound to')

    def get_header(self, name):
        """Return the value of the specified HTTP header, or `None` if there's
        no such header in the request.
        """
        name = name.lower()
        for key, value in self._inheaders:
            if key == name:
                return value
        return None

    def send_response(self, code=200):
        """Set the status code of the response."""
        self._status = '%s %s' % (code, HTTP_STATUS.get(code, 'Unknown'))

    def send_header(self, name, value):
        """Send the response header with the specified name and value.

        `value` must either be an `unicode` string or can be converted to one
        (e.g. numbers, ...)
        """
        if name.lower() == 'content-type':
            ctpos = value.find('charset=')
            if ctpos >= 0:
                self._outcharset = value[ctpos + 8:].strip()
        self._outheaders.append((name, unicode(value).encode('utf-8')))

    def end_headers(self):
        """Must be called after all headers have been sent and before the actual
        content is written.
        """
        self._send_cookie_headers()
        self._write = self._start_response(self._status, self._outheaders)

    def check_modified(self, datetime, extra=''):
        """Check the request "If-None-Match" header against an entity tag.

        The entity tag is generated from the specified last modified time
        (`datetime`), optionally appending an `extra` string to
        indicate variants of the requested resource.

        That `extra` parameter can also be a list, in which case the MD5 sum
        of the list content will be used.

        If the generated tag matches the "If-None-Match" header of the request,
        this method sends a "304 Not Modified" response to the client.
        Otherwise, it adds the entity tag as an "ETag" header to the response
        so that consecutive requests can be cached.
        """
        if isinstance(extra, list):
            import md5
            m = md5.new()
            for elt in extra:
                m.update(repr(elt))
            extra = m.hexdigest()
        etag = 'W/"%s/%s/%s"' % (self.authname, http_date(datetime), extra)
        inm = self.get_header('If-None-Match')
        if (not inm or inm != etag):
            self.send_header('ETag', etag)
        else:
            self.send_response(304)
            self.end_headers()
            raise RequestDone

    def redirect(self, url, permanent=False):
        """Send a redirect to the client, forwarding to the specified URL. The
        `url` may be relative or absolute, relative URLs will be translated
        appropriately.
        """
        if self.session:
            self.session.save() # has to be done before the redirect is sent

        if permanent:
            status = 301 # 'Moved Permanently'
        elif self.method == 'POST':
            status = 303 # 'See Other' -- safe to use in response to a POST
        else:
            status = 302 # 'Found' -- normal temporary redirect

        self.send_response(status)
        if not url.startswith('http://') and not url.startswith('https://'):
            # Make sure the URL is absolute
            scheme, host = urlparse.urlparse(self.base_url)[:2]
            url = urlparse.urlunparse((scheme, host, url, None, None, None))

        self.send_header('Location', url)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Cache-control', 'no-cache')
        self.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        self.end_headers()

        if self.method != 'HEAD':
            self.write('Redirecting...')
        raise RequestDone

    def display(self, template, content_type='text/html', status=200):
        """Render the response using the ClearSilver template given by the
        `template` parameter, which can be either the name of the template file,
        or an already parsed `neo_cs.CS` object.
        """
        assert self.hdf, 'HDF dataset not available. Check your clearsilver installation'
        if self.args.has_key('hdfdump'):
            # FIXME: the administrator should probably be able to disable HDF
            #        dumps
            self.perm.require('TRAC_ADMIN')
            content_type = 'text/plain'
            data = str(self.hdf)
        else:
            try:
                form_token = self.form_token
            except AttributeError:
                form_token = None
            data = self.hdf.render(template, form_token)

        self.send(data, content_type, status)

    def send(self, content, content_type='text/html', status=200):
        self.send_response(status)
        self.send_header('Cache-control', 'must-revalidate')
        self.send_header('Content-Type', content_type + ';charset=utf-8')
        self.send_header('Content-Length', len(content))
        self.end_headers()

        if self.method != 'HEAD':
            self.write(content)
        raise RequestDone

    def send_error(self, exc_info, template='error.html',
                   content_type='text/html', status=500, env=None, data={}):
        try:
            if template.endswith('.cs') and self.hdf: # FIXME: remove this
                if self.args.has_key('hdfdump'):
                    self.perm.require('TRAC_ADMIN')
                    content_type = 'text/plain'
                    data = str(self.hdf)
                else:
                    data = self.hdf.render(template)

            if template.endswith('.html'):
                if env:
                    from trac.web.chrome import Chrome
                    from trac.util import translation
                    translation.activate(self.locale)
                    try:
                        data = Chrome(env).render_template(self, template,
                                                           data, 'text/html')
                    finally:
                        translation.deactivate()
                else:
                    content_type = 'text/plain'
                    data = '%s\n\n%s: %s' % (data.get('title'),
                                             data.get('type'),
                                             data.get('message'))
        except: # failed to render
            data = get_last_traceback()
            content_type = 'text/plain'

        self.send_response(status)
        self._outheaders = []
        self.send_header('Cache-control', 'must-revalidate')
        self.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        self.send_header('Content-Type', content_type + ';charset=utf-8')
        self.send_header('Content-Length', len(data))
        self._send_cookie_headers()

        self._write = self._start_response(self._status, self._outheaders,
                                           exc_info)

        if self.method != 'HEAD':
            self.write(data)
        raise RequestDone

    def send_file(self, path, mimetype=None):
        """Send a local file to the browser.
        
        This method includes the "Last-Modified", "Content-Type" and
        "Content-Length" headers in the response, corresponding to the file
        attributes. It also checks the last modification time of the local file
        against the "If-Modified-Since" provided by the user agent, and sends a
        "304 Not Modified" response if it matches.
        """
        if not os.path.isfile(path):
            raise HTTPNotFound("File %s not found" % path)

        stat = os.stat(path)
        mtime = datetime.fromtimestamp(stat.st_mtime, localtz)
        last_modified = http_date(mtime)
        if last_modified == self.get_header('If-Modified-Since'):
            self.send_response(304)
            self.end_headers()
            raise RequestDone

        if not mimetype:
            mimetype = mimetypes.guess_type(path)[0] or \
                       'application/octet-stream'

        self.send_response(200)
        self.send_header('Content-Type', mimetype)
        self.send_header('Content-Length', stat.st_size)
        self.send_header('Last-Modified', last_modified)
        self.end_headers()

        if self.method != 'HEAD':
            self._response = file(path, 'rb')
            file_wrapper = self.environ.get('wsgi.file_wrapper')
            if file_wrapper:
                self._response = file_wrapper(self._response, 4096)
        raise RequestDone

    def read(self, size=None):
        """Read the specified number of bytes from the request body."""
        fileobj = self.environ['wsgi.input']
        if size is None:
            size = self.get_header('Content-Length')
            if size is None:
                size = -1
            else:
                size = int(size)
        data = fileobj.read(size)
        return data

    def write(self, data):
        """Write the given data to the response body.

        `data` can be either a `str` or an `unicode` string.
        If it's the latter, the unicode string will be encoded
        using the charset specified in the ''Content-Type'' header
        or 'utf-8' otherwise.
        """
        if not self._write:
            self.end_headers()
        if isinstance(data, unicode):
            data = data.encode(self._outcharset or 'utf-8')
        self._write(data)

    # Internal methods

    def _parse_args(self):
        """Parse the supplied request parameters into a dictionary."""
        args = _RequestArgs()

        fp = self.environ['wsgi.input']

        # Avoid letting cgi.FieldStorage consume the input stream when the
        # request does not contain form data
        ctype = self.get_header('Content-Type')
        if ctype:
            ctype, options = cgi.parse_header(ctype)
        if ctype not in ('application/x-www-form-urlencoded',
                         'multipart/form-data'):
            fp = StringIO('')

        fs = cgi.FieldStorage(fp, environ=self.environ, keep_blank_values=True)
        if fs.list:
            for name in fs.keys():
                values = fs[name]
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    if not value.filename:
                        value = unicode(value.value, 'utf-8')
                    if name in args:
                        if isinstance(args[name], list):
                            args[name].append(value)
                        else:
                            args[name] = [args[name], value]
                    else:
                        args[name] = value

        return args

    def _parse_cookies(self):
        cookies = Cookie()
        header = self.get_header('Cookie')
        if header:
            cookies.load(header, ignore_parse_errors=True)
        return cookies

    def _parse_headers(self):
        headers = [(name[5:].replace('_', '-').lower(), value)
                   for name, value in self.environ.items()
                   if name.startswith('HTTP_')]
        if 'CONTENT_LENGTH' in self.environ:
            headers.append(('content-length', self.environ['CONTENT_LENGTH']))
        if 'CONTENT_TYPE' in self.environ:
            headers.append(('content-type', self.environ['CONTENT_TYPE']))
        return headers

    def _parse_languages(self):
        """The list of languages preferred by the remote user, taken from the
        ``Accept-Language`` header.
        """
        header = self.get_header('Accept-Language') or 'en-us'
        langs = []
        for lang in header.split(','):
            code, params = cgi.parse_header(lang)
            q = 1
            if 'q' in params:
                try:
                    q = float(params['q'])
                except ValueError:
                    q = 0
            langs.append((-q, code))
        langs.sort()
        return [code for q, code in langs]

    def _reconstruct_url(self):
        """Reconstruct the absolute base URL of the application."""
        host = self.get_header('Host')
        if not host:
            # Missing host header, so reconstruct the host from the
            # server name and port
            default_port = {'http': 80, 'https': 443}
            if self.server_port and self.server_port != default_port[self.scheme]:
                host = '%s:%d' % (self.server_name, self.server_port)
            else:
                host = self.server_name
        return urlparse.urlunparse((self.scheme, host, self.base_path, None,
                                    None, None))

    def _send_cookie_headers(self):
        for name in self.outcookie.keys():
            path = self.outcookie[name].get('path')
            if path:
                path = path.replace(' ', '%20') \
                           .replace(';', '%3B') \
                           .replace(',', '%3C')
            self.outcookie[name]['path'] = path

        cookies = self.outcookie.output(header='')
        for cookie in cookies.splitlines():
            self._outheaders.append(('Set-Cookie', cookie.strip()))


class IAuthenticator(Interface):
    """Extension point interface for components that can provide the name
    of the remote user."""

    def authenticate(req):
        """Return the name of the remote user, or `None` if the identity of the
        user is unknown."""


class IRequestHandler(Interface):
    """Extension point interface for request handlers."""

    def match_request(req):
        """Return whether the handler wants to process the given request."""

    def process_request(req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """


class IRequestFilter(Interface):
    """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""

    def pre_process_request(req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """

    # for ClearSilver templates
    def post_process_request(req, template, content_type):
        """Do any post-processing the request might need; typically adding
        values to req.hdf, or changing template or mime type.
        
        Always returns a tuple of (template, content_type), even if
        unchanged.

        (for 0.10 compatibility; only used together with ClearSilver templates)
        """

    # for Genshi templates
    def post_process_request(req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        (Since 0.11 - not yet stabilized)
        """


class ITemplateStreamFilter(Interface):
    """Filter a Genshi event stream prior to rendering."""

    def filter_stream(req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """
