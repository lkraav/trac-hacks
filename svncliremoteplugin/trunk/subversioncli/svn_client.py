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
from xml.sax import parseString
from xml.sax.handler import ContentHandler


def _add_rev(path, rev):
    return '%s@%s' % (path, rev)


def call_svn_to_unicode(cmd, repos=None):
    """Start app with the given list of parameters. Returns
    command output as unicode or an empty string in case of error.

    :param cmd: list with command, sub command and parameters
    :return: unicode string. In case of error an empty string is returned.

    Note: an error may occur when svn can't find a path or revision.
    """
    # print('  ## svn_client.py running %s' % (cmd,))
    try:
        ret = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        if repos:
            repos.log.info('#### svn error with cmd "%s": %s' % (cmd[1], e))
        ret = u''
    return to_unicode(ret, 'utf-8')

class ChangesHandler(ContentHandler):
    """Parse changes for a given revision.

    The input data is from 'svn log -r XXX -v -q --xml ...'
    """
    attrs = ('action', 'kind', 'text-mods', 'copyfrom-rev', 'copyfrom-path')
    def __init__(self, tzinfo=None):
        self.clear()
        self.current_tag = ''
        self.path_entries = []
        self.copied = []
        ContentHandler.__init__(self)

    def clear(self):
        self.rev = None
        self.path = ''
        self.path_attrs = {}

    def get_path_entries(self):
        return self.path_entries, self.copied

    # Called when an element starts
    def startElement(self, tag, attributes):
        self.current_tag = tag
        if tag == 'logentry':
            self.rev = int(attributes["revision"])
        elif tag == 'path':
            self.path_attrs = {item: attributes.get(item, '') for item in self.attrs}

    # Called when an elements ends
    def endElement(self, tag):
        if tag == "logentry":
            pass
        elif tag == 'path':
            if self.path_attrs.get('copyfrom-path'):
                self.copied.append(self.path_attrs.get('copyfrom-path', ''))
            self.path_entries.append((self.path_attrs, self.path))
            self.clear()
        self.current_tag = ''

    # Called when a character is read
    def characters(self, content):
        if self.current_tag == "path":
            self.path += content


def get_changeset_info(repos, rev):
    """

    :param repos: Repository object
    :param rev: changeset revision
    :return:
    """
    # svn log -r 11177 -v -q --xml
    cmd = ['svn', '--non-interactive', 'log',
           '-r', '%s' % (rev,),
           '-v', '-q', '--xml',
           # We need to add the revision to the path. Otherwise any path copied, moved ore removed
           # in a younger revision won't be found by svn. See changeset 11183 in https://trac-hacks.org/svn
           _add_rev(repos.repo_url, rev)]
           # repos.repo_url]

    ret = call_svn_to_unicode(cmd, repos)
    if ret:
        handler = ChangesHandler()
        parseString(ret.encode('utf-8'), handler)
        return handler.get_path_entries()
    else:
        return [], None


if __name__ == '__main__':
    for item in get_changeset_info(None, 11177):
        attrs, path = item
        if attrs['action'] == u'M':
            pass
        print(item)
