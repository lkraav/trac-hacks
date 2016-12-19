#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrei Culapov <aculapov@optaros.com>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os
import re
import subprocess
import sys

from loader import *


def epopen(cmd):
    """
    This function adds some variables in the environment before
    running a command.
    """
    global TRAC_ENV, production
    # env is a dictionary of environment variables
    prefix = ''
    if PYTHONPATH != '' and production:
        prefix = 'export "PYTHONPATH=%s"; \n' % PYTHONPATH
    p = subprocess.Popen(prefix + cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    out_text = p.stdout.readlines()
    pid, status = os.waitpid(p.pid, 0)
    status %= 255
    return status, out_text


def run_command(command):
    """
    This function tries to run a command on to the system
    and returns a tuple composed from the exit status and
    the output of the command.
    """
    try:
        p = subprocess.Popen(' '.join(command), shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        response = p.stdout.read()
    except Exception, e:
        status = 4
        response = "Error in invoking the command: %s" % e
    else:
        pid, status = os.waitpid(p.pid, 0)
        status %= 255
    return status, response


def build_log_command(repos, txn):
    """
    This function returns the command used for getting the
    log message for an in-progress svn commit.
    """
    global SVNLOOK
    return [SVNLOOK, 'log', '-t', str(txn), str(repos)]


def check_log(log, settings):
    """
    This function checks if a log message from an in-progress
    svn commit is validated according to the policies
    described in the settings.
    """
    if 'LOG' in settings:
        if settings['LOG']:
            if len(log) == 0:
                return False
        else:
            # the project admin does not need log checking
            return True
    else:
        # the global setting is not set
        return True
    # check the log size
    if 'LOG_SIZE' in settings:
        if len(log.strip()) < int(settings['LOG_SIZE']):
            return False
    # check the pattern
    if 'LOG_PATTERN' in settings:
        regex = re.compile(settings['LOG_PATTERN'])
        if regex is not None:
            if regex.match(log) is None:
                return False
    return True


def run_trac_advanced(settings, repos, rev):
    """
    This method tries to run the script edited by the project admin.
    """
    if not settings['ADVANCED_PRE']:
        return 0, ''
    return run_command([settings['ADVANCED_PRE_FILE'],
                        str(repos),
                        str(rev), ])


if __name__ == '__main__':

    # STEP 1 - Read and parse the ARGUMENTS
    arguments = sys.argv[1:]
    if len(arguments) != 2:
        sys.stderr.write("""wrong number of arguments!
""")
        sys.exit(1)

    repos = arguments[0]
    if not os.path.isdir(repos):
        sys.stderr.write("""the svn repository isn't set properly
""")
        sys.exit(2)

    txn = arguments[1]

    # STEP 2 - Get the Trac ini SETTINGS
    # read the ini file of the trac environment
    config = api.IniReader(get_trac_path(__file__))

    # STEP 3 - If the svn repository is readonly reject the commit
    if config.get_svn_policy_settings()['READONLY']:
        sys.stderr.write("The svn repository is readonly! Commit rejected!\n")
        sys.exit(1)

    # STEP 4 - Try to get the log message
    command = build_log_command(repos, txn)
    status, response = run_command(command)
    if status != 0:
        sys.stderr.write("""the log message couldn't be retrieved!
""")
        sys.exit(status)

    if response == '':
        sys.stderr.write("""no log message
""")
        sys.exit(1)

    # STEP 5 - Try to verify the log message
    if check_log(response, config.get_svn_policy_settings()):
        status = 0
    else:
        sys.stderr.write("""the log message doesn't conform to the project policy!
""")
        status = 1

    # STEP 6 - Try to run the scripts from the trac hooks directory
    advanced_status, advanced_response = run_trac_advanced(
        config.get_svn_policy_settings(), repos, txn)
    if response != '':
        response += '\n'
    response += advanced_response
    status = status or advanced_status

    # STEP 7 - Exit the Hook
    if response != '':
        sys.stderr.write(response)

    sys.exit(status)
