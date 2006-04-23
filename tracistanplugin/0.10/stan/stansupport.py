# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 John Hampton <pacopablo@asylumware.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at:
# http://trac-hacks.org/wiki/TracBlogPlugin
#
# Author: John Hampton <pacopablo@asylumware.com>

import sys
import os
import os.path
import time
import datetime

from StringIO import StringIO
from pkg_resources import resource_filename

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, Chrome
from trac.web.api import RequestDone

from nevow.flat import flatten, ten
from nevow import rend
from nevow import tags as T

from nevow import accessors, inevow
#from zope.interface import implements, Interface
from twisted.python.components import registerAdapter

try:
    import tidy
except ImportError:
    tidy = False

__all__ = ['TracIStan', 'IStanRequestHandler', 'IStanRenderer', ]
__version__ = '0.1'

class DataVars(object):
    """Turn a dict into a class for notational convenience in templates.

    """
    def __init__(self, values):
        for k, v in values.iteritems():
            if isinstance(v, dict):
                setattr(self, k, DataVars(v))
            else:
                setattr(self, k, v)

    def __getattr__(self, key):
        print "__getattr__: %s returns None" % key
        return None
registerAdapter(accessors.ObjectContainer, DataVars, inevow.IContainer)

class IStanRequestHandler(Interface):
    """Extension point interface for Stan request handlers."""

    def match_request(req):
        """Return whether the handler wants to process the given request."""

    def process_request(req):
        """Process the request. Should return a (template_name, content_type)
        tuple, where `template` is the filename of the Stan template to use,
        and `content_type` is the MIME type of the content. If `content_type`
        is `None`, "text/html" is assumed.

        Note that if template processing should not occur, Why are you using
        this interface?
        """

class IStanRenderer(Interface):
    """Interface for defining render methods.

    The methods defined in the class that implements this interfaces are added
    to the namespace used by TracIStan.  This means that renderers from other
    plugins are available.  However, it also means that plugins should be
    careful not to stomp on each other's methods

    """

    def get_renderers():
        """Return a dictionary of method names and methods """
    

class StanEngine(Component):
    renderers = ExtensionPoint(IStanRenderer)

    def _inherits_tag (self, template, locals, globals):
        self.log.debug("called _inherits_tag")
        filename = self.find_template(template)
        self.__superTemplate = eval(file(filename, 'rU' ).read(), 
                                    locals, globals)
        return T.invisible

    def _replace_tag (self, slot):
        self.log.debug("called _replace_tag")
        self.log.debug("slot: %s" % str(slot))
        
        return T.invisible(slot=slot)

    def _include_tag (self, template, locals, globals):
        self.log.debug("called _include_tag")
        try:
            filename = self.find_template(template)
            return eval(file(filename, 'rU').read(),
                        locals, globals)
        except:
            print "ERROR IN INCLUDE", template
            raise

    def find_template (self, template):
        """Find the location of the template amongst the template dirs

        """
        filename = template
        try:
            template_dirs = self.template_dirs
        except KeyError:
            template_dirs = []

        for dir in template_dirs:
            absolute_path = os.path.join(dir, filename)
            if os.path.exists(absolute_path):
                return absolute_path
            continue
        return filename

    def render(self, info, format="html", fragment=False, template=None):
        """Renders the template to a string using the provided info.

        info: dict of variables to pass into template
        format: can only be "html" at this point
        template: path to template

        """
        self.__superTemplate = None

        filename = self.find_template(template)

        ns = {}

        if format.startswith('tidy.'):
            pretty, format = format.split('.')
        else:
            pretty = False
        if format == 'html':
            ns.update(__import__('nevow.tags', ns, ns, ['__all__']).__dict__)
            ns.update(__import__('nevow.entities', ns, ns, 
                                 ['__all__']).__dict__)
        else: # import user-defined Stan tags
            ns.update(__import__('%s.tags' % format, ns, ns, 
                                 ['__all__']).__dict__)

        protected = ['vars', 'render', 'inherits', 'replace', 'include',
                     'formerror', ]
        ns['vars'] = DataVars(info)
#        if self.get_extra_vars:
#            ns['std'] = self.get_extra_vars (  ) [ 'std' ]
        ns['render'] = rend
        ns['inherits'] = lambda template: self._inherits_tag(template, ns, ns)
        ns['replace'] = ns ['override'] = self._replace_tag
        ns['include'] = lambda template: self._include_tag(template, ns, ns)
        ns['formerror'] = T.Proto('form:error')
        for renderer in self.renderers:
            funcs = renderer.get_renderers()
            for key in funcs.keys():
                if key in protected:
                    del funcs[key]
                continue
            ns.update(funcs)
            continue

        try:
            self.__template = eval(file(filename, 'rU').read(), ns, ns)
        except:
            print "ERROR IN TEMPLATE", filename
            raise

        if self.__superTemplate:
            parts = dict([ (c.attributes['slot'], flatten(c.children))
                           for c in self.__template.children])
            
            from pprint import PrettyPrinter
            ppstream = StringIO() 
            pp = PrettyPrinter(stream=ppstream)
            pp.pprint(parts)
            self.log.debug("parts: %s" % ppstream.getvalue())
            for slot, fragment in parts.items():
                self.__superTemplate.fillSlots(slot, fragment)
            from pprint import PrettyPrinter
            ppstream = StringIO() 
            pp = PrettyPrinter(stream=ppstream)
            pp.pprint(self.__superTemplate)
            self.log.debug("__superTemplate: %s" % ppstream.getvalue())
            output = flatten(self.__superTemplate)
        else:
            output = flatten(self.__template)

        if pretty and tidy:
            options = dict ( input_xml = True,
                             output_xhtml = True,
                             add_xml_decl = False,
                             doctype = 'omit',
                             indent = 'auto',
                             tidy_mark = False )
            return str(tidy.parseString(output, **options))

        return output

