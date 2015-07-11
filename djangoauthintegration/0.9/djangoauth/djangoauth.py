# DjangoAuth plugin

# Copyright (c) 2007, Waylan Limberg <waylan@gmail.com>

from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.web.main import IAuthenticator, IRequestHandler
from trac.perm import IPermissionGroupProvider
from trac.util import escape, Markup
import os
import datetime

class DjangoAuthPlugin(Component):
    implements(IAuthenticator, IPermissionGroupProvider, \
               INavigationContributor, IRequestHandler)

    # IAuthenticator methods
    def authenticate(self, req):
        authname = None
        if req.remote_user and (req.remote_user != "anonymous"):
            authname = req.remote_user
        elif req.incookie.has_key('sessionid'):
            authname = self._get_name_from_django(req, req.incookie['sessionid'])
        else:
            authname = req.remote_user

        if authname and self.config.getbool('trac', 'ignore_auth_case'):
            authname = authname.lower()

        return authname

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'login'

    def get_navigation_items(self, req):
        if req.authname and req.authname != 'anonymous':
            yield 'metanav', 'login', 'logged in as "%s"' % req.authname
            yield 'metanav', 'logout', Markup('<a href="%s">Log-out</a>',
                    self.config.get('djangoauth', 'logout_url', '#'))
        else:
            yield 'metanav', 'login', Markup('<a href="%s">Log-in</a>',
                    self.config.get('djangoauth', 'login_url', '#'))

    # private methods
    def _get_name_from_django(self, req, sessionid):
        settings = self.config.get('djangoauth', 'django_settings_module')
        os.environ['DJANGO_SETTINGS_MODULE'] = settings
        from django.contrib.sessions.models import Session
        from django.contrib.auth.models import User
        #req.django_sess = 'value is '+sessionid.value
        try:
            session = Session.objects.get(pk=sessionid.value)
        except Session.DoesNotExist:
            pass
        else:
     
            # Check for stale session
            if session.expire_date > datetime.datetime.now():
                data = session.get_decoded()

                if data.has_key('_auth_user_id'):
                    try:
                        user = User.objects.get(pk=data['_auth_user_id'])
                    except User.DoesNotExist:
                        return None

                    # Check user perms
                    if user.is_active:

                        if self.config.getbool('djangoauth', 'use_django_perms'):
                            # make user object available for perm checks later
                            self.user = user

                        # Update session expire_date
                        # session.expire_date = datetime.datetime.now()
                        # session.save() # OperationalError: readonly db??

                    return user.username
        return None
 
    # IPermissionGroupProvider methods
    def get_permission_groups(self, username):
        if hasattr(self, 'user') and self.user.username == username:
            groups = self.user.groups.filter(name__startswith='trac_')
            return [g.name[5:] for g in groups]
        else:
            return []

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/dj'

    def process_request(self, req):
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.end_headers()
        req.write('DjangoAuth is enabled!\n')
        req.write(str(dir(req))+ '\n')
        req.write('incookie: ' + str(req.incookie) + '\n')
        req.write('outcookie: ' + str(req.outcookie) + '\n')
        try:
            req.write('perm: ' + str((req.perm.permissions(),req.perm.perms)) + '\n')
        except AttributeError:
            pass
        req.write('remote_user: ' + str(req.remote_user) + '\n')
        req.write('server_name: ' + str(req.server_name) + '\n')
        req.write('session: ' + str(req.session) + '\n')
        if req.django_sess:
            req.write('django-sess: ' + str(req.django_sess) + '\n') 
        if req.authname:
            req.write('authname: ' + str(req.authname) + '\n') 
