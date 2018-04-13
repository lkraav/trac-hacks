# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# ==============================================================================

from trac.admin import IAdminPanelProvider
from trac.config import Option, _TRUE_VALUES
from trac.core import Component, implements
from trac.web.chrome import add_stylesheet

class AdsenseAdmin(Component):
    config = env = log = None # make pylint happy
    implements(IAdminPanelProvider)

    def __init__(self):
        self.options = {}

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('google', 'Google', 'search', 'Search')

    def render_admin_panel(self, req, cat, page, path_info):
        add_stylesheet(req, 'googlesearch/googlesearch.css')
        if req.method == 'POST':
            self.config.set('google.search', 'google_search_active',
                            req.args.get('google_search_active') in
                            _TRUE_VALUES)

            for arg, value in req.args.iteritems():
                if self.config.has_option('google.search', arg):
                    if arg != 'google_search_active':
                        self.config.set('google.search', arg, value)
            self.config.save()
            req.redirect(req.href.admin(cat, page))

        self._update_config()
        return 'google_search_admin.html', {'ads_options': self.options}

    # Internal methods
    def _update_config(self):
        for option in [option for option in Option.registry.values()
                       if option.section == 'google.search']:
            if option.name in ('hide_for_authenticated',
                               'google_search_active'):
                option.value = self.config.getbool('google.search', option.name,
                                                   True)
            elif option.name == 'search_iframe_initial_width':
                option.value = self.config.getint('google.search', option.name,
                                                  option.default)
            else:
                # String options
                option.value = self.config.get('google.search', option.name,
                                               option.default)
            self.options[option.name] = option
