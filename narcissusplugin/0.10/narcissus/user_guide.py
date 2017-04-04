# Narcissus plugin for Trac

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.util import escape, Markup

class NarcissusPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'narcissus'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/user_guide'

    def process_request(self, req):
        req.hdf['trac.href.narcissus'] = self.env.href.narcissus()
        req.hdf['trac.href.configure'] = self.env.href.configure()
        req.hdf['trac.href.user_guide'] = self.env.href.user_guide()

        req.hdf['main'] = "no"
        req.hdf['config'] = "no"
        req.hdf['user_guide'] = "yes"

        return 'user_guide.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided ClearSilver
        templates.
        """

        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('nar', resource_filename(__name__, 'htdocs'))]
