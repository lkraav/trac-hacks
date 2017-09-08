import re

from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.admin.api import IAdminPanelProvider
from trac.util.translation import _

class BasicThemeEditorAdminPanel(Component):

  implements(IAdminPanelProvider, ITemplateProvider)

  # IAdminPanelProvider methods

  def get_admin_panels(self, req):
    if 'TRAC_ADMIN' in req.perm:
      yield ('general', _('General'), 'basic_theme_editor', _('Basic Theme Editor'))

  def render_admin_panel(self, req, cat, page, path_info):
    req.perm.require('TRAC_ADMIN')

    if req.method == 'POST':
      self.config.set('header_logo', 'src', req.args.get('logo_src'))
      self.config.set('header_logo', 'link', req.args.get('logo_link'))
      self.config.set('header_logo', 'alt', req.args.get('logo_alt'))
      
      self.config.set('project', 'icon', req.args.get('project_icon'))
      self.config.set('project', 'css', req.args.get('project_css'))
      self.config.set('project', 'footer', req.args.get('project_footer'))
      
      self.config.save()
      req.redirect(req.href.admin(cat, page))

    data = {
      'logo_src' : self.config.get('header_logo', 'src'),
      'logo_link' : self.config.get('header_logo', 'link'),
      'logo_alt' : self.config.get('header_logo', 'alt'),
      
      'project_icon' : self.config.get('project', 'icon'),
      'project_css' : self.config.get('project', 'css'),
      'project_footer' : self.config.get('project', 'footer')
    }
    
    return 'admin_themeeditor.html', data

  # ITemplateProvider methods
  
  def get_templates_dirs(self):
    from pkg_resources import resource_filename
    return [resource_filename(__name__, 'templates')]
  
  def get_htdocs_dirs(self):
    return []
    
class CssInjector(Component):
  
  implements(IRequestFilter) 
  
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
    
    if template:
      css_url = self.config.get('project', 'css', '')
      if len(css_url) != 0:
        add_stylesheet(req, css_url)
    
    return (template, data, content_type)

  def pre_process_request(self, req, handler):
    """Called after initial handler selection, and can be used to change
    the selected handler or redirect request.
    
    Always returns the request handler, even if unchanged.
    """
    return handler
    