# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import subprocess

from trac.util.text import to_unicode


def add_rev(path, rev):
    return '%s@%s' % (path, rev)


def join_path(base, path):
    """Create a joined path from two path components. Change escape characters.

    :param base: The first part, usually the base path into a repo
    :param path: second part, usually the path of a node.
    :return: a joined path with '/' as separator.

    Some file names are 'Foo%2Fbar' in the repo which are expanded by the svn client
    to 'foo/bar' albeit they are properly encoded. Prevent this unescaping.
    """
    path = path.replace('%2F', '%252F')
    return '/'.join([base.rstrip('/'), path.lstrip('/')])


def call_cmd_to_unicode(cmd, repos=None):
    """Start cmd with the given list of parameters. Returns
    command output as unicode or an empty string in case of error.

    :param cmd: list with command, sub command and parameters
    :param repos: Repository object for using logging
    :return: unicode string. In case of error an empty string is returned.
    """
    # print('  ## In svn_cli.py: running %s' % (' '.join(cmd),))
    try:
        ret = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        if repos:
            repos.log.debug('#### In svn_cli.py: error with cmd "%s":\n    %s' % (' '.join(cmd), e))
        ret = u''
    return to_unicode(ret, 'utf-8')
