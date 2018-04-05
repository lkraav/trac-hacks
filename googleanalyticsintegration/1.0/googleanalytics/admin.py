# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# ==============================================================================

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.util import as_bool
from trac.web.chrome import add_stylesheet


class GoogleAnalyticsAdmin(Component):

    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield 'google', 'Google', 'analytics', 'Analytics'

    def render_admin_panel(self, req, cat, page, path_info):
        if req.method.lower() == 'post':
            self.config.set('google.analytics', 'uid',
                            req.args.get('uid'))
            self.config.set('google.analytics', 'admin_logging',
                            as_bool(req.args.get('admin_logging')))
            self.config.set('google.analytics', 'authenticated_logging',
                            as_bool(req.args.get('authenticated_logging')))
            self.config.set('google.analytics', 'outbound_link_tracking',
                            as_bool(req.args.get('outbound_link_tracking')))
            self.config.set('google.analytics', 'google_external_path',
                            req.args.get('google_external_path'))
            self.config.set('google.analytics', 'extensions',
                            req.args.get('extensions'))
            self.config.set('google.analytics', 'tracking_domain_name',
                            req.args.get('tracking_domain_name'))
            self.config.save()
            req.redirect(req.href.admin('google/analytics'))

        add_stylesheet(req, 'googleanalytics/googleanalytics.css')
        ga = self.config['google.analytics']
        return 'google_analytics_admin.html', {
            'admin_logging': ga.getbool('admin_logging'),
            'authenticated_logging': ga.getbool('authenticated_logging'),
            'extensions': ga.get('extensions'),
            'google_external_path': ga.get('google_external_path'),
            'outbound_link_tracking': ga.getbool('outbound_link_tracking'),
            'tracking_domain_name': ga.get('tracking_domain_name'),
            'uid': ga.get('uid'),
        }
