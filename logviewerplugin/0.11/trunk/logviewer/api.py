import os
import fileinput
import re
from trac.core import *

class LogViewerApi(Component):
  def get_logfile_name(self):
     """Get the name of the logfile used.
     Returns None if its not configured. Raises IOError if configured but not existing.
     @return logfile or None
     """
     if self.env.config.get('logging','log_type').lower()!='file': return None
     name = self.env.config.get('logging','log_file')
     fpath, fname = os.path.split(name)
     if not fpath: name = os.path.join(self.env.path,'log',name)
     if not os.path.exists(name): raise IOError
     self.env.log.debug('Logfile name: %s' % (name,))
     return name

  def get_log(self, logname, req):
     """Retrieve the logfile content
     @param logname     : name of the logfile
     @param req
     @return array [0..n] of {level,line}
     """
     level = req.args.get('level')
     up = req.args.get('up')
     tfilter = req.args.get('filter')
     levels  = ['', 'CRITICAL:', 'ERROR:', 'WARNING:', 'INFO:', 'DEBUG:']
     classes = ['', 'log_crit', 'log_err', 'log_warn', 'log_info', 'log_debug']
     log = []
     logline = {}
     level = int(level)
     try:
       for line in fileinput.input(logname):
         if tfilter and line.find(tfilter)==-1: continue
         logline = {}
         if line.find(levels[level])!=-1:
           logline['level'] = classes[level]
           logline['line']  = line
           log.append(logline)
         elif up:
           i = level
           found = False
           while i > 0:
             if line.find(levels[i])!=-1:
               logline['level'] = classes[i]
               logline['line']  = line
               log.append(logline)
               found = True
             i -= 1
           if not found and re.search('^[^0-9]+',line):
             logline['level'] = 'log_other'
             logline['line']  = line
             log.append(logline)
     except IOError:
       self.env.log.debug('Could not read from logfile!')
     fileinput.close()
     return log
