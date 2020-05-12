import os
import re

from trac.core import Component, implements
from trac.config import BoolOption, IntOption, Option
from trac.admin.api import IAdminPanelProvider
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider, add_stylesheet


class LogViewerPage(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

    _autoload = BoolOption('logviewer', 'autoload', False,
        doc="""Whether the log file content should be automatically
        loaded when the module is called, i.e. even before the form
        was submitted. This is a boolean option (true/false), and
        defaults to false.
        """)

    _autolevel = IntOption('logviewer', 'autolevel', 3,
        doc="""Which log level shall be used on autoload (only applies
        when autoload is enabled). This integer value defaults to 3
        (warnings). Possible values: 1=critical, 2=error, 3=warning,
        4=info, 5=debug
        """)

    _autoup = BoolOption('logviewer', 'autoup', True,
        doc="""Include log events of higher levels than autolevel on
        autoload? This boolean option defaults to true - and only
        applies on autoload
        """)

    _autotail = IntOption('logviewer', 'autotail', 1000,
        doc="""Only applies to autoload: Restrict the evaluated lines
        to the last N lines. Defaults to 1000.
        """)

    _defaultlevel = IntOption('logviewer', 'defaultlevel', 3,
        doc="""Preset for the log level dropdown (if autoload is disabled).
        This integer value defaults to 3 (warnings). Possible values:
        1=critical, 2=error, 3=warning, 4=info, 5=debug
        """)

    _defaultup = BoolOption('logviewer', 'defaultup', True,
        doc="""Check the box to include log events of higher levels
        when autoload is disabled? This boolean option defaults to true.
        """)

    _defaulttail = IntOption('logviewer', 'defaulttail', 100,
        doc="""Preset for the Tail input (restrict query to the last N
        lines of the logfile to load). This must be a number (integer),
        and by default is empty (not set)
        """)

    # IAdminPageProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield 'general', _('General'), 'logviewer', _('Log Viewer')

    def render_admin_panel(self, req, cat, page, path_info):
        data = {
            'err': [],
            'msg': [],
            'log': [],
        }
        autoload = self.config.getbool('logviewer', 'autoload')
        try:
            logfile = self._get_logfile_name()
            if not logfile:
                self.log.debug('No log file configured.')
                data['err'].append(
                    'There is no log file configured for this environment.')
        except IOError:
            self.log.debug('Got IOError - configured log file does not exist!')
            data['err'].append('The configured log file does not exist.')

        if logfile:
            params = {}
            if req.method == 'POST':
                params['level'] = req.args.get('level')
                params['up'] = req.args.get('up')
                params['invert'] = req.args.get('invertsearch')
                params['regexp'] = req.args.get('regexp')
                params['tail'] = req.args.getint('tail')
                params['filter'] = req.args.get('filter')
                data['log'] = self._do_process(params, logfile)
                data['level'] = req.args.getint('level')
                data['up'] = req.args.getint('up')
                data['invert'] = req.args.getint('invertsearch')
                data['regexp'] = req.args.getint('regexp')
                data['filter'] = req.args.get('filter', '')
                data['tail'] = req.args.get('tail', '')
            elif autoload:
                data['level'] = self.config.getint('logviewer', 'autolevel')
                data['up'] = self.config.getbool('logviewer', 'autoup')
                data['invert'] = 0
                data['regexp'] = 0
                data['filter'] = ''
                data['tail'] = self.config.get('logviewer', 'autotail')
                data['log'] = self._do_process(data, logfile)
            else:
                data['level'] = self.config.getint('logviewer', 'defaultlevel')
                data['up'] = int(self.config.getbool('logviewer', 'defaultup'))
                data['invert'] = 0
                data['regexp'] = 0
                data['filter'] = ''
                data['tail'] = self.config.getint('logviewer', 'defaulttail') \
                               or 100

        data['us_message'] = data['msg']
        data['us_error'] = data['err']
        data['us_log'] = data['log']

        add_stylesheet(req, 'logviewer/css/logviewer.css')

        return 'logviewer.html', data, None

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('logviewer', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Internal methods

    def _do_process(self, params, logfile):
        self.log.debug('Processing form data')
        log = self._get_log(logfile, params)
        return log

    def _get_logfile_name(self):
        if self.config.get('logging', 'log_type').lower() != 'file':
            return None
        name = self.config.get('logging', 'log_file')
        fpath, fname = os.path.split(name)
        if not fpath:
            name = os.path.join(self.env.path, 'log', name)
        if not os.path.exists(name):
            raise IOError
        self.log.debug('Logfile name: %s', name)
        return name

    def _get_log(self, logname, params):
        up = params['up']
        invert = params['invert']
        regexp = params['regexp']
        level = int(params['level'])
        tfilter = params['filter']
        tail = int(params['tail'] or 0)
        levels = ['', 'CRITICAL:', 'ERROR:', 'WARNING:', 'INFO:', 'DEBUG:']
        classes = ['', 'log_crit', 'log_err',
                   'log_warn', 'log_info', 'log_debug']
        log = []
        logline = {}
        try:
            with open(logname, 'r') as f:
                lines = f.readlines()
            linecount = len(lines)
            if tail and linecount - tail > 0:
                start = linecount - tail
            else:
                start = 0
            for i in range(start, linecount):
                line = lines[i].decode('utf-8', 'replace')
                if tfilter:
                    if regexp:
                        if not invert and not re.search(tfilter, line):
                            continue
                        if invert and re.search(tfilter, line):
                            continue
                    else:
                        if not invert and line.find(tfilter) == -1:
                            continue
                        if invert and not line.find(tfilter) == -1:
                            continue
                logline = {}
                if line.find(levels[level]) != -1:
                    logline['level'] = classes[level]
                    logline['line'] = line
                    log.append(logline)
                elif up:
                    i = level
                    found = False
                    while i > 0:
                        if line.find(levels[i]) != -1:
                            logline['level'] = classes[i]
                            logline['line'] = line
                            log.append(logline)
                            found = True
                        i -= 1
                    if not found and re.search('^[^0-9]+', line):
                        logline['level'] = 'log_other'
                        logline['line'] = line
                        log.append(logline)
        except IOError:
            self.log.debug('Could not read from logfile!')
        return log
