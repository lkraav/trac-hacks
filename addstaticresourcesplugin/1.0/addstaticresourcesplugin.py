import re

#from trac.config import BoolOption, IntOption, ListOption
from trac.core import Component, implements
from trac.web import IRequestFilter
from trac.web.chrome import add_stylesheet, add_script, Chrome

srkey = "static_resources"


def urljoin(*args):
    return '/'.join([i.strip('/') for i in args])


class AddStaticResourcesComponent(Component):
    implements(IRequestFilter)

    def __init__(self):
        self.resources = self.env.config.options(srkey)

    # IRequestHandler methods
    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.

        Always returns the request handler, even if unchanged.
        """
        if(type(handler) == Chrome):
            return handler

        self.log.debug("Maybe adding resources to %s ,%s", req, handler)
        conf = self.env.config
        resources = conf.options(srkey)
        for regex, value in resources:
            match = re.search(regex, req.path_info, re.IGNORECASE)
            self.log.debug("Regex:'%s' matched:%s", regex, match)
            if match:
                paths = conf.getlist(srkey, regex)
                for p in paths:
                    if p.endswith("js"):
                        add_script(req, urljoin('shared', p))
                    elif p.endswith("css"):
                        add_stylesheet(req, urljoin('shared', p))

        return handler

    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.

        `data` may be update in place.
        Always returns a tuple of (template, data, content_type), even if
        unchanged.
        Note that `template`, `data`, `content_type` will be `None` if:
        - called when processing an error page
        - the default request handler did not return any result
        (Since 0.11)
        """
        ## Nothing to do here.
        return (template, data, content_type)