class TracStanRenderers(Component):
    implements(IStanRenderer)

    def get_renderers(self):
        """Map methods to method names"""
        self.log.debug("called get_renderers")
        return {'tracPageTitle' : self._pageTitle,
                'tracNoRobots' : self._robots,
                'tracLinks' : self._links,
                'tracScript' : self._scripts,
                'tracProjectLogo' : self._project_logo,
                'includeCS' : self._include_cs,
               }

    def _pageTitle(self, context, data):
        self.log.debug("called _pageTitle")
        self.log.debug("data: %s" % str(type(data)))
        if data.project.name_encoded:
            t = [data.title or '',
                 ' - ',
                 data.project.name_encoded,
                 ' - Trac',]
        else:
            t = ['Trac: ',
                 data.project.name_encoded,]
        return context.tag[''.join(t)]

    def _robots(self, context, data):
        self.log.debug("called _robots")
        if data.html.norobots:
            return context.tag(name="ROBOTS", content="NOINDEX, NOFOLLOW")

    def _links(self, context, data):
        self.log.debug("called _links")
        return ''

    def _scripts(self, context, data):
        self.log.debug("called _scripts")
        return ''

    def _include_cs(self, context, data):
        self.log.debug("called _include_cs")
        return '<!-- THis is cs stuff -->'

    def _project_logo(self, context, data):
        self.log.debug("called _project_logo")
        href = data.chrome.logo.link
        logosrc = data.chrome.logo.src
        logowidth = data.chrome.logo.width
        logoheight = data.chrome.logo.height
        logoalt = data.chome.logo.alt
        if logosrc:
            image = T.img(src=logosrc, width=logowidth, height=logoheight, 
                          alt=logoalt)
            print 'logosrc present: %s' % str(image)
            return context.tag [T.a(id="logo", href=href)[image], T.hr]
        else:
            image = data.project.name_encoded
            if image:
                return context.tag[T.h1 [ T.a(id="logo", href=href)[image] ]]
        return ""
        
class TracIStan(Component):
    """Interface for using the Stan templating language

    To use Stan for templates instead of ClearSilver, simply subclass this
    class.  It implements the IRequestHandler and ITemplateProvider interfaces.
    
    Instead of returning a template name and content_type, the return line
    should look like:

    return self._return(req, 'templatename.stan', 'content_type')

    As usual, if content_type is ommitted, then text/html is assumed.
    
    """
#    abstract = True
    implements(IRequestHandler, ITemplateProvider)
    stanreqhandlers = ExtensionPoint(IStanRequestHandler)

    def __init__(self):
        self.stantheman = StanEngine(self.env)

    # IRequestHandler methods
    def match_request(self, req):
        self.log.debug('IStanRequestHandlers:')
        [self.log.debug('  Stan Request Handler   : %s' % type(x).__name__)
             for x in self.stanreqhandlers]
        for handler in self.stanreqhandlers:
            if handler.match_request(req):
                return True
            continue
        return False

    def process_request(self, req):
        for handler in self.stanreqhandlers:
            if handler.match_request(req):
                chosen_handler = handler
                break
            continue
        req.standata = {}
        hdf = getattr(req, 'hdf', None)
        if hdf:
            req.standata.update(self._convert_hdf_to_data(hdf))
        template, content_type = chosen_handler.process_request(req)
        content_type = content_type or 'text/html'
        self._return(req, template, content_type)
        return None

    def _return(self, req, template, content_type='text/html'):
        """ Wrap the return so that things are processed by Stan
    
        """
        if req.args.has_key('hdfdump'):
            # FIXME: the administrator should probably be able to disable HDF
            #        dumps
            from pprint import PrettyPrinter
            outstream = StringIO()
            pp = PrettyPrinter(stream=outstream)
            pp.pprint(req.standata)
            content_type = 'text/plain'
            data = outstream.getvalue()
            outstream.close()
        else:
            data = self._render(req.standata, template)
         
        req.send_response(200)
        req.send_header('Cache-control', 'must-revalidate')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', content_type + ';charset=utf-8')
        req.send_header('Content-Length', len(data))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(data)
        pass

    def _render(self, data, template):
        c = Chrome(self.env)
        self.stantheman.template_dirs = c.get_all_templates_dirs()
        return self.stantheman.render(data, template=template)

    def _convert_hdf_to_data(self, hdf):
        """Converts an HDFWrapper to a dictionary

        """
        def reformat_data(data):
            """Check to see if the keys are sequential numbers and reformats 
               into a list

            """
            try:
                keys = [int(k) for k in data.keys()]
                keys.sort()
                datalist = [data[str(k)] for k in keys]
                return datalist
            except ValueError:
                return data

        def hdf_tree_walk(node):
            d = {}
            while node:
                name = node.name() or ''
                value = node.value()
                if (value or not node.child()) and name:
                    d[name] = value.strip()
                if node.child() and name:
                    data = hdf_tree_walk(node.child())
                    data = reformat_data(data)
                    if data:
                        d[name] = data
                node = node.next()
            return d

        return hdf_tree_walk(hdf.hdf.child())

    # ITemplateProvider
    def get_templates_dirs(self):
        """ Return the absolute path of the directory containing the provided
            templates

        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """ Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.

        """
#        return [('blog', resource_filename(__name__, 'htdocs'))]
        return []



