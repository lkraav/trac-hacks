from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.admin.api import IAdminPanelProvider

import os

class SVNAuthzPlugin(Component):
    implements(ITemplateProvider, IAdminPanelProvider)
    
    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('svn', 'Subversion', 'authz', 'Permissions')
    
    def render_admin_panel(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')
        
        # get default authz file from trac.ini
        authz_file = self.config.get('trac', 'authz_file')
        
        # test if authz file exists and is writable
        if not os.access(authz_file,os.W_OK|os.R_OK):
            raise TracError("Can't access authz file %s" % authz_file)
        
        # evaluate forms
        if req.method == 'POST':
            current=req.args.get('current').strip().replace('\r', '')
            
            # encode to utf-8
            current = current.encode('utf-8')
            
            # parse and validate authz file with a config parser
            from ConfigParser import ConfigParser
            from StringIO import StringIO
            cp = ConfigParser()
            try:
                cp.readfp(StringIO(current))
            except Exception, e:
                raise TracError("Invalid Syntax: %s" % e)
            
            # write to disk
            try:
                fp = open(authz_file, 'wb')
                current = fp.write(current)
                fp.close()
            except Exception, e:
                raise TracError("Can't write authz file: %s" % e)
        
        # read current authz file
        current = ""
        try:
            fp = open(authz_file,'r')
            current = fp.read()
            fp.close() 
        except:
            pass
        
        return 'svnauthz.html', {'auth_data':current}
    
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        return []