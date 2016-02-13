# -*- coding: utf-8 -*-

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.web.chrome import add_warning

from dbBackend import dbBackend
from model import get_threshold, set_threshold

__author__ = 'Cinc'


class MgrOptionsAdminPlugin(Component):
    """Set threshold percentage"""
    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'CODE_REVIEW_MGR' in req.perm:
            yield ('codereview', 'Code review', 'threshold', 'Threshold')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('CODE_REVIEW_MGR')

        db = self.env.get_read_db()
        dbBack = dbBackend(db)

        if req.method=='POST':
            percentage = req.args.get('percentage', '')
            if not percentage:
                add_warning(req, u"You must specify a  percentage between 0 and 100.")
                req.redirect(req.href.admin(cat, page))
            elif int(percentage) < 0 or int(percentage) > 100:
                add_warning(req, u"You must specify a  percentage between 0 and 100.")
                req.redirect(req.href.admin(cat, page))
            else:
                req.redirect(req.href.admin(cat, page))

        data = {'percentage': get_threshold(self.env)}

        return 'admin_mgr_options.html', data