# -*- coding: utf-8 -*-
"""
A Trac plugin which interfaces with the Hudson Continuous integration server

You can configure this component via the
[wiki:TracIni#hudson-section "[hudson]"]
section in the trac.ini file.

See also:
 - http://hudson-ci.org/
 - http://wiki.hudson-ci.org/display/HUDSON/Trac+Plugin
"""

import time
import urllib2
import base64
from xml.dom import minidom
from datetime import datetime
from trac.core import *
from trac.config import Option, BoolOption
from trac.perm import IPermissionRequestor
from trac.util import Markup, format_datetime, pretty_timedelta
from trac.util.text import unicode_quote
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.chrome import add_stylesheet
try:
    from trac.timeline.api import ITimelineEventProvider
except ImportError:
    from trac.Timeline import ITimelineEventProvider

class HudsonTracPlugin(Component):
    """
    Display Hudson results in the timeline and an entry in the main navigation
    bar.
    """

    implements(INavigationContributor, ITimelineEventProvider,
               ITemplateProvider, IPermissionRequestor)

    disp_mod = BoolOption('hudson', 'display_modules', 'false',
                          'Display status of modules in the timeline too. '
                          'Note: enabling this may slow down the timeline '
                          'retrieval significantly')
    job_url  = Option('hudson', 'job_url', 'http://localhost/hudson/',
                      'The url of the top-level hudson page if you want to '
                      'display all jobs, or a job or module url (such as '
                      'http://localhost/hudson/job/build_foo/) if you want '
                      'only display builds from a single job or module. '
                      'This must be an absolute url.')
    username = Option('hudson', 'username', '',
                      'The username to use to access hudson')
    password = Option('hudson', 'password', '',
                      'The password to use to access hudson')
    nav_url  = Option('hudson', 'main_page', '/hudson/',
                      'The url of the hudson main page to which the trac nav '
                      'entry should link; if empty, no entry is created in '
                      'the nav bar. This may be a relative url.')
    disp_tab = BoolOption('hudson', 'display_in_new_tab', 'false',
                          'Open hudson page in new tab/window')
    alt_succ = BoolOption('hudson', 'alternate_success_icon', 'false',
                          'Use an alternate success icon (green ball instead '
                          'of blue)')
    use_desc = BoolOption('hudson', 'display_build_descriptions', 'true',
                          'Whether to display the build descriptions for '
                          'each build instead of the canned "Build finished '
                          'successfully" etc messages.')

    def __init__(self):
        api_url = unicode_quote(self.job_url, '/%:@')
        if api_url and api_url[-1] != '/':
            api_url += '/'
        api_url += 'api/xml'

        pwd_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pwd_mgr.add_password(None, api_url, self.username, self.password)

        b_auth = urllib2.HTTPBasicAuthHandler(pwd_mgr)
        d_auth = urllib2.HTTPDigestAuthHandler(pwd_mgr)

        self.url_opener = urllib2.build_opener(b_auth, d_auth,
                                            self.HudsonFormLoginHandler(self))

        self.env.log.debug("registered auth-handler for '%s', username='%s'",
                           api_url, self.username)

        if '/job/' in api_url:
            path = '/*/build[timestamp>=%(start)s][timestamp<=%(stop)s]'
            depth = 1
            if self.disp_mod:
                path  += ('|/*/module/build'
                          '[timestamp>=%(start)s][timestamp<=%(stop)s]')
                depth += 1
        else:
            path = '/*/job/build[timestamp>=%(start)s][timestamp<=%(stop)s]'
            depth = 2
            if self.disp_mod:
                path  += ('|/*/job/module/build'
                          '[timestamp>=%(start)s][timestamp<=%(stop)s]')
                depth += 1

        self.info_url = ('%s?xpath=%s&depth=%s&'
                         'exclude=//action|//artifact|//changeSet|//culprit&'
                         'wrapper=builds' %
                         (api_url.replace('%', '%%'), path, depth))

        self.env.log.debug("Build-info url: '%s'", self.info_url)

    # IPermissionRequestor methods  

    def get_permission_actions(self):
        return ['BUILD_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'builds'

    def get_navigation_items(self, req):
        if self.nav_url and req.perm.has_permission('BUILD_VIEW'):
            yield 'mainnav', 'builds', Markup('<a href="%s"%s>Builds</a>' % \
                    (self.nav_url, self.disp_tab and ' target="hudson"' or ''))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [self.env.get_templates_dir(),
                self.config.get('trac', 'templates_dir')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('HudsonTrac', resource_filename(__name__, 'htdocs'))]

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if req.perm.has_permission('BUILD_VIEW'):
            yield ('build', 'Hudson Builds')

    def get_timeline_events(self, req, start, stop, filters):
        if 'build' not in filters or not req.perm.has_permission('BUILD_VIEW'):
            return

        # xml parsing helpers
        def _get_text(node):
            rc = ""
            for node in node.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc += node.data
            return rc

        def _get_string(parent, child):
            nodes = parent.getElementsByTagName(child)
            return nodes and _get_text(nodes[0]).strip() or ''

        def _get_number(parent, child):
            num = _get_string(parent, child)
            return num and int(num) or 0

        # Support both Trac 0.10 and 0.11
        if isinstance(start, datetime): # Trac>=0.11
            from trac.util.datefmt import to_timestamp
            start = to_timestamp(start)
            stop = to_timestamp(stop)

        add_stylesheet(req, 'HudsonTrac/hudsontrac.css')

        # get and parse the build-info
        url = self.info_url % {'start': int(start*1000), 'stop': int(stop*1000)}
        try:
            try:
                info = minidom.parse(self.url_opener.open(url))
            except Exception:
                import sys
                self.env.log.exception("Error getting build info from '%s'",
                                       url)
                raise IOError(
                    "Error getting build info from '%s': %s: %s. This most "
                    "likely means you configured a wrong job_url, username, "
                    "or password." %
                    (url, sys.exc_info()[0].__name__, str(sys.exc_info()[1])))
        finally:
            self.url_opener.close()

        if info.documentElement.nodeName != 'builds':
            raise IOError(
                "Error getting build info from '%s': returned document has "
                "unexpected node '%s'. This most likely means you configured "
                "a wrong job_url." %
                (self.info_url, info.documentElement.nodeName))

        # extract all build entries
        for entry in info.documentElement.getElementsByTagName("build"):
            # ignore builds that are still running
            if _get_string(entry, 'building') == 'true':
                continue

            # create timeline entry
            started   = _get_number(entry, 'timestamp')
            completed = started + _get_number(entry, 'duration')
            started   /= 1000
            completed /= 1000

            result = _get_string(entry, 'result')
            message, kind = {
                'SUCCESS': ('Build finished successfully',
                            ('build-successful',
                             'build-successful-alt')[self.alt_succ]),
                'UNSTABLE': ('Build unstable', 'build-unstable'),
                'ABORTED': ('Build aborted', 'build-aborted'),
                }.get(result, ('Build failed', 'build-failed'))

            if self.use_desc:
                message = _get_string(entry, 'description') or message

            comment = "%s at %s, duration %s" % (
                          message, format_datetime(completed),
                          pretty_timedelta(started, completed))

            href  = _get_string(entry, 'url')
            title = 'Build "%s" (%s)' % \
                        (_get_string(entry, 'fullDisplayName'), result.lower())

            yield kind, href, title, completed, None, comment

    class HudsonFormLoginHandler(urllib2.BaseHandler):
        def __init__(self, parent):
            self.p = parent

        def http_error_403(self, req, fp, code, msg, headers):
            for h in self.p.url_opener.handlers:
                if isinstance(h, self.p.HTTPOpenHandlerBasicAuthNoChallenge):
                    return

            self.p.url_opener.add_handler(
                self.p.HTTPOpenHandlerBasicAuthNoChallenge(self.p.username,
                                                           self.p.password))
            self.p.env.log.debug(
                "registered auth-handler for form-based authentication")

            fp.close()
            return self.p.url_opener.open(req)

    class HTTPOpenHandlerBasicAuthNoChallenge(urllib2.BaseHandler):

        auth_header = 'Authorization'

        def __init__(self, username, password):
            raw = "%s:%s" % (username, password)
            self.auth = 'Basic %s' % base64.b64encode(raw).strip()

        def default_open(self, req):
            req.add_header(self.auth_header, self.auth)

