#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Florent Xicluna <laxyf@yahoo.fr>


# The service module defines a single class (TracWindowsService) that contains
# the functionality for running Trac as a Windows Service.
# 
# To use this class, users must do the following:
# 1. Download and install the win32all package
#    (http://starship.python.net/crew/mhammond/win32/)
# 2. Edit the constants section with the proper information.
# 3. Open a command prompt and navigate to the directory where this file
#    is located.  Use one of the following commands to
#    install/start/stop/remove the service:
#    > tracservice.py install
#    > tracservice.py start
#    > tracservice.py stop
#    > tracservice.py remove
#    Additionally, typing "tracservice.py" will present the user with all of the
#    available options.
#
# Once installed, the service will be accessible through the Services
# management console just like any other Windows Service.  All service 
# startup exceptions encountered by the TracWindowsService class will be 
# viewable in the Windows event viewer (this is useful for debugging
# service startup errors); all application specific output or exceptions that
# are not captured by the standard Trac logging mechanism should 
# appear in the stdout/stderr logs.
#

import locale
import sys
import os
from distutils import sysconfig

import win32serviceutil
import win32service

from trac.web.standalone import BasicAuthentication as BasicAuth, \
    DigestAuthentication as DigestAuth, TracHTTPServer, \
    AuthenticationMiddleware, BasePathMiddleware, TracEnvironMiddleware

from trac.web.main import dispatch_request

# ==  Editable CONSTANTS SECTION  ============================================

TRAC_PROJECT = 'c:\\path\\to\\Trac\\Projects'

# Trac options (see tracd --help)
#  -a DIGESTAUTH, --auth=DIGESTAUTH
#                        [projectdir],[htdigest_file],[realm]
#  --basic-auth=BASICAUTH
#                        [projectdir],[htpasswd_file],[realm]
#  -p PORT, --port=PORT  the port number to bind to
#  -b HOSTNAME, --hostname=HOSTNAME
#                        the host name or IP address to bind to
#  -e PARENTDIR, --env-parent-dir=PARENTDIR
#                        parent directory of the project environments
#  --base-path=BASE_PATH
#                        the initial portion of the request URL's "path"
#  -s, --single-env      only serve a single project without the project list
OPTS = [
    ('--hostname', 'mycomputer.mydomain.com'),
    ('--single-env', True),
    ('--auth', ('trac,c:\\path\\to\\pswd\\file,TracRealm')),
    ('--port', '80'),
]

# ==  End of CONSTANTS SECTION  ==============================================

# Other constants
PYTHONDIR = sysconfig.get_python_lib()  # gets site-packages folder
PYTHONSERVICE_EXE=os.path.join(PYTHONDIR, 'win32', 'pythonservice.exe')
LOG_DIR = os.path.join(TRAC_PROJECT, log)

# Trac instance(s)
ARGS = [TRAC_PROJECT]

def add_auth(auths, vals, cls):
    info = vals.split(',', 3)
    p, h, r = info
    if auths.has_key(p):
        print >>sys.stderr, 'Ignoring duplicate authentication option for ' \
                            'project: %s' % p
    else:
        auths[p] = cls(h, r)

class TracWindowsService(win32serviceutil.ServiceFramework):
    """Trac Windows Service helper class.

    The TracWindowsService class contains all the functionality required
    for running Trac application as a Windows Service.

    For information on installing the application, please refer to the
    documentation at the end of this module or navigate to the directory
    where this module is located and type "tracservice.py" from the command
    prompt.
    """

    _svc_name_ = 'Trac_%s' % str(hash(TRAC_PROJECT))
    _svc_display_name_ = 'Trac instance at %s' % TRAC_PROJECT
    _exe_name_ = PYTHONSERVICE_EXE

    def SvcDoRun(self):
        """ Called when the Windows Service runs. """

        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.httpd = self.trac_init()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        try:
            self.httpd.serve_forever()
        except OSError:
            sys.exit(1)

    def SvcStop(self):
        """Called when Windows receives a service stop request."""

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.httpd:
            self.httpd.server_close()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def trac_init(self):
        """ Checks for the required data and initializes the application. """

        locale.setlocale(locale.LC_ALL, '')
        port = 80
        hostname = ''
        auths = {}
        env_parent_dir = None

        for o, a in OPTS:
            if o in ("-a", "--auth"):
                add_auth(auths, a, DigestAuth)
            if o == '--basic-auth':
                add_auth(auths, a, BasicAuth)
            if o in ("-p", "--port"):
                port = int(a)
            elif o in ("-b", "--hostname"):
                hostname = a
            if o in ("-e", "--env-parent-dir"):
                env_parent_dir = a
            if o in ("-s", "--single-env"):
                single_env = a
            if o in ("--base-path"):
                base_path = a

        if not env_parent_dir and not ARGS:
            raise ValueError("""No Trac project specified""")

        wsgi_app = TracEnvironMiddleware(dispatch_request,
                                         env_parent_dir, ARGS,
                                         single_env)
        if auths:
            if single_env:
                project_name = os.path.basename(ARGS[0])
                wsgi_app = AuthenticationMiddleware(wsgi_app, auths, project_name)
            else:
                wsgi_app = AuthenticationMiddleware(wsgi_app, auths)
        base_path = base_path.strip('/').strip('\\')
        if base_path:
            wsgi_app = BasePathMiddleware(wsgi_app, base_path)

        sys.stdout = open(os.path.join(LOG_DIR, 'stdout.log'),'a')
        sys.stderr = open(os.path.join(LOG_DIR, 'stderr.log'),'a')

        server_address = (hostname, port)
        return TracHTTPServer(server_address, wsgi_app, env_parent_dir, ARGS)

if __name__ == '__main__':
    # The following are the most common command-line arguments that are used
    # with this module:
    #  tracservice.py install (Installs the service with manual startup)
    #  tracservice.py --startup auto install (Installs the service with auto startup)    
    #  tracservice.py start (Starts the service)
    #  tracservice.py stop (Stops the service)
    #  tracservice.py remove (Removes the service)
    #
    # For a full list of arguments, simply type "tracservice.py".
    win32serviceutil.HandleCommandLine(TracWindowsService)
