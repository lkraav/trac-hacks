# -*- coding: utf-8 -*-
"""
A Trac plugin which interfaces with the Jenkins Continuous integration server

You can configure this component via the
[wiki:TracIni#hudson-section "[hudson]"]
section in the trac.ini file.

See also:
 - https://jenkins-ci.org/
 - https://trac-hacks.org/wiki/HudsonTracPlugin
"""

import urllib.request, urllib.error, urllib.parse
import base64
from datetime import datetime
import json

from pkg_resources import resource_filename

from trac.core import *
from trac.config import Option, BoolOption, ListOption, ConfigSection
from trac.perm import IPermissionRequestor
from trac.timeline.api import ITimelineEventProvider
from trac.util.datefmt import datetime_now, format_datetime, \
                              pretty_timedelta, user_time, utc, to_timestamp
from trac.util.html import Markup, tag
from trac.util.text import unicode_quote
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.chrome import add_notice, add_stylesheet, web_context
from trac.wiki.formatter import format_to_oneliner
from trac.util.translation import domain_functions

_, N_, add_domain = domain_functions("hudsontrac", ('_', 'N_', 'add_domain'))

class HudsonTracPlugin(Component):
    """
    Display Jenkins results in the timeline and an entry in the main navigation
    bar.
    """

    implements(INavigationContributor, ITimelineEventProvider,
               ITemplateProvider, IPermissionRequestor)

    hudson_section = ConfigSection('hudson',
               """This section is used to store configurations used by Jenkins Interface ([[https://trac-hacks.org/wiki/HudsonTracPlugin|HudsonTracPlugin]]).""",
               doc_domain='hudsontrac')

    disp_mod = BoolOption('hudson', 'display_modules', 'false',
                          'Display status of modules in the timeline too. ', doc_domain="hudsontrac")
    job_url  = Option('hudson', 'job_url', 'http://localhost/jenkins/',
                      'The url of the top-level Jenkins page if you want to '
                      'display all jobs, or a job or module url (such as '
                      'http://localhost/jenkins/job/build_foo/) if you want '
                      'only display builds from a single job or module. '
                      'This must be an absolute url.', doc_domain="hudsontrac")
    api_path = Option('hudson', 'api_path', 'api/json',
                      'The path part of the API, either "api/python" or "api/json"', doc_domain="hudsontrac")
    interfacename = Option('hudson', 'interfacename', 'Jenkins',
                      'The interfacename (i.e. Jenkins) to use', doc_domain="hudsontrac")
    username = Option('hudson', 'username', '',
                      'The username to use to access Jenkins', doc_domain="hudsontrac")
    password = Option('hudson', 'password', '',
                      'The password to use to access Jenkins - but see also '
                      'the api_token field.', doc_domain="hudsontrac")
    api_token = Option('hudson', 'api_token', '',
                       'The API Token to use to access Jenkins. This takes '
                       'precendence over any password and is the preferred '
                       'mechanism if you are running Jenkins 1.426 or later '
                       'and Jenkins is enforcing authentication (as opposed '
                       'to, for example, a proxy in front of Jenkins).', doc_domain="hudsontrac")
    nav_url  = Option('hudson', 'main_page', '/jenkins/',
                      'The url of the Jenkins main page to which the trac nav '
                      'entry should link; if empty, no entry is created in '
                      'the nav bar. This may be a relative url.', doc_domain="hudsontrac")
    nav_label = Option('hudson', 'nav_label', N_('Builds'),
                      'The label for the nav menu entry (default value will be translated)', doc_domain="hudsontrac")
    tl_label = Option('hudson', 'timeline_opt_label', '%(interfacename)s Builds',
                      'The label for the timeline option to display builds, can contain '
                      '%(interfacename) to be replaced by the interface name option', doc_domain="hudsontrac")
    disp_tab = BoolOption('hudson', 'display_in_new_tab', 'false',
                          'Open Jenkins page in new tab/window', doc_domain="hudsontrac")
    alt_succ = BoolOption('hudson', 'alternate_success_icon', 'false',
                          'Use an alternate success icon (green ball instead '
                          'of blue)', doc_domain="hudsontrac")
    use_desc = BoolOption('hudson', 'display_build_descriptions', 'true',
                          'Whether to display the build descriptions for '
                          'each build instead of the canned "Build finished '
                          'successfully" etc messages.', doc_domain="hudsontrac")
    disp_building = BoolOption('hudson', 'display_building', False,
                               'Also show in-progress builds', doc_domain="hudsontrac")
    list_changesets = BoolOption('hudson', 'list_changesets', False,
                                 'List the changesets for each build', doc_domain="hudsontrac")
    disp_culprit = ListOption('hudson', 'display_culprit', [], doc =
                              'Display the culprit(s) for each build. This is '
                              'a comma-separated list of zero or more of the '
                              'following tokens: `starter`, `author`, '
                              '`authors`, `culprit`, `culprits`. `starter` is '
                              'the user that started the build, if any; '
                              '`author` is the author of the first commit, if '
                              'any; `authors` is the list of authors of all '
                              'commits; `culprit` is the first of what Jenkins '
                              'thinks are the culprits that caused the build; '
                              'and `culprits` is the list of all culprits. If '
                              'given a list, the first non-empty value is used.'
                              ' Example: `starter,authors` (this would show '
                              'who started the build if it was started '
                              'manually, else list the authors of the commits '
                              'that triggered the build if any, else show no '
                              'author for the build).', doc_domain="hudsontrac")

    def __init__(self):
        """Set up translation domain"""
        try:
            locale_dir = resource_filename(__name__, 'locale')
        except KeyError:
            pass
        else:
            add_domain(self.env.path, locale_dir)

        # get base api url
        api_url = unicode_quote(self.job_url, '/%:@')
        if api_url and api_url[-1] != '/':
            api_url += '/'
        api_url += self.api_path

        # set up http authentication
        if self.username and self.api_token:
            handlers = [
                self.HTTPOpenHandlerBasicAuthNoChallenge(self.username,
                                                         self.api_token)
            ]
        elif self.username and self.password:
            pwd_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            pwd_mgr.add_password(None, api_url, self.username, self.password)

            b_auth = urllib.request.HTTPBasicAuthHandler(pwd_mgr)
            d_auth = urllib.request.HTTPDigestAuthHandler(pwd_mgr)

            handlers = [ b_auth, d_auth, self.HudsonFormLoginHandler(self) ]
        else:
            handlers = []

        self.url_opener = urllib.request.build_opener(*handlers)
        if handlers:
            self.env.log.debug("registered auth-handlers for '%s', " \
                               "username='%s'", api_url, self.username)

        # construct tree=... parameter to query for the desired items
        tree = '%(b)s'
        if self.disp_mod:
            tree += ',modules[%(b)s]'
        if '/job/' not in api_url:
            tree = 'jobs[' + tree + ']'

        items = 'builds[building,timestamp,duration,result,description,url,' \
                'fullDisplayName'

        elems = []
        if self.list_changesets:
            elems.append('revision')
            elems.append('id')
        if 'author' in self.disp_culprit or 'authors' in self.disp_culprit:
            elems.append('user')
            elems.append('author[fullName]')
        if elems:
            items += ',changeSet[items[%s]]' % ','.join(elems)

        if 'culprit' in self.disp_culprit or 'culprits' in self.disp_culprit:
            items += ',culprits[fullName]'

        if 'starter' in self.disp_culprit:
            items += ',actions[causes[userName]]'

        items += ']'

        # assemble final url
        tree = tree % {'b': items}
        self.info_url = '%s?tree=%s' % (api_url, tree)

        self.env.log.debug("Build-info url: '%s'", self.info_url)

    def __get_info(self):
        """Retrieve build information from Jenkins"""
        try:
            local_exc = False
            try:
                resp = self.url_opener.open(self.info_url)

                ct   = resp.info().get_content_type()
                mimewantpy = 'text/x-python'
                mimewantjs = 'application/json'
                mimewantjsold = 'application/javascript'
                if ct == mimewantjs or ct == mimewantjsold:
                  return json.loads(resp.read())
                elif ct == mimewantpy:
                  return eval(resp.read(), {"__builtins__":None}, {"True":True, "False":False})
                else:
                    local_exc = True
                    raise IOError(
                        _("Error getting build info from '%(url)s': returned document "
                        "has unexpected type '%(mime)s' (expected '%(mimewantjs)s' or '%(mimewantpy)s'). "
                        "The returned text is:\n%(text)s") %
                        {'url': self.info_url, 'mime': ct, 'mimewantpy': mimewantpy,
                         'mimewantjs': mimewantjs, 'text': resp.read()})
            except Exception as e:
                if local_exc:
                    raise e

                import sys
                self.env.log.exception("Error getting build info from '%s'",
                                       self.info_url)
                raise IOError(
                    _("Error getting build info from '%(url)s': %(name)s: %(info)s. This most "
                    "likely means you configured a wrong job_url, username, "
                    "or password.") % {'url': self.info_url, 'name': sys.exc_info()[0].__name__,
                     'info': str(sys.exc_info()[1])})
        finally:
            self.url_opener.close()

    def __find_all(self, d, paths):
        """Find and return a list of all items with the given paths."""
        if not isinstance(paths, str):
            for path in paths:
                for item in self.__find_all(d, path):
                    yield item
            return

        parts = paths.split('.', 1)
        key = parts[0]
        if key in d:
            if len(parts) > 1:
                for item in self.__find_all(d[key], parts[1]):
                    yield item
            else:
                yield d[key]
        elif not isinstance(d, dict) and not isinstance(d, str):
            for elem in d:
                for item in self.__find_all(elem, paths):
                    yield item

    def __find_first(self, d, paths):
        """Similar to __find_all, but return only the first item or None"""
        l = list(self.__find_all(d, paths))
        return len(l) > 0 and l[0] or None

    def __extract_builds(self, info):
        """Extract individual builds from the info returned by Jenkins.
        What we may get from Jenkins is zero or more of the following:
          {'jobs': [{'modules': [{'builds': [{'building': False, ...
          {'jobs': [{'builds': [{'building': False, ...
          {'modules': [{'builds': [{'building': False, ...
          {'builds': [{'building': False, ...
        """
        p = ['builds', 'modules.builds', 'jobs.builds', 'jobs.modules.builds']
        for arr in self.__find_all(info, p):
            for item in arr:
                yield item

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['BUILD_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'builds'

    def get_navigation_items(self, req):
        if self.nav_url and 'BUILD_VIEW' in req.perm:
            yield ('mainnav', 'builds',
                   tag.a(_(self.nav_label) % {'interfacename': self.interfacename}, href=self.nav_url,
                         target='hudson' if self.disp_tab else None))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('HudsonTrac', resource_filename(__name__, 'htdocs'))]

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if 'BUILD_VIEW' in req.perm:
            yield ('build', self.tl_label % {'interfacename': self.interfacename})

    def __fmt_changeset(self, rev, req):
        ctxt = web_context(req, 'changeset', rev)
        return format_to_oneliner(self.env, ctxt, '[%s]' % rev)

    def get_timeline_events(self, req, start, stop, filters):
        if 'build' not in filters or 'BUILD_VIEW' not in req.perm:
            return

        start = to_timestamp(start)
        stop = to_timestamp(stop)

        add_stylesheet(req, 'HudsonTrac/hudsontrac.css')

        # get and parse the build-info
        try:
            info = self.__get_info()
        except Exception as e:
            add_notice(req, _("Error accessing build status"))
            self.log.warn(repr(e))
            return

        # extract all build entries
        for entry in self.__extract_builds(info):
            # get result, optionally ignoring builds that are still running
            if entry['building']:
                if self.disp_building:
                    result = 'IN-PROGRESS'
                else:
                    continue
            else:
                result = entry['result']

            # get start/stop times
            started = entry['timestamp'] / 1000
            if started < start or started > stop:
                continue

            if result == 'IN-PROGRESS':
                # we hope the clocks are close...
                completed = datetime_now(utc)
            else:
                completed = datetime.fromtimestamp((entry['timestamp'] + entry['duration']) / 1000, utc)

            # get message
            message, kind = {
                'SUCCESS': (_('Build finished successfully'),
                            ('build-successful',
                             'build-successful-alt')[self.alt_succ]),
                'UNSTABLE': (_('Build unstable'), 'build-unstable'),
                'ABORTED': (_('Build aborted'), 'build-aborted'),
                'IN-PROGRESS': (_('Build in progress'),
                                ('build-inprogress',
                                 'build-inprogress-alt')[self.alt_succ]),
                }.get(result, (_('Build failed'), 'build-failed'))

            if self.use_desc:
                message = entry['description'] and entry['description'] or message

            # get changesets
            changesets = ''
            if self.list_changesets:
                paths = ['changeSet.items.revision', 'changeSet.items.id']
                revs  = self.__find_all(entry, paths)
                if revs:
                    revs = [self.__fmt_changeset(r, req) for r in revs]
                    changesets = '<br/>'+_("Changesets:")+' ' + ', '.join(revs)

            # get author(s)
            author = None
            for c in self.disp_culprit:
                author = {
                    'starter':
                        self.__find_first(entry, 'actions.causes.userName'),
                    'author':
                        self.__find_first(entry, ['changeSet.items.user',
                                           'changeSet.items.author.fullName']),
                    'authors':
                        self.__find_all(entry, ['changeSet.items.user',
                                           'changeSet.items.author.fullName']),
                    'culprit':
                        self.__find_first(entry, 'culprits.fullName'),
                    'culprits':
                        self.__find_all(entry, 'culprits.fullName'),
                }.get(c)

                if author and not isinstance(author, str):
                    author = ', '.join(set(author))
                if author:
                    author = author
                    break

            # format response
            if result == 'IN-PROGRESS':
                comment = Markup(_("%(message)s since %(time)s, duration %(duration)s%(changesets)s") % {
                                 'message': message, 'time': user_time(req, format_datetime, started),
                                 'duration': pretty_timedelta(started, completed),
                                 'changesets': changesets})
            else:
                comment = Markup(_("%(message)s at %(time)s, duration %(duration)s%(changesets)s") % {
                                 'message': message, 'time': user_time(req, format_datetime, completed),
                                 'duration': pretty_timedelta(started, completed),
                                 'changesets': changesets})

            href  = entry['url']
            title = _('Build "%(name)s" (%(result)s)') % \
                    {'name': entry['fullDisplayName'], 'result': _(result.lower())}
            # Results: _("success"), _("in-progress"), _("unstable"), _("failure")

            yield kind, completed, author, (href, title, comment)

    def render_timeline_event(self, context, field, event):
        data = event[3]
        if field == 'url':
            return data[0]
        elif field == 'title':
            return data[1]
        elif field == 'description':
            return data[2]

    class HudsonFormLoginHandler(urllib.request.BaseHandler):
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

    class HTTPOpenHandlerBasicAuthNoChallenge(urllib.request.BaseHandler):

        auth_header = 'Authorization'

        def __init__(self, username, password):
            raw = "%s:%s" % (username, password)
            self.auth = 'Basic %s' % base64.b64encode(raw.encode()).decode().strip()

        def default_open(self, req):
            req.add_header(self.auth_header, self.auth)

