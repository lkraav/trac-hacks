from datetime import date
from genshi.builder import tag

from trac.core import *
from trac.config import BoolOption, Option
from trac.resource import Resource
from trac.ticket import Version
from trac.util.datefmt import get_datetime_format_hint, parse_date
from trac.util.translation import _
#from trac.web.chrome import add_link, add_notice, add_stylesheet, add_warning

### interfaces:  
from trac.web.api import IRequestHandler, IRequestFilter
from trac.web.chrome import INavigationContributor


class ReleasesModule(Component):
    implements(INavigationContributor, IRequestHandler, IRequestFilter)

    navigation = BoolOption('extended_version', 'roadmap_navigation', 'false',
        doc="""Whether to add a link to the main navigation bar.""")
    navigation_item = Option('extended_version', 'navigation_item', 'roadmap',
        doc="""The name for the navigation item to highlight.
        
        May be set to 'roadmap' to highlight the navigation provided by the core
        ticket module. If roadmap_navigation is also set to true, this completely
        replaces the main navigation for the core roadmap.""")

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'versions'

    def get_navigation_items(self, req):
        if self.navigation and 'VERSION_VIEW' in req.perm:
            if self.navigation_item == 'roadmap':
                yield ('mainnav', 'versions',
                               tag.a(_('Roadmap'), href=req.href.versions()))
            elif self.navigation_item == 'versions':
                yield ('mainnav', self.navigation_item,
                               tag.a(_('Versions'), href=req.href.versions()))

    # IRequestHandler methods

    def match_request(self, req):
        return '/versions' == req.path_info
        #match = re.match(r'/versions$', req.path_info)
        #if match:
        #    return True

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if self.navigation and 'VERSION_VIEW' in req.perm and self.navigation_item == 'roadmap':
            self._remove_item(req, self.navigation_item)
        return template, data, content_type

    def process_request(self, req):
        req.perm.require('VERSION_VIEW')

        showall = req.args.get('show') == 'all'

        db = self.env.get_read_db()
        versions = []
        resources = []
        is_released = []
        for v in Version.select(self.env, db):
            r = Resource('version', v.name)
            ir = v.time and v.time.date() < date.today()

            # apply more visibiity
            if (showall or not ir) and 'VERSION_VIEW' in req.perm(r):
                versions.append(v)
                resources.append(r)
                is_released.append(v.time and v.time.date() < date.today())

        versions.reverse(),
        resources.reverse(),
        is_released.reverse(),

        data = {
            'versions': versions,
            'resources': resources,
            'is_released': is_released,
            'showall': showall,
        }
        return 'versions.html', data, None

    def _remove_item(self, req, name):

        navitems = req.chrome['nav']['mainnav']

        active = False;
        for navitem in navitems:
            if navitem['active'] and navitem['name'] == name:
                active = True
            if navitem['name'] == name:
                navitems.remove(navitem)
        if active:
            for navitem in navitems:
                if navitem['name'] == 'versions':
                    navitem['active'] = True
