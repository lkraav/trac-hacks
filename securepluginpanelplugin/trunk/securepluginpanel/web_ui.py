# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009 Edgewall Software
# Copyright (C) 2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2009 Sebastian Krysmanski
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/.
#
# Author: Jonas Borgström <jonas@edgewall.com>
# Partially rewritten by: Sebastian Krysmanski

import inspect
import os
import pkg_resources
import re
import shutil
import sys

from genshi import HTML
from genshi.builder import tag

from trac import __version__ as TRAC_VERSION
from trac.admin.api import IAdminPanelProvider
from trac.core import *
from trac.perm import PermissionSystem, IPermissionRequestor
from trac.util import get_pkginfo, get_module_path
from trac.util.compat import partial
from trac.util.text import exception_to_unicode, to_unicode
from trac.util.translation import _
from trac.web import HTTPNotFound, IRequestHandler
from trac.web.chrome import add_notice, add_script, add_stylesheet, \
                            add_warning, Chrome, INavigationContributor, \
                            ITemplateProvider

#
# This is a copy of "trac.admin.web_ui._save_config".
# Version: 0.11.5
#
# NOTE: We can't use the function from "trac.admin.web_ui" directly as it has 
#   been added firstly in Trac 0.11.5. So to keep this plugin compatible with
#   Trac 0.11.0 - 0.11.4 we keep a copy here.
#
def _save_config(config, req, log):
    """Try to save the config, and display either a success notice or a
    failure warning.
    """
    try:
        config.save()
        add_notice(req, _('Your changes have been saved.'))
    except Exception, e:
        log.error('Error writing to trac.ini: %s', exception_to_unicode(e))
        add_warning(req, _('Error writing to trac.ini, make sure it is '
                           'writable by the web server. Your changes have '
                           'not been saved.'))
                            
