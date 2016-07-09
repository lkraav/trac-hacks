from pkg_resources import resource_filename

from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script

class SubComponentsModule(Component):
    """Implements subcomponents in Trac's interface."""
    
    implements(IRequestFilter, ITemplateProvider) #, ITemplateStreamFilter)
 
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket/') or \
           req.path_info.startswith('/newticket') or \
           req.path_info.startswith('/query'):
            add_script(req, 'subcomponents/componentselect.js')                      
        
        return template, data, content_type        
 
  
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('subcomponents', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [resource_filename(__name__, 'templates')]


    # ITemplateStreamFilter
#    def filter_stream(self, req, method, filename, stream, data):
 #       # Add the componentselect.js file to several templates
     #   return stream
    #
