# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Andreas Itzchak Rehberg <izzysoft@qumran.org>
# Copyright (C) 2014 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import re
import stat
import time
import locale
import collections
from trac.core import Component

CONST_TRAC_LOG = ['CRITICAL:', 'ERROR:', 'WARNING:', 'INFO:', 'DEBUG:']
CONST_TOMCAT_LOG = ['SEVERE:', 'ERROR:', 'WARNING:', 'INFO:', 'DEBUG:']


class LogViewerApi(Component):
    _log_names = {}

    def get_logfile_names(self, log_dest, log_lvl_names, sort_by=2):
        if not log_dest:
            return None
        if sort_by > 2 or sort_by < 0:
            sort_by = 2

        destinations = {}
        pos = 0
        for dest in log_dest:
            dest_path = None
            if os.path.isdir(dest):
                dest_path = dest
                filelist = []

                for f in os.listdir(dest):
                    f_abs = dest + '/' + f
                    f_stat = (f, os.stat(f_abs)[stat.ST_SIZE],
                              os.stat(f_abs)[stat.ST_MTIME])
                    filelist.append(f_stat)

                def compare_modified(a, b):
                    return cmp(b[sort_by], a[sort_by])

                filelist.sort(compare_modified)

                i = 0
                for f in filelist:
                    filelist[i] = (
                        f[0],
                        self._get_hr_number(f[1]),
                        self._get_hr_datetime(f[2])
                    )
                    i += 1

                destinations[dest] = filelist
            elif os.path.exists(dest):
                dest_path = os.path.split(dest)[0]
                dest_file = os.path.split(dest)[1]
                destinations[dest_path] = [(dest_file,
                                            self._get_hr_number(
                                                os.stat(dest)[stat.ST_SIZE]),
                                            self._get_hr_datetime(
                                                os.stat(dest)[stat.ST_MTIME]
                                            ))]
            else:
                destinations[
                    dest] = "File or directory %s does not exist" % dest

            if log_lvl_names and len(log_lvl_names) > pos:
                self._set_log_level_names(dest_path, log_lvl_names[pos])
            else:
                self._set_log_level_names(dest_path, None)
            pos = pos + 1
        destinations = collections.OrderedDict(sorted(destinations.items()))
        return destinations

    def _set_log_level_names(self, dest_path, lvl_names):
        if lvl_names is None:
            self.env.log.warn(
                'Could not find any "log_level_names", using only "ALL"')
            self._log_names[dest_path] = ['ALL']
        elif lvl_names == 'TracLog':
            self._log_names[dest_path] = CONST_TRAC_LOG
        elif lvl_names == 'TomcatLog':
            self._log_names[dest_path] = CONST_TOMCAT_LOG
        else:
            self.env.log.warn(
                'Could not find level_name "%s", using only "ALL"' % lvl_names)
            self._log_names[dest_path] = ['ALL']

    def _get_hr_datetime(self, datetime_in_sec):
        """
        @return date in human readable format
                %d.%m.%Y %H:%M:%S (German locale)
        """
        t_struct = time.localtime(datetime_in_sec)
        tstr = time.strftime("%d.%m.%Y %H:%M:%S", t_struct)
        return tstr

    def _get_hr_number(self, number):
        return locale.format("%.*f", (0, number), grouping=True)

    def get_log_level_names(self, logname):
        if logname:
            log_path = os.path.split(logname)
            if not log_path[0] in self._log_names:
                return ['ALL']
            return self._log_names[log_path[0]]
        return []

    def get_logfile_name(self):
        """Get the name of the logfile used.
        Returns None if its not configured.

        @return logfile or None
        @raise IOError: if configured but not existing
        """
        if self.env.config.get('logging', 'log_type').lower() != 'file':
            return None
        name = self.env.config.get('logging', 'log_file')
        fpath, fname = os.path.split(name)  # @UnusedVariable
        if not fpath:
            name = os.path.join(self.env.path, 'log', name)
        if not os.path.exists(name):
            raise IOError
        self.env.log.debug('Logfile name: %s' % (name))
        return name

    def get_log(self, logname, params):
        """Retrieve the logfile content
        @param logname     : name of the logfile
        @param req
        @return array [0..n] of {level,line}
        """

        up = params['up']
        invert = params['invert']
        regexp = params['regexp']

        levels = ("")
        level = int(params['level'] or 0)
        tfilter = params['filter']
        tail = int(params['tail'] or 0)
        extlines = int(params['extlines'] or 0)
        params['clinesnext'] = extlines
        params['clinesprev'] = extlines
        # Anzahl der nachfolgenden lines
        clinesnext = int(params['clinesnext'])
        # Anzahl der nachfolgenden lines
        clinesprev = int(params['clinesprev'])

        classes = [
            '', 'log_crit', 'log_err', 'log_warn', 'log_info', 'log_debug']
        log = []
        logline = {}

        try:
            f = open(logname, 'r')
            try:
                lines = f.readlines()
            finally:
                f.close()
            linecount = len(lines)
            if tail and linecount - tail > 0:
                start = linecount - tail
            else:
                start = 0

            lineprev = ""
            lineprev = ""
            for i in range(start, linecount):
                prevlines = []
                nextlines = []

                if clinesprev == 0:
                    prevlines = ""
                else:
                    for ibev in range(clinesprev + 1, 0, -1):
                        if (i - (ibev - 1)) >= 0:
                            lineprev = lines[
                                i - (ibev - 1)].decode('utf-8', 'replace')
                            prevlines.append(lineprev)
                    prevlines.pop()
                if clinesnext == 0:
                    nextlines = ""
                else:
                    for ine in range(0, clinesnext):
                        if i + (ine + 1) < linecount:
                            linenext = lines[
                                i + (ine + 1)].decode('utf-8', 'replace')
                            nextlines.append(linenext)
                        elif i + clinesnext >= linecount:
                            for inr in range(clinesnext, 0, -1):
                                linenext = lines[linecount - inr]

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
                dictprevlines = {}
                dictnextlines = {}

                if level == 0:
                    logline['level'] = classes[level + 1]
                    dictprevlines['level'] = classes[level + 1]
                    dictnextlines['level'] = classes[level + 1]
                    dictprevlines['line'] = prevlines
                    logline['line'] = line
                    dictnextlines['line'] = nextlines
                    log.append(dictprevlines)
                    log.append(logline)
                    log.append(dictnextlines)

                elif line.find(levels[level]) != -1:
                    logline['level'] = classes[level]
                    dictnextlines['level'] = classes[level]
                    dictprevlines['level'] = classes[level]
                    dictprevlines['line'] = prevlines
                    logline['line'] = line
                    dictnextlines['line'] = nextlines
                    log.append(dictprevlines)
                    log.append(logline)
                    log.append(dictnextlines)
                elif up:
                    i = level
                    found = False
                    while i > 0:
                        if line.find(levels[i]) != -1:
                            logline['level'] = classes[i]
                            dictprevlines['level'] = classes[i]
                            dictnextlines['level'] = classes[i]
                            dictprevlines['line'] = prevlines
                            logline['line'] = line
                            dictnextlines['line'] = nextlines
                            log.append(dictprevlines)
                            log.append(logline)
                            log.append(dictnextlines)
                            found = True
                        i -= 1
                    if not found and re.search('^[^0-9]+', line):
                        logline['level'] = 'log_other'
                        dictprevlines['level'] = 'log_other'
                        dictnextlines['level'] = 'log_other'
                        dictprevlines['line'] = prevlines
                        logline['line'] = line
                        dictnextlines['line'] = nextlines
                        log.append(dictprevlines)
                        log.append(logline)
                        log.append(dictnextlines)
        except IOError:
            self.env.log.debug('Could not read from logfile!')
        return log
