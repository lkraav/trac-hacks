# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import sys
from types import GeneratorType
from pkg_resources import resource_filename

from trac.core import Component, ExtensionPoint, TracError, implements
from trac.perm import PermissionError
from trac.resource import ResourceNotFound
from trac.util.html import tag
from trac.util.text import to_unicode
from trac.web.api import RequestDone, HTTPUnsupportedMediaType
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet, add_script, Chrome, web_context
from trac.wiki.formatter import format_to_oneliner

from tracrpc.api import XMLRPCSystem, IRPCProtocol, ProtocolException, \
                        ServiceException
from tracrpc.util import accepts_mimetype, exception_to_unicode

try:
    from trac.web.api import HTTPInternalError as HTTPInternalServerError
except ImportError:  # Trac 1.3.1+
    from trac.web.api import HTTPInternalServerError

if hasattr(Chrome, 'jenv'):
    from trac.util.text import jinja2template
    import jinja2
    genshi = None
else:
    jinja2template = None
    jinja2 = None
    import genshi
    import genshi.template
    import genshi.template.text

__all__ = ['RPCWeb']

class RPCWeb(Component):
    """ Handle RPC calls from HTTP clients, as well as presenting a list of
        methods available to the currently logged in user. Browsing to
        <trac>/rpc or <trac>/login/rpc will display this list. """

    implements(IRequestHandler, ITemplateProvider, INavigationContributor)

    protocols = ExtensionPoint(IRPCProtocol)

    # IRequestHandler methods

    def match_request(self, req):
        """ Look for available protocols serving at requested path and
            content-type. """
        content_type = req.get_header('Content-Type') or 'text/html'
        must_handle_request = req.path_info in ('/rpc', '/login/rpc')
        for protocol in self.protocols:
            for p_path, p_type in protocol.rpc_match():
                if req.path_info in ['/%s' % p_path, '/login/%s' % p_path]:
                    must_handle_request = True
                    if content_type.startswith(p_type):
                        req.args['protocol'] = protocol
                        return True
        # No protocol call, need to handle for docs or error if handled path
        return must_handle_request

    def process_request(self, req):
        protocol = req.args.get('protocol', None)
        content_type = req.get_header('Content-Type') or 'text/html'
        if protocol:
            # Perform the method call
            self.log.debug("RPC incoming request of content type '%s' "
                           "dispatched to %s", content_type, repr(protocol))
            self._rpc_process(req, protocol, content_type)
        elif accepts_mimetype(req, 'text/html') \
                    or content_type.startswith('text/html'):
            return self._dump_docs(req)
        else:
            # Attempt at API call gone wrong. Raise a plain-text 415 error
            body = "No protocol matching Content-Type '%s' at path '%s'." % (
                                                content_type, req.path_info)
            self.log.error(body)
            req.send_error(None, template='', content_type='text/plain',
                    status=HTTPUnsupportedMediaType.code, env=None, data=body)

    # Internal methods

    def _dump_docs(self, req):
        self.log.debug("Rendering docs")

        # Dump RPC documentation
        req.perm.require('XML_RPC')  # Need at least XML_RPC
        namespaces = {}
        ctxt = web_context(req)
        for method in XMLRPCSystem(self.env).all_methods(req):
            namespace = method.namespace.replace('.', '_')
            if namespace not in namespaces:
                namespaces[namespace] = {
                    'description': format_to_oneliner(self.env, ctxt,
                                    method.namespace_description),
                    'methods': [],
                    'namespace': method.namespace,
                    }
            try:
                namespaces[namespace]['methods'].append(
                        (method.signature,
                        format_to_oneliner(self.env, ctxt,
                            method.description),
                        method.permission))
            except Exception as e:
                from tracrpc.util import StringIO
                import traceback
                out = StringIO()
                traceback.print_exc(file=out)
                raise Exception('%s: %s\n%s' % (method.name,
                                                str(e), out.getvalue()))
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'tracrpc/rpc.css')
        add_script(req, 'tracrpc/rpc.js')
        data = {
            'rpc': {
                'functions': namespaces,
                'protocols': [p.rpc_info() + (list(p.rpc_match()),)
                              for p in self.protocols],
                'version': __import__('tracrpc', ['__version__']).__version__,
            },
        }
        if hasattr(Chrome, 'jenv'):
            data['expand_docs'] = self._expand_docs_jinja
            return 'rpc_jinja.html', data
        else:
            data['expand_docs'] = self._expand_docs_genshi
            return 'rpc.html', data, None

    def _expand_docs_jinja(self, context, docs):
        try:
            template = jinja2template(docs, text=True,
                                      line_statement_prefix=None,
                                      line_comment_prefix=None)
            return template.render(context)
        except jinja2.TemplateError as e:
            self.log.error("Template error rendering protocol documentation%s",
                           exception_to_unicode(e, traceback=True))
            return '**Error**: {{{%s}}}' % exception_to_unicode(e)
        except Exception as e:
            self.log.error("Runtime error rendering protocol documentation%s",
                           exception_to_unicode(e, traceback=True))
            return "Error rendering protocol documentation. " \
                   "Contact your '''Trac''' administrator for details"
    if jinja2:
        _expand_docs_jinja = jinja2.contextfunction(_expand_docs_jinja)

    def _expand_docs_genshi(self, docs, ctx):
        try :
            tmpl = genshi.template.text.NewTextTemplate(docs)
            return tmpl.generate(**dict(ctx.items())).render()
        except genshi.template.TemplateError as e:
            self.log.error("Template error rendering protocol documentation%s",
                           exception_to_unicode(e, traceback=True))
            return '**Error**: {{{%s}}}' % exception_to_unicode(e)
        except Exception as e:
            self.log.error("Runtime error rendering protocol documentation%s",
                           exception_to_unicode(e, traceback=True))
            return "Error rendering protocol documentation. " \
                   "Contact your '''Trac''' administrator for details"

    def _rpc_process(self, req, protocol, content_type):
        """Process incoming RPC request and finalize response."""
        proto_id = protocol.rpc_info()[0]
        rpcreq = req.rpc = {'mimetype': content_type}
        self.log.debug("RPC(%s) call by '%s'", proto_id, req.authname)
        try:
            if req.path_info.startswith('/login/') and \
                    req.authname == 'anonymous':
                raise TracError("Authentication information not available")
            rpcreq = req.rpc = protocol.parse_rpc_request(req, content_type)
            rpcreq['mimetype'] = content_type

            # Important ! Check after parsing RPC request to add
            #             protocol-specific fields in response
            #             (e.g. JSON-RPC response `id`)
            req.perm.require('XML_RPC') # Need at least XML_RPC

            method_name = rpcreq.get('method')
            if method_name is None :
                raise ProtocolException('Missing method name')
            args = rpcreq.get('params') or []
            self.log.debug("RPC(%s) call by '%s' %s", proto_id,
                           req.authname, method_name)
            try :
                result = (XMLRPCSystem(self.env).get_method(method_name)(req, args))[0]
                if isinstance(result, GeneratorType):
                    result = list(result)
            except (TracError, PermissionError, ResourceNotFound) as e:
                raise
            except Exception:
                e, tb = sys.exc_info()[-2:]
                self.log.error("RPC(%s) [%s] Exception caught while calling "
                               "%s(*%r) by %s%s", proto_id, req.remote_addr,
                               method_name, args, req.authname,
                               exception_to_unicode(e, traceback=True))
                raise ServiceException(e), None, tb
            else :
                protocol.send_rpc_result(req, result)
        except RequestDone :
            raise
        except (TracError, PermissionError, ResourceNotFound) as e:
            if type(e) is not ServiceException:
                self.log.warning("RPC(%s) [%s] %s", proto_id, req.remote_addr,
                                 exception_to_unicode(e))
            try :
                protocol.send_rpc_error(req, e)
            except RequestDone :
                raise
            except Exception as e :
                self.log.exception("RPC(%s) Unhandled protocol error", proto_id)
                self._send_unknown_error(req, e)
        except Exception as e :
            self.log.exception("RPC(%s) Unhandled protocol error", proto_id)
            self._send_unknown_error(req, e)

    def _send_unknown_error(self, req, e):
        """Last recourse if protocol cannot handle the RPC request | error"""
        method_name = req.rpc and req.rpc.get('method') or '(undefined)'
        body = "Unhandled protocol error calling '%s': %s" % (
                                        method_name, to_unicode(e))
        req.send_error(None, template='', content_type='text/plain',
                            env=None, data=body,
                            status=HTTPInternalServerError.code)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        yield ('tracrpc', resource_filename(__name__, 'htdocs'))

    def get_templates_dirs(self):
        yield resource_filename(__name__, 'templates')

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        pass

    def get_navigation_items(self, req):
        if req.perm.has_permission('XML_RPC'):
            yield ('metanav', 'rpc',
                   tag.a('API', href=req.href.rpc(), accesskey=1))

