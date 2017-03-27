# -*- coding: iso-8859-1 -*-
#
# Copyright 2008 Optaros, Inc.
#

from trac.core import Component, implements
from trac.prefs.api import IPreferencePanelProvider
from trac.util.translation import _
from trac.web.chrome import add_stylesheet

from tracusermanager.profile.api import UserProfileManager
from tracusermanager.api import UserManager


class UserProfileModule(Component):

    implements(IPreferencePanelProvider)

    # IPreferencePanelProvider methods

    def get_preference_panels(self, req):
        if req.session.authenticated:
            yield 'userprofile', _("My Profile")

    def render_preference_panel(self, req, panel):
        user = UserManager(self.env).get_user(req.session.sid)
        data = dict(messages=[], errors=[],
                    user=user,
                    um_profile_fields=UserProfileManager(self.env)
                    .get_user_profile_fields(ignore_internal=True))

        if req.method == "POST":
            if 'um_profile_picture_remove' in req.args:
                if UserProfileManager(self.env)\
                        .remove_user_file(user['picture_href']):
                    del user["picture_href"]
                    if user.save():
                        data['messages'].append(
                            _("Successfully removed %(user)s's picture.",
                              user=user.username))
                        req.redirect(req.href.prefs('userprofile'))
                        return

            for field in data['um_profile_fields'].keys():
                if 'um_profile_%s' % field in req.args:
                    if data['um_profile_fields'][field]['type'] == 'file':
                        user_file_new = UserProfileManager(self.env)\
                            .get_uploaded_file_href(req, user, field,
                                                    'um_profile_%s' % field)
                        user_file_old = user[field]
                        if user_file_new != user_file_old:
                            user[field] = user_file_new
                            if user_file_old:
                                try:
                                    UserProfileManager(self.env)\
                                        .remove_user_file(user_file_old)
                                except Exception, e:
                                    self.log.error(e)
                                    data['errors'].append(
                                        _("Unable to remove previous "
                                          "%(field)s=%(file)s", field=field,
                                          file=user_file_old))
                    elif data['um_profile_fields'][field]['type'] == \
                            'multichecks':
                        user[field] = '|'.join(
                            req.args.getlist('um_profile_%s' % field))
                    else:
                        user[field] = req.args.get('um_profile_%s' % field)
                elif data['um_profile_fields'][field]['type'] == \
                        'multichecks':
                    # cleanup if none selected
                    user[field] = ''

            if user.save():
                data['messages'].append(
                    _("Successfully updated profile for user %(user)s.",
                      user=user.username))
                req.redirect(req.href.prefs('userprofile'))

        add_stylesheet(req, 'tracusermanager/css/prefs_um_profile.css')

        return 'prefs_um_profile.html', data
