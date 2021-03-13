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


xml = """<?xml version="1.0" encoding="UTF-8"?>
<log>
<logentry
   revision="11177">
<author>osimons</author>
<date>2012-01-22T23:42:37.751201Z</date>
<paths>
<path
   action="A"
   prop-mods="false"
   text-mods="true"
   kind="file"
   copyfrom-path="/customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py"
   copyfrom-rev="11170">/customfieldadminplugin/0.11/customfieldadmin/admin.py</path>
<path
   action="M"
   prop-mods="false"
   text-mods="true"
   kind="file">/customfieldadminplugin/0.11/customfieldadmin/api.py</path>
<path
   action="D"
   prop-mods="false"
   text-mods="false"
   kind="file">/customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py</path>
<path
   kind="file"
   action="M"
   prop-mods="false"
   text-mods="true">/customfieldadminplugin/0.11/customfieldadmin/locale/customfieldadmin.pot</path>
<path
   text-mods="true"
   kind="file"
   action="M"
   prop-mods="false">/customfieldadminplugin/0.11/customfieldadmin/locale/ja/LC_MESSAGES/customfieldadmin.po</path>
<path
   text-mods="true"
   kind="file"
   action="M"
   prop-mods="false">/customfieldadminplugin/0.11/customfieldadmin/locale/nb/LC_MESSAGES/customfieldadmin.po</path>
<path
   action="M"
   prop-mods="false"
   text-mods="true"
   kind="file">/customfieldadminplugin/0.11/customfieldadmin/locale/ru/LC_MESSAGES/customfieldadmin.po</path>
<path
   action="M"
   prop-mods="false"
   text-mods="true"
   kind="file">/customfieldadminplugin/0.11/customfieldadmin/templates/customfieldadmin.html</path>
<path
   action="M"
   prop-mods="false"
   text-mods="true"
   kind="file">/customfieldadminplugin/0.11/customfieldadmin/tests/__init__.py</path>
<path
   copyfrom-path="/customfieldadminplugin/0.11/customfieldadmin/tests/web_ui.py"
   copyfrom-rev="11170"
   action="A"
   prop-mods="false"
   text-mods="true"
   kind="file">/customfieldadminplugin/0.11/customfieldadmin/tests/admin.py</path>
<path
   action="M"
   prop-mods="false"
   text-mods="true"
   kind="file">/customfieldadminplugin/0.11/customfieldadmin/tests/api.py</path>
<path
   kind="file"
   action="D"
   prop-mods="false"
   text-mods="false">/customfieldadminplugin/0.11/customfieldadmin/tests/web_ui.py</path>
<path
   prop-mods="false"
   text-mods="true"
   kind="file"
   action="M">/customfieldadminplugin/0.11/setup.py</path>
</paths>
</logentry>
</log>
"""


def call_svn_to_unicode(cmd, repos=None):
    """Start app with the given list of parameters. Returns
    command output as unicode or an empty string in case of error.

    :param cmd: list with command, sub command and parameters
    :return: unicode string. In case of error an empty string is returned.

    Note: an error may occur when svn can't find a path or revision.
    """
    # print('  ## running %s' % (cmd,))
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
           repos.repo_url]
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
