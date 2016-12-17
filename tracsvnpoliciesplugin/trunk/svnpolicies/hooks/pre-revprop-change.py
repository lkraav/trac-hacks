#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from loader import *

PROPERTIES = [
    'svn:log',
    'svn:eol-style',
    'svn:executable',
    'svn:keywords',
    'svn:mime-type',
    'svn:needs-lock',
    'svn:externals',
    'svn:ignore'
]


def run_command(command):
    """This function tries to run a command on to the system and
    returns a tuple composed from the exit status and the output
    of the command.
    """
    status = 0
    response = ''
    try:
        child_in, child_out_err = os.popen4(' '.join(command))
        response_list = child_out_err.readlines()
        if len(response_list) != 0:
            response = '\n'.join(response_list)
    except Exception:
        status = 4
        response = "Error in invoking the command "
    return status, response


def build_author_command(repos, rev):
    """This function returns the command used for getting the author
    for a, in progress, svn commit.
    """
    global SVNLOOK
    return [SVNLOOK, '-r', str(rev), 'author', str(repos)]


def user_author_policy(author, user, property_name, settings):
    if not settings['SVN_PROPERTY']:
        return True

    if author == user and property_name == 'svn:log':
        return True

    return False


if __name__ == '__main__':

    # STEP 1 - Read and parse the ARGUMENTS
    arguments = sys.argv[1:]
    if len(arguments) < 4:
        sys.stderr.write("wrong number of arguments!" + str(arguments))
        sys.exit(1)

    repos = arguments[0]
    if not os.path.isdir(repos):
        sys.stderr.write("the svn repository isn't set properly")
        sys.exit(2)

    # revision number
    try:
        rev = int(arguments[1])
    except ValueError:
        sys.stderr.write("bad revision number")
        sys.exit(3)

    user = arguments[2]
    propname = arguments[3]
    try:
        PROPERTIES.index(propname)
    except:
        sys.stderr.write("bad property name")
        sys.exit(4)

    # STEP 2 - Get the Trac ini SETTINGS
    # read the ini file of the trac enviroment
    config = api.IniReader(get_trac_path(__file__))

    # STEP 3 - Try to get the log message
    command = build_author_command(repos, rev)
    status, response = run_command(command)
    response = response.strip()

    if status != 0:
        sys.stderr.write("the author name couldn't be retrieved!")
        sys.exit(status)

    author = response

    # STEP 4 - Try to verify the author
    if user_author_policy(author, user, propname,
                          config.get_svn_policy_settings()):
        status = 0
    else:
        sys.stderr.write(
            "modifing this property isn't conform to the project policy!")
        status = 1

    sys.exit(status)
