# The Trac-hacks autoinstaller

# Table format
# hacks (id, name, type, current, installed, readme, install)

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider, add_stylesheet
from webadmin.web_ui import IAdminPageProvider
from db_default import default_table
from core import *
import urlparse, xmlrpclib

__all__ = ['HackInstallPlugin']

def add_userpass_to_url(url, user=None, password=None):
    """Given a URL, add login data."""
    parts = list(urlparse.urlsplit(url))
    if user:
        if password:
            user = user + ':' + password
        parts[1] = user + '@' + parts[1]
    return urlparse.urlunsplit(parts)

class HackInstallPlugin(Component):
    """A component managing plugin installation."""
    
    implements(IEnvironmentSetupParticipant, ITemplateProvider, IAdminPageProvider)
    
    def __init__(self):
        """Perform basic initializations."""
        url = self.config.get('hackinstall','url',default='http://trac-hacks.org')
        builddir = self.config.get('hackinstall','builddir')
        version = self.config.get('hackinstall','version')
        self.installer = HackInstaller(self.env, url, builddir, version)
        self.rpc_url = add_userpass_to_url(url+'/login/xmlrpc','TracHacks')

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN') or True:
            yield ('hacks', 'Trac-Hacks', 'general', 'General')
            yield ('hacks', 'Trac-Hacks', 'plugins', 'Plugins')
            #yield ('hacks', 'Trac-Hacks', 'macros', 'Macros')
            
    def process_admin_request(self, req, cat, page, path_info):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        self.plugins = self._get_hacks('plugin')
        self.macros = self._get_hacks('macro')        
        
        if req.method == 'POST':
            if page == 'general':
                if 'update' in req.args:
                    self._check_version()
                    self._update('plugin')
            elif page == 'plugins':
                installs = [k[8:] for k in req.args.keys() if k.startswith('install_')]
                if installs:
                    req.hdf['hackinstall.message'] = "Installing plugin %s" % (installs[0])
                    self.installer.install_hack(installs[0], self.plugins[installs[0]]['current'])

        req.hdf['hackinstall'] = { 'version': self.installer.version, 'url': self.installer.url }
        req.hdf['hackinstall.plugins'] = self.plugins
        req.hdf['hackinstall.macros'] = self.macros
        for x in ['general', 'plugins', 'macros']:
            req.hdf['hackinstall.hdf.%s'%x] = self.env.href.admin('hacks',x)
        
        template = { 'general': 'hackinstall_admin.cs', 'plugins': 'hackinstall_admin_plugin.cs', 'macros': 'hackinstall_admin_macro.cs' }[page]
        return template, None

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM hacks")
            return False
        except: # Is there some way to only catch DatabaseErrors?
            return True
        
    def upgrade_environment(self, db):
        cursor = db.cursor()
        for sql in db.to_sql(default_table):
            self.log.debug(sql)
            cursor.execute(sql)
        db.commit()   

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
        from pkg_resources import resource_filename
        return [('hackinstall', resource_filename(__name__, 'htdocs'))]

    # Internal methods
    def _get_hacks(self, type):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        hacks = {}
        cursor.execute('SELECT id, name, current FROM hacks WHERE type = %s', (type,))
        for row in cursor:
            hacks[row[1]] = {'id': row[0], 'current': row[2]}
        return hacks
        
    def _check_version(self):
        """Verify that we have a valid version of Trac."""
        server = xmlrpclib.ServerProxy(self.rpc_url)
        versions = server.trachacks.getReleases()
        if self.installer.version not in versions:
            raise TracError, "Trac-Hacks doesn't know about your version of Trac (%s)" % (self.version)
        return True
          
    def _update(self, type):
        """Update metadata from trac-hacks."""
        server = xmlrpclib.ServerProxy(self.rpc_url)
        types = server.trachacks.getTypes()
        if type not in types:
            raise TracError, "Trac-Hacks doesn't know about '%s' hacks" % (type)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        hacks = server.trachacks.getHacks(self.installer.version, type)
        for hack in hacks:
            cursor.execute("SELECT id FROM hacks WHERE name = %s", (hack[0],))
            row = cursor.fetchone()
            if row:        
                cursor.execute("UPDATE hacks SET current = %s WHERE name = %s", (hack[1], hack[0]))
            else:
                cursor.execute("INSERT INTO hacks (name, type, current) VALUES (%s, %s, %s)", (hack[0], type, hack[1]))
        db.commit()                
            
