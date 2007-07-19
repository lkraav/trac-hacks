# ManualTesting.MTP_TemplateProvider

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.util import escape

class MTP_TemplateProvider(Component):
    implements(ITemplateProvider)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided ClearSilver
        templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'htdocs/templates')]

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
        return [('mt', resource_filename(__name__, 'htdocs'))]