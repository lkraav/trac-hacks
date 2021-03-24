# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import subprocess

from util import add_rev, call_cmd_to_unicode, join_path
from trac.core import TracError
from trac.util.text import to_unicode
from trac.versioncontrol import Changeset
from xml.sax import parseString
from xml.sax.handler import ContentHandler


def get_file_content(repos, rev, path, query_path):
    """Get the contents of the given file as a unicode string.

    :param repos: Repository object. This holds e.g. the repo root information
    :param rev: revision
    :param path: the file path relative to the repository root
    :param query_path: fully qualified path into the repo. This may include
           revisions and has already followed every copy operation. Known to have worked in the past.
    :return: In case of error an empty string is returned.

    Note: an error may occur when svn can't find a path or revision.
    """
    if query_path:
        try:
            ret = subprocess.check_output(['svn', 'cat',
                                           '-r', str(rev),
                                           query_path])
            return ret
        except subprocess.CalledProcessError:
            raise TracError('svn cat: query_path is there but is not working!')  # We shouldn't end here

    raise TracError('svn cat: query_path is empty! (%s, %s, %s )' %
                    (path, repr(query_path), rev))  # We shouldn't end here (?)


def list_path(repos, rev, path):
    """Get a list of files/directories with file sizes for the given path
    using 'svn list' .

    :param repos: Repository object
    :param rev: revision of file/directory we query
    :param path: a directory or file path relative to the real root of the repo
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
           # We need to add the revision to the path. Otherwise any path copied, moved or removed
           # in a younger revision won't be found by svn. See changeset 11183 in https://trac-hacks.org/svn
           add_rev(join_path(repos.root, path), rev)]

    ret = call_cmd_to_unicode(cmd)
    if not ret:
        return []

    res = []
    changerev, name, size = 0, -1, -5
    for line in ret.split('\n'):
        parts = line.split()
        if parts and parts[name] != './':
            path = join_path(path, parts[name])
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

# TODO: this is the only function calling list_path. Unify them after checking the similar method
#       in Changeset class
def get_change_rev(repos, rev, path):
    """

    :param repos: Repository object, needed for base url
    :param rev: revision we query the change for. This is usually a subversion tree revision
    :param path: path of the file/directory relative to the real root of the repo.
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
    """Get blame inforamtion for the given file with given rev.

    :param repos: Repository object
    :param rev: changeset revision
    :param path: the filepath. This is a relative path into the repo
    :return: list
    """
    full_path = join_path(repos.repo_url, path)
    cmd = ['svn', '--non-interactive', 'blame',
           '-r', '%s' % (rev,),
           add_rev(full_path, rev)]
    ret = call_cmd_to_unicode(cmd, repos)

    res = []
    if ret:
        for line in ret.split('\n'):
            parts = [x.strip() for x in line.split()]
            if parts:
                res.append(int(parts[0]))
    return res


class PropertiesHandler(ContentHandler):
    """Get a dict of all copy operations within the repo.

    This is used to find files for a given revision which were
    later copied and then removed in a younger revisions.

    Parse log data for a given revision or range of revisions.
    The xml data is externally provided.

    The input data is from 'svn log -r XXX -v -q --xml ...'
    or 'svn log -r XXX:YYY -v -q --xml ...'
    """

    def __init__(self):
        self.property = ''
        self.current_tag = ''
        self.properties = {}
        ContentHandler.__init__(self)

    def clear(self):
        self.property = ''

    def get_properties(self):
        return self.properties

    # Called when an element starts
    def startElement(self, tag, attributes):
        self.current_tag = tag
        if tag == 'property':
            self.propname = attributes['name']

    # Called when an elements ends
    def endElement(self, tag):
        if tag == 'property':
            self.properties[self.propname] = self.property
            self.clear()
        self.current_tag = ''

    # Called when a character is read
    def characters(self, content):
        if self.current_tag == "property":
            self.property += content


