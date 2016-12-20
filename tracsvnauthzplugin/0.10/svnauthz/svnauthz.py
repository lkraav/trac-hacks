from trac.core import *
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider

import os
import subprocess


__all__ = ['SVNAuthzPlugin']


class SVNAuthzPlugin(Component):
    implements(ITemplateProvider, IAdminPageProvider)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('svn', 'Subversion', 'authz', 'Permissions')

    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')
        
        # get default authz file from trac.ini
        authz_file = self.config.get('trac', 'authz_file')
        
        # test if authz file exists and is writable
        if not os.access(authz_file, os.W_OK|os.R_OK):
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
            
            # create .reload file for cronjob
            try:
                TRAC_PATH = '/'.join(self.env.path.split('/')[:-1])
                subprocess.call("touch " + TRAC_PATH + os.sep + ".reload",
                                shell=True)
            except Exception:
                raise TracError("Can't create .reload file")
        # read current authz file
        current = ""
        try:
            fp = open(authz_file, 'r')
            current = fp.read()
            fp.close() 
        except Exception:
            pass
        
        req.hdf['svnauthz.current'] = current
        
        return 'svnauthz.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)
        
        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []