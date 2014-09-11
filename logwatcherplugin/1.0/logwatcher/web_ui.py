# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Andreas Itzchak Rehberg <izzysoft@qumran.org>
# Copyright (C) 2014 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.util.translation import _

from logwatcher.api import LogViewerApi
from pkg_resources import resource_filename  # @UnresolvedImport
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.core import Component, implements
from trac.config import BoolOption, Option, ListOption


class LogViewerPage(Component):

    implements(IAdminPanelProvider, ITemplateProvider, IPermissionRequestor)

    def __init__(self):
        self.api = LogViewerApi(self.env)

#   Configuration options
    _autoload = BoolOption('logwatcher', 'autoload', 'false',
                           doc='Whether the log file content should be automatically loaded when'
                           ' the module is called, i.e. even before the form was submitted.'
                           ' This is a boolean option (true/false), and defaults to false.')
    _autolevel = Option('logwatcher', 'autolevel', '3',
                        doc='Which log level shall be used on autoload (only applies when'
                        ' autoload is enabled). This integer value defaults to 3 (warnings).'
                        ' Possible values: 1=critical, 2=error, 3=warning, 4=info, 5=debug')
    _autoup = BoolOption('logwatcher', 'autoup', 'true',
                         doc='Include log events of higher levels than autolevel on autoload?'
                         ' This boolean option defaults to true - and only applies on autoload')
    _autotail = Option('logwatcher', 'autotail', '1000',
                       doc='Only applies to autoload: Restrict the evaluated lines to the last N'
                       ' lines. Defaults to 1000.')
    _defaultlevel = Option('logwatcher', 'defaultlevel', '0',
                           doc='Preset for the log level dropdown (if autoload is disabled). This'
                           ' integer value defaults to 3 (warnings). Possible values:'
                           ' 1=critical, 2=error, 3=warning, 4=info, 5=debug')
    _defaultup = BoolOption('logwatcher', 'defaultup', 'true',
                            doc='Check the box to include log events of higher levels when autoload'
                            ' is disabled? This boolean option defaults to true.')
    _defaulttail = Option('logwatcher', 'defaulttail', '100',
                          doc='Preset for the Tail input (restrict query to the last N lines of the'
                          ' logfile to load). This must be a number (integer), and by default is'
                          ' empty (not set)')
    _defaultextlines = Option('logwatcher,', 'defaultextlines', '0')
    _log_destinations = ListOption('logwatcher', 'log_destinations',
                                   doc="List of directories or files in which log file resides")
    _log_levels = ListOption('logwatcher', 'log_level_names',
                             doc="List of log level names for destinations. Available log names are: TracLog, TomcatLog")

    # IPermissionRequestor
    def get_permission_actions(self):
        yield ("LOG_WATCHER_VIEW")

    def checkPermissions(self, req):
        for permission in ("TRAC_ADMIN", "LOG_WATCHER_VIEW"):
            if permission in PermissionSystem(self.env).get_user_permissions(
                    req.authname):
                return True
        return False

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN') \
                or req.perm.has_permission("LOG_WATCHER_VIEW"):
            yield ('general', _('General'), 'logwatcher', 'Log Viewer')

    def render_admin_panel(self, req, cat, page, path_info):
        # here comes the page content, handling, etc.
        if req.args and 'log_file' in req.args.keys():
            logfile = req.args['log_file']
        else:
            logfile = None

        sort_by = 2
        if req.args and 'sort_by' in req.args.keys():
            sort_by = int(req.args['sort_by'])

        self.data = {}
        self.data['err'] = []
        self.data['msg'] = []
        self.data['log'] = []
        data = {}
        data['log_file'] = logfile
        data['sort_by'] = sort_by
        html_template = 'logviewer.html'

        autoload = self.env.config.getbool('logwatcher', 'autoload') or False
        try:
            log_list = self.api.get_logfile_names(
                self._log_destinations, self._log_levels, sort_by)
            if log_list and not logfile:
                data['log_list'] = log_list
                print "got log_list %s" % data['log_list']
                html_template = 'logfiles.html'
            elif not logfile:
                logfile = self.api.get_logfile_name()
                if not logfile:
                    self.env.log.debug('No log file configured.')
                    self.data['err'].append(
                        'There is no log file configured for this environment.'
                    )
        except IOError:
            self.env.log.debug(
                'Got IOError - configured log file does not exist!')
            self.data['err'].append('The configured log file does not exist.')

        # OK to process?
        if logfile or log_list:
            params = {}
            if logfile:
                data['log_file'] = logfile
            if log_list:
                data['has_log_list'] = 1
#          if req.method == "POST":
            if not autoload:
                params['extlines'] = req.args.get('extlines')
                params['level'] = req.args.get('level') or self._defaultlevel
                params['up'] = req.args.get('up')
                params['invert'] = req.args.get('invertsearch')
                params['regexp'] = req.args.get('regexp')
                params['tail'] = int(req.args.get('tail') or self._defaulttail)
                params['filter'] = req.args.get('filter')
                if logfile:
                    self._do_process(params, logfile)
                data['extlines'] = int(
                    req.args.get('extlines')or self._defaultextlines)
                data['level'] = int(
                    req.args.get('level') or self._defaultlevel)
                data['up'] = int(req.args.get('up') or 0)
                data['invert'] = int(req.args.get('invertsearch') or 0)
                data['regexp'] = int(req.args.get('regexp') or 0)
                data['filter'] = req.args.get('filter') or ''
                data['tail'] = req.args.get('tail') or self._defaulttail
            elif autoload:
                data['level'] = int(
                    self.env.config.get('logwatcher', 'autolevel') or 3)
                data['up'] = int(
                    self.env.config.getbool('logwatcher', 'autoup') or True)
                data['invert'] = 0
                data['regexp'] = 0
                data['filter'] = ''
                data['tail'] = self.env.config.get(
                    'logwatcher', 'autotail') or ''
                self._do_process(data, logfile)
            else:
                data['level'] = int(
                    self.env.config.get('logwatcher', 'defaultlevel') or 3)
                data['up'] = int(
                    self.env.config.getbool('logwatcher', 'defaultup') or True)
                data['invert'] = 0
                data['regexp'] = 0
                data['filter'] = ''
                data['tail'] = self.env.config.get(
                    'logwatcher', 'defaulttail') or ''

        # append the messages
        data['us_message'] = self.data['msg']
        data['us_error'] = self.data['err']
        data['us_log'] = self.data['log']
        data['levels'] = self.api.get_log_level_names(logfile)

        # adding stylesheets
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'logwatcher/css/logviewer.css')

        return html_template, data

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('logwatcher', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver/Genshi templates.
        """
        return [resource_filename(__name__, 'templates')]

    # Internal methods
    def _do_process(self, params, logfile):
        """Process form data received via POST
        @param params  : config parameters
        @param logfile : logfile name
        """
        print "PROCESS logfile %s" % logfile
        self.env.log.debug('Processing form data')
        log = self.api.get_log(logfile, params)
        self.data['log'] = log