def get_properties_list(repos, rev, path):
    """

    :param repos:
    :param rev:
    :param path: full path into the repo including file:// or http://
    :return:
    """
    cmd = ['svn', '--non-interactive', 'proplist',
           '-r', str(rev),
           '-v', '--xml',
           path]

    ret = call_cmd_to_unicode(cmd, repos)
    if ret:
        handler = PropertiesHandler()  # This parses a log with one or more logentries
        parseString(ret.encode('utf-8'), handler)
        return handler.get_properties()
    else:
        return {}


class CopyHandler(ContentHandler):
    """Get a dict of all copy operations within the repo.

    This is used to find files for a given revision which were
    later copied and then removed in a younger revisions.

    Parse log data for a given revision or range of revisions.
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
        self.rev = 0
        ContentHandler.__init__(self)

    def clear(self):
        self.path = ''
        self.path_attrs = {}

    def get_copy_path_entries(self):
        return self.dict_of_path_entries

    def normalize_path(self, path):
        return path.lstrip('/') or '/'

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
                    self.dict_of_path_entries[self.normalize_path(path)] = self.normalize_path(from_path)
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
    """Get all copy operation in the past starting with start_rev.

    :param repos: Repository object
    :param start_rev: youngest changeset revision we start with.
    :return: a dict {current_path: copyfrom_path}

    This data is used when trying to follow a path which may have moved in the past when
    querying the history.
    """
    # svn log -r 11177 -v -q --xml
    cmd = ['svn', '--non-interactive', 'log',
           '-r', '%s:1' % (start_rev,),
           '-v', '-q', '--xml',
           repos.root]

    ret = call_cmd_to_unicode(cmd, repos)
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
           add_rev(repos.root, rev)]

    ret = call_cmd_to_unicode(cmd, repos)
    if ret:
        handler = ChangesHandler()  # This parses a log with one or more logentries
        parseString(ret.encode('utf-8'), handler)
        # path, copied, deleted = handler.get_path_entries()[0]
        # return  path[163:164], copied, deleted
        return handler.get_path_entries()[0]  # This is a list of tuples but we only requested one log here
    else:
        return [], None


def get_history(repos, rev, path, limit=None):
    """Get the history for the given path at revision rev.

    :param repos:
    :param rev:
    :param path:
    :param limit: number of history items to return
    :return: a list of tuples: (path, revisions, change)

    This is called from Node.get_history() when showing the revision log.
    """
    def is_copied_dir(attrs_):
        return attrs_.get('action') == 'A' and attrs_.get('kind') == 'dir' and attrs_.get('copyfrom-path')

    # See htgroupsplugin/trunk/htgroups/__init__.py@1984: don't use created_rev here
    path = repos.full_path_from_normalized(path)
    cmd = ['svn', '--non-interactive',
           'log',
           '-q', '-v', '--xml',
           '-r', '%s:1' % rev]
    if limit:
        cmd += ['-l', str(limit)]
    cmd.append(add_rev(join_path(repos.root, path), rev))

    ret = call_cmd_to_unicode(cmd)
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
                # With is_copied_dir(attrs) check for svn-copied parent directories, e.g. when branching.
                if path_ == cur_path or is_copied_dir(attrs):
                    if attrs['action'] == 'M':
                        history.append((path_, attrs['rev'], Changeset.EDIT))
                    elif attrs['action'] == 'A':
                        if attrs['copyfrom-path']:
                            copied_path = attrs['copyfrom-path'][1:]
                            if is_copied_dir(attrs):
                                # Only add to history and adjust path if this copy operation
                                # affects our path
                                if cur_path.startswith(path_):
                                    # A copied directory needs special dealing with paths
                                    history.append((cur_path, attrs['rev'], Changeset.COPY))
                                    # Because we copied the whole directory we have to adjust the leading
                                    # directory sub path to the older location.
                                    cur_path = cur_path.replace(path_, copied_path, 1)
                            else:
                                # Note that copyfrom-rev is the revision of the subversion tree when the copy took
                                # place. It isn't the change revision of the file being copied.
                                history.append((path_, attrs['rev'], Changeset.COPY))
                                # Account for path change due to copy
                                # cur_path = cur_path.replace(path_, copied_path)
                                cur_path = copied_path
                        else:
                            history.append((cur_path, attrs['rev'], Changeset.ADD))
    return history


if __name__ == '__main__':
    pass
