import re
from genshi.builder import tag
from trac.config import Option, BoolOption, IntOption, ListOption
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.resource import Resource, ResourceNotFound
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import Chrome, add_ctxtnav, add_stylesheet, \
                            INavigationContributor, ITemplateProvider
from handlers import IFieldHandler
from droplets import Droplet
from chefapi import ChefApi
from awsapi import AwsApi


class CloudModule(Component):
    """Orchestrates AWS cloud resources via Chef.  Leans heavily on boto
    and PyChef and borrowed much from the built-in report component."""

    implements(ITemplateProvider, INavigationContributor, IPermissionRequestor,
               IRequestHandler)
    
    # trac.ini options
    nav_label = Option('cloud', 'nav_label', _('Cloud'), _("Top nav label."))
    
    aws_key = Option('cloud', 'aws_key', '', _("AWS/S3 access key."))
    
    aws_secret = Option('cloud', 'aws_secret', '', _("AWS/S3 secret."))
    
    aws_keypair = Option('cloud', 'aws_keypair', '', _("AWS/S3 keypair name."))
    
    aws_keypair_pem = Option('cloud', 'aws_keypair_pem', '',
        _("AWS/EC2 keypair file path."))
    
    aws_username = Option('cloud', 'aws_username', 'ubuntu',
        _("AWS/EC2 ssh username."))
    
    chef_base_path = Option('cloud', 'chef_base_path', '',
        _("Directory where .chef configs can be found."))
    
    chef_boot_run_list = ListOption('cloud', 'chef_boot_run_list', [],
        _("If set, used instead of the role(s) to bootstrap instances."))
    
    chef_boot_sudo = BoolOption('cloud', 'chef_boot_sudo', True,
        _("Whether the chef knife bootstrap should be run as sudo."))
    
    default_resource = Option('cloud', 'default_resource', '',
        _("Name of the AWS resource to show if not provided in url."))
    
    items_per_page = IntOption('cloud', 'items_per_page', 100,
        _("Number of items displayed per page in cloud reports by default"))
    
    items_per_page_rss = IntOption('cloud', 'items_per_page_rss', 0,
        _("Number of items displayed in the rss feeds for cloud reports"))
    
    # NOTE: Each droplet's [cloud.*] config is retrieved during its init.
    
    
    field_handlers = ExtensionPoint(IFieldHandler)
    
        
    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('cloud', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    
    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'cloud'

    def get_navigation_items(self, req):
        if 'CLOUD_VIEW' in req.perm:
            yield ('mainnav', 'cloud',
                   tag.a(self.nav_label, href=req.href.cloud()))
    
    
    # IPermissionRequestor methods  
    
    def get_permission_actions(self):  
        actions = ['CLOUD_CREATE','CLOUD_DELETE','CLOUD_MODIFY','CLOUD_VIEW']  
        return actions + [('CLOUD_ADMIN',actions)]  
    
    
    # IRequestHandler methods
    
    def match_request(self, req):
        match = re.match(r'/cloud(?:/([^/]+)(?:/([\w.\-]+))?)?$', req.path_info)
        if match:
            if match.group(1):
                req.args['droplet_name'] = match.group(1)
            if match.group(2):
                req.args['id'] = match.group(2)
            return True

    def process_request(self, req):
        req.perm.require('CLOUD_VIEW')
        
        # setup cloud droplets
        if not hasattr(self, 'droplets'):
            # setup chefapi and cloudapi
            chefapi = ChefApi(self.chef_base_path,
                              self.aws_keypair_pem,
                              self.aws_username,
                              self.chef_boot_run_list,
                              self.chef_boot_sudo,
                              self.log)
            
            cloudapi = AwsApi(self.aws_key,
                              self.aws_secret,
                              self.aws_keypair,
                              self.log)
            
            # instantiate each droplet (singletons)
            self.droplets = {}
            self.titles = Droplet.titles(self.env)
            for order_,droplet_name,title_ in self.titles:
                self.droplets[droplet_name] = Droplet.new(self.env,
                    droplet_name, chefapi, cloudapi,
                    self.field_handlers, self.log)
        
        # ensure at least one droplet exists
        if not self.droplets:
            raise ResourceNotFound(
                _("No cloud resources found in trac.ini."),
                _('Missing Cloud Resource'))
        
        droplet_name = req.args.get('droplet_name', '')
        id = req.args.get('id', '')
        action = req.args.get('action', 'view')
        
        if not droplet_name:
            droplet_name = self.default_resource
            if not droplet_name:
                o_,droplet_name,t_ = self.titles[0]
            req.redirect(req.href.cloud(droplet_name))
        
        # check for valid kind
        if droplet_name not in self.droplets:
            raise ResourceNotFound(
                _("Cloud resource '%(droplet_name)s' does not exist.",
                  droplet_name=droplet_name),
                _('Invalid Cloud Resource'))
            
        # retrieve the droplet
        droplet = self.droplets[droplet_name]
        
        # route the request
        if req.method == 'POST':
            if 'cancel' in req.args:
                req.redirect(req.href.cloud(droplet_name,id))
            elif action == 'new':
                droplet.create(req)
            elif action == 'delete':
                droplet.delete(req, id)
            elif action == 'edit':
                droplet.save(req, id)
        else: # req.method == 'GET':
            if action in ('edit', 'new'):
                template, data, content_type = droplet.render_edit(req, id)
                Chrome(self.env).add_wiki_toolbars(req)
            elif action == 'delete':
                template, data, content_type = droplet.render_delete(req, id)
            elif id == '':
                template, data, content_type = droplet.render_grid(req)
                if content_type: # i.e. alternate format
                    return template, data, content_type
            else:
                template, data, content_type = droplet.render_view(req, id)
                if content_type: # i.e. alternate format
                    return template, data, content_type
        
        # add contextual nav
        for order_,droplet_name,title in self.titles:
            add_ctxtnav(req, title, href=req.href.cloud(droplet_name))
        
        add_stylesheet(req, 'common/css/report.css') # reuse css
        return template, data, None