#
# This is basically a copy of "trac.admin.web_ui.PluginAdminPanel".
# Version: 0.11.5
#
class SecurePluginPanel(Component):
    """Provides the secure mode plugin panel."""

    implements(IAdminPanelProvider, ITemplateProvider)

    # Base components that must not be disabled (and therefore are readonly)
    readonly_components = ['trac.about.AboutModule', 
                           'trac.perm.DefaultPermissionGroupProvider',
                           'trac.env.Environment', 
                           'trac.env.EnvironmentSetup', 
                           'trac.perm.PermissionSystem',
                           'trac.web.main.RequestDispatcher', 
                           'trac.mimeview.api.Mimeview', 
                           'trac.web.chrome.Chrome',
                           'trac.admin.web_ui.AdminModule']
                           
    simplified_name_regexp = re.compile(r"^(?:Trac(?=[^a-z0-9]))?(.+)$")

    def __init__(self):
        self.trac_path = get_module_path(sys.modules['trac.core'])
        # Add us to readonly list as we usually don't want the user to disable 
        # the plugin. Also we disable the original plugin panel.
        # NOTE: We don't prepend the module for these two as it would be a great
        #   security risk if their modules were renamed so that they were not
        #   be disabled anymore.
        self.readonly_components.append('SecurePluginPanel')
        self.readonly_components.append('PluginAdminPanel')
        
        # Load additional readonly components from the trac.ini
        self.readonly_components.extend(self.config.getlist('trac', 'readonly_components'))

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('general', _('General'), 'secureplugin', _('Plugins (MTP mode)'))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TRAC_ADMIN')

        if req.method == 'POST':
            self._do_update(req)
            anchor = ''
            if req.args.has_key('plugin'):
                anchor = '#no%d' % (int(req.args.get('plugin')) + 1)
            req.redirect(req.href.admin(cat, page) + anchor)

        return self._render_view(req)

    # ITemplateProvider methods
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('securepluginpanel', resource_filename(__name__, 'htdocs'))]
        
    # Internal methods

    def _do_update(self, req):
        """Update component enablement."""
        components = req.args.getlist('component')
        enabled = req.args.getlist('enable')
        changes = False

        # FIXME: this needs to be more intelligent and minimize multiple
        # component names to prefix rules

        for component in components:
            is_enabled = self.env.is_component_enabled(component)
            if is_enabled != (component in enabled):
                # Check whether the state of this component is "readonly"
                if ((component in self.readonly_components) or 
                   (component.rsplit('.', 2)[-1] in self.readonly_components)):
                    raise Exception, 'Tried to dis-/enable readonly component'
                    
                self.config.set('components', component,
                                is_enabled and 'disabled' or 'enabled')
                self.log.info('%sabling component %s',
                              is_enabled and 'Dis' or 'En', component)
                changes = True

        if changes:
            _save_config(self.config, req, self.log)

    def _render_view(self, req):
        plugins = {}
        plugins_dir = os.path.realpath(os.path.join(self.env.path, 'plugins'))
        plugins_dir = os.path.normcase(plugins_dir) # needs to match loader.py

        from trac.core import ComponentMeta
        for component in ComponentMeta._components:
            module = sys.modules[component.__module__]

            dist = self._find_distribution(module)
            plugin_filename = None
            if os.path.realpath(os.path.dirname(dist.location)) == plugins_dir:
                plugin_filename = os.path.basename(dist.location)

            description = inspect.getdoc(component)
            if description:
                description = to_unicode(description).split('.', 1)[0] + '.'

            if dist.project_name not in plugins:
                #
                # retrieve plugin metadata
                #
                info = get_pkginfo(dist)
                if not info:
                    # no info found; construct from module, if possible
                    info = {'summary': description}
                    for k in ('author author_email home_page url license trac'
                              .split()):
                        v = getattr(module, k, '')
                        if v:
                            if k == 'home_page' or k == 'url':
                                k = 'home_page'
                                v = v.replace('$', '').replace('URL: ', '')
                            if k == 'author':
                                v = to_unicode(v)
                            
                            info[k] = v
                else:
                    # Info found; set all those fields to "None" that have the 
                    # value "UNKNOWN" as this is value for fields that aren't
                    # specified within "setup.py"
                    for k in info:
                        if info[k] == 'UNKNOWN':
                            info[k] = None
                        elif k == 'author':
                            # Must be encoded as unicode as otherwise Genshi 
                            # may raise a "UnicodeDecodeError".
                            info[k] = to_unicode(info[k])

                # retrieve plugin version info
                version = dist.version
                if not version:
                    version = (getattr(module, 'version', '') or
                               getattr(module, 'revision', ''))
                    # special handling for "$Rev$" strings
                    version = version.replace('$', '').replace('Rev: ', 'r') 
                
                # Simplify name
                simplified_name = dist.project_name
                matcher = self.simplified_name_regexp.match(simplified_name)
                if matcher:
                  simplified_name = matcher.group(1)
                if simplified_name.endswith('Plugin'):
                  simplified_name = simplified_name[0:-6]
                  name_postfix = 'Plugin'
                elif simplified_name.endswith('Macro'):
                  simplified_name = simplified_name[0:-5]
                  name_postfix = 'Macro'
                else:
                  name_postfix = None
                
                plugins[dist.project_name] = {
                    'name': simplified_name, 'version': version,
                    'path': dist.location, 'description': description,
                    'plugin_filename': plugin_filename,
                    'info': info, 'components': [], 'compcount': 0,
                    'compenabledcount': 0,
                    'full_name': dist.project_name != simplified_name and dist.project_name or None,
                    'name_postfix': name_postfix
                }
            plugins[dist.project_name]['components'].append({
                'name': component.__name__, 'module': module.__name__,
                'description': description,
                'enabled': self.env.is_component_enabled(component),
                'readonly': ((module.__name__ + '.' + component.__name__) in self.readonly_components) or
                            (component.__name__ in self.readonly_components),
            })
            # Add some information about counts
            plugins[dist.project_name]['compcount'] += 1
            if self.env.is_component_enabled(component):
                plugins[dist.project_name]['compenabledcount'] += 1

        def component_order(a, b):
            # CHANGE: Sort components by name - not by module.
            return cmp(a['name'].lower(), b['name'].lower())
        
        # Sort components
        for category in plugins:
            plugins[category]['components'].sort(component_order)

        plugin_list = [plugins['Trac']]
        addons = [(key, plugins[key]['name']) for key in plugins.keys() if key != 'Trac']
        addons.sort(cmp=lambda x,y: cmp(x[1].lower(), y[1].lower()))
        plugin_list += [plugins[category[0]] for category in addons]

        data = {
            'plugins': plugin_list,
            'readonly': not os.access(plugins_dir, os.F_OK + os.W_OK)
        }
        return 'securepluginpanel.html', data

    def _find_distribution(self, module):
        path = get_module_path(module)
        if path == self.trac_path:
            return pkg_resources.Distribution(project_name='Trac',
                                              version=TRAC_VERSION,
                                              location=path)
        for dist in pkg_resources.find_distributions(path, only=True):
            return dist
        else:
            # This is a plain Python source file, not an egg
            return pkg_resources.Distribution(project_name=module.__name__,
                                              version='',
                                              location=module.__file__)
