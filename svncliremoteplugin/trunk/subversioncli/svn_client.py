# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import subprocess

from trac.core import TracError
from trac.util.text import to_unicode
from trac.versioncontrol import Changeset
from xml.sax import parseString
from xml.sax.handler import ContentHandler


def _add_rev(path, rev):
    return '%s@%s' % (path, rev)


def _create_path(base, path):
    return '/'.join([base.rstrip('/'), path.lstrip('/')])


def get_file_content(repos, rev, path):
    """Get the contents of the given file as a unicode string.

    :param repos: Repository object. This holds e.g. the repo root information
    :param rev: revision
    :param path: the file path relative to the repository root
    :return: In case of error an empty string is returned.

    Note: an error may occur when svn can't find a path or revision.
    """
    full_path = _create_path(repos.repo_url, path)
    try:
        # repos.log.info('## ## cat: %s %s' % (rev, path))
        process = subprocess.Popen(['svn', 'cat',
                                       '-r', str(rev),
                                       full_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ret, err = process.communicate()
        if err and u'E200009' in err:
            # We need to add the revision to the path. Otherwise any path copied, moved or removed
            # in a younger revision won't be found by svn. See changeset 11183 in https://trac-hacks.org/svn
            #
            # We can't always add the revision otherwise we can't view 'normal' files in the browser. See r18058
            ret = subprocess.check_output(['svn', 'cat',
                                           '-r', str(rev),
                                           _add_rev(full_path, rev)])
    except subprocess.CalledProcessError as e:
        repos.log.error('#### svn cat failed for %s' % _add_rev(full_path, rev))
        ret = u''
    # The file contents is utf-8 encoded
    return ret


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
            repos.log.debug('#### In sVn_client.py: error with cmd "%s": %s' % (' '.join(cmd), e))
        ret = u''
    return to_unicode(ret, 'utf-8')


def list_path(repos, rev, path):
    """Get a list of files/directories with file sizes for the given path
    using 'svn list' .

    :param path: a directory or file path
    :return list of tuples, (path, (filesize, changerev))

    'filesize' is 'None' for directories. If path is a file the list only
    contains a single item.

    'snv list ...' gives all the directory entries when called for a
    directory path. Information includes change revision and filesizes
    (among others we ignore here):
       11177 author               Jan 23  2012 ./
       11168 author           497 Jan 23  2012 __init__.py
       10057 author          4416 Jan 23  2012 admin.py

    For a file path the same information is given for the single file:
       11168 author           497 Jan 23  2012 __init__.py
    """
    cmd = ['svn', '--non-interactive',
           'list', '-v',
           '-r', str(rev),
           # _create_path(self.repos.repo_url, self.path)]
           # We need to add the revision to the path. Otherwise any path copied, moved or removed
           # in a younger revision won't be found by svn. See changeset 11183 in https://trac-hacks.org/svn
           _add_rev(_create_path(repos.repo_url, path), rev)]

    ret = call_svn_to_unicode(cmd)
    if not ret:
        return []

    res = []
    changerev, name, size = 0, -1, -5
    for line in ret.split('\n'):
        parts = line.split()
        if parts and parts[name] != './':
            path = _create_path(path, parts[name])
            if path and path != '/':
                path = path.rstrip('/')
            if parts[name].strip().endswith('/'):
                # directory
                res.append((path, (None, parts[changerev])))
            else:
                res.append((path,
                            (int(parts[size]), int(parts[changerev]))
                            ))
    return res


def get_change_rev(repos, rev, path):
    """

    :param repos: Repository object, needed for base url
    :param rev: revision we query the change for. This is usually a subversion tree revision
    :param path: path of the file/directory
    :return: change revision for the given path (int)
    """
    file_info = list_path(repos, rev, path)[0]
    try:
        return file_info[1][1]
    except IndexError:
        msg = "Can't get change revision for '%s' with rev '%s'" % (path, rev)
        repos.log.error(msg)
        raise TracError("Can't get change revision for '%s' with rev '%s'" % (path, rev))


def get_blame_annotations(repos, rev, path):
    """Get data for a the given changeset rev to be displayed on the
    changeset page.

    :param repos: Repository object
    :param rev: changeset revision
    :return: list
    """
    full_path = _create_path(repos.repo_url, path)
    cmd = ['svn', '--non-interactive', 'blame',
           '-r', '%s' % (rev,),
           _add_rev(full_path, rev)]
           # repos.repo_url]
    ret = call_svn_to_unicode(cmd, repos)

    res =[]
    if ret:
        for line in ret.split('\n'):
            parts = [x.strip() for x in line.split()]
            if parts:
                res.append(int(parts[0]))
    return res


class CopyHandler(ContentHandler):
    """Parse changes for a given revision or range of revisions.
    The xml data is externally provided.

    The input data is from 'svn log -r XXX -v -q --xml ...'
    or 'svn log -r XXX:YYY -v -q --xml ...'
    """
    attrs = ('copyfrom-rev', 'copyfrom-path')
    def __init__(self):
        self.clear()
        self.current_tag = ''
        self.path_entries = []
        self.dict_of_path_entries = {}
        self.copied = []
        self.rev = 0
        ContentHandler.__init__(self)

    def clear(self):
        self.path = ''
        self.path_attrs = {}

    def get_copy_path_entries(self):
        return self.dict_of_path_entries

    # Called when an element starts
    def startElement(self, tag, attributes):
        self.current_tag = tag
        if tag == 'logentry':
            self.rev = int(attributes["revision"])
        elif tag == 'path':
            self.path_attrs = {item: attributes.get(item, '') for item in self.attrs}
            self.path_attrs['rev'] = self.rev

    # Called when an elements ends
    def endElement(self, tag):
        if tag == "logentry":
            for attrs, path in self.path_entries:
                from_path = attrs.get('copyfrom-path')
                if from_path:
                    self.dict_of_path_entries[path] = from_path
            self.path_entries = []
        elif tag == 'path':
            self.path_entries.append((self.path_attrs, self.path))
            self.clear()
        self.current_tag = ''

    # Called when a character is read
    def characters(self, content):
        if self.current_tag == "path":
            self.path += content


def get_copy_info(repos, start_rev):
    """Get data for a the given changeset rev to be displayed on the
    changeset page.

    :param repos: Repository object
    :param rev: changeset revision
    :return: a dict {current_path: copyfrom_path}
    """
    # svn log -r 11177 -v -q --xml
    cmd = ['svn', '--non-interactive', 'log',
           '-r', '%s:1' % (start_rev,),
           '-v', '-q', '--xml',
           repos.repo_url]

    ret = call_svn_to_unicode(cmd, repos)
    if ret:
        handler = CopyHandler()  # This parses a log with one or more logentries
        parseString(ret.encode('utf-8'), handler)
        res = handler.get_copy_path_entries()
        return res
    else:
        return {}


class ChangesHandler(ContentHandler):
    """Parse changes for a given revision or range of revisions.
    The xml data is externally provided.

    The input data is from 'svn log -r XXX -v -q --xml ...'
    or 'svn log -r XXX:YYY -v -q --xml ...'
    """
    attrs = ('action', 'kind', 'text-mods', 'copyfrom-rev', 'copyfrom-path')
    def __init__(self):
        self.clear()
        self.current_tag = ''
        self.path_entries = []
        self.list_of_path_entries = []
        self.copied = []
        self.deleted = []
        self.rev = 0
        ContentHandler.__init__(self)

    def clear(self):
        self.path = ''
        self.path_attrs = {}

    def get_path_entries(self):
        return self.list_of_path_entries

    # Called when an element starts
    def startElement(self, tag, attributes):
        self.current_tag = tag
        if tag == 'logentry':
            self.rev = int(attributes["revision"])
        elif tag == 'path':
            self.path_attrs = {item: attributes.get(item, '') for item in self.attrs}
            # self.path_attrs = {k: v for k, v in attributes.items()}
            self.path_attrs['rev'] = self.rev

    # Called when an elements ends
    def endElement(self, tag):
        if tag == "logentry":
            self.list_of_path_entries.append((self.path_entries, self.copied, self.deleted))
            self.copied = []
            self.path_entries = []
        elif tag == 'path':
            if self.path_attrs.get('copyfrom-path'):
                self.copied.append(self.path_attrs.get('copyfrom-path', ''))
            if self.path_attrs.get('action') == 'D':
                self.deleted.append(self.path)
            # if self.path.startswith('/htgroupsplugin'):
            self.path_entries.append((self.path_attrs, self.path))
            self.clear()
        self.current_tag = ''

    # Called when a character is read
    def characters(self, content):
        if self.current_tag == "path":
            self.path += content


def get_changeset_info(repos, rev):
    """Get data for a the given changeset rev to be displayed on the
    changeset page.

    :param repos: Repository object
    :param rev: changeset revision
    :return: a tuple ([({attrs}, path), (...)], [copy1, copy2])
    """
    # svn log -r 11177 -v -q --xml
    cmd = ['svn', '--non-interactive', 'log',
           '-r', '%s' % (rev,),
           '-v', '-q', '--xml',
           # We need to add the revision to the path. Otherwise any path copied, moved or removed
           # in a younger revision won't be found by svn. See changeset 11183 in https://trac-hacks.org/svn
           _add_rev(repos.repo_url, rev)]
           # repos.repo_url]

    ret = call_svn_to_unicode(cmd, repos)
    if ret:
        handler = ChangesHandler()  # This parses a log with one or more logentries
        parseString(ret.encode('utf-8'), handler)
        return handler.get_path_entries()[0]  # This is a list of tuples but we only requested one log here
    else:
        return [], None


def get_history(repos, rev, path, limit=None):
    """Get the history for the given path at revision rev.

    :param repos: Repository object. This holds e.g. the repo root information
    :param rev: revision
    :param path: the file/directory path relative to the repository root
    :param limit: number of history items to return
    :return: a list of tuples: (path, revisions, change)

    This is called from Node.get_history() when showing the revision log.
    """
    def is_copied_dir(attrs):
        return attrs.get('action') == 'A' and attrs.get('kind') == 'dir' and attrs.get('copyfrom-path')
    cmd = ['svn', '--non-interactive',
           'log',
           '-q', '-v', '--xml',
           '-r', '%s:1' % rev]
    if limit:
        cmd += ['-l', str(limit)]
    cmd.append(_add_rev(_create_path(repos.repo_url, path), rev))

    ret = call_svn_to_unicode(cmd)
    history = []
    if ret:
        # Used to track path over copy and move
        cur_path = path
        handler = ChangesHandler()
        parseString(ret.encode('utf-8'), handler)

        # List of tuples:
        # ([({attrs}, path1), (...)], [copyfrom-path 1, copyfrom-path 2])
        logentries = handler.get_path_entries()
        for entry in logentries:  # This contains all the information for one revision
            path_entries, copied, deleted = entry
            for attrs, path_ in path_entries:
                path_ = path_[1:]  # returned path has a leading '/'
                if path_ == cur_path or is_copied_dir(attrs):
                    if attrs['action'] == 'M':
                        history.append((path_, attrs['rev'], Changeset.EDIT))
                    elif attrs['action'] == 'A':
                        if attrs['copyfrom-path']:
                            copied_path = attrs['copyfrom-path'][1:]
                            if is_copied_dir(attrs):
                                # A copied directory needs special dealing with paths
                                # history.append((cur_path, attrs['rev'], Changeset.EDIT))
                                history.append((cur_path, attrs['rev'], Changeset.COPY))
                                # Because we copied the whole directory we have to adjust the leading
                                # directory sub path to the old location.
                                cur_path = cur_path.replace(path_, copied_path)
                                #change_rev = get_change_rev(repos, attrs['copyfrom-rev'], cur_path)
                            else:
                                history.append((path_, attrs['rev'], Changeset.COPY))
                                # Note that copyfrom-rev is the revision of the subversion tree when the copy took
                                # place. It isn't the change revision of the file being copied.
                                cur_path = cur_path.replace(path_, copied_path)
                        else:
                            history.append((cur_path, attrs['rev'], Changeset.ADD))
    return history


if __name__ == '__main__':
    for item in get_changeset_info(None, 11177):
        attrs, path = item
        if attrs['action'] == u'M':
            pass
        print(item)
