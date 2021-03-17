# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import os
import re
import subprocess
import time

from xml.sax import parseString
from xml.sax.handler import ContentHandler
from datetime import datetime
from io import BytesIO, StringIO
from pkg_resources import parse_version

from svn_client import get_blame_annotations, get_change_rev, get_changeset_info, get_copy_info,\
    get_file_content, get_history, get_properties_list
from datetime_z import parse_datetime
from trac.config import ChoiceOption
from trac.core import Component, implements, TracError
from trac.env import ISystemInfoProvider
from trac.util.datefmt import to_datetime, utc
from trac.util.text import exception_to_unicode, to_unicode, to_utf8
from trac.util.translation import _
from trac.versioncontrol import Changeset, Node, Repository, \
                                IRepositoryConnector, InvalidRepository, \
                                NoSuchChangeset, NoSuchNode
from threading import RLock


NUM_REV_INFO = 500


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start


def _from_svn(path):
    """Expect an UTF-8 encoded string and transform it to an `unicode` object

    But Subversion repositories built from conversion utilities can have
    non-UTF-8 byte strings, so we have to convert using `to_unicode`.
    """
    return path and to_unicode(path, 'utf-8')


def _create_path(base, path):
    return '/'.join([base.rstrip('/'), path.lstrip('/')])


def _add_rev(path, rev):
    return '%s@%s' % (path, rev)


def _call_svn_to_unicode(cmd, repos=None):
    """Start app with the given list of parameters. Returns
    command output as unicode or an empty string in case of error.

    :param cmd: list with command, sub command and parameters
    :return: unicode string. In case of error an empty string is returned.

    Note: an error may occur when svn can't find a path or revision.
    """
    # print('  ## In svn_cli.py: running %s' % (' '.join(cmd),))
    try:
        ret = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        if repos:
            repos.log.debug('#### In svn_cli.py: error with cmd "%s":\n    %s' % (' '.join(cmd), e))
        ret = u''
    return to_unicode(ret, 'utf-8')


def _get_svn_info(repos, rev, path=''):
    """Get information about the given path from the local repo.

    :param repos: a SubversionRepositoryCli object
    :param path: relative path in the repo
    :return: dict

    The output of 'svn info -r XXX repo/path' is parsed and put into a dict.

    Sample output is:

    Path: readme.doc
    Name: readme.doc
    URL: http://svn.red-bean.com/repos/test/readme.doc
    Repository Root: http://svn.red-bean.com/repos/test
    Repository UUID: 5e7d134a-54fb-0310-bd04-b611643e5c25
    Revision: 1
    Node Kind: file
    Schedule: normal
    Last Changed Author: sally
    Last Changed Rev: 42
    Last Changed Date: 2003-01-14 23:21:19 -0600 (Tue, 14 Jan 2003)
    Lock Token: opaquelocktoken:14011d4b-54fb-0310-8541-dbd16bd471b2
    Lock Owner: harry
    Lock Created: 2003-01-15 17:35:12 -0600 (Wed, 15 Jan 2003)
    Lock Comment (1 line):
    My test lock comment

    The part left from ':' is the dict key, the right part is the value.
    """
    # TODO: check if concat of url and path is always working. Use posix_path instead
    full_path = _create_path(repos.repo_url, path)
    # repos.log.info('#################################')
    # repos.log.info('%s, %s, %s' % (repos.repo_url, path, full_path))
    # repos.log.info('#################################')
    cmd = ['svn', '--non-interactive',
           'info',
           # '-r', str(rev),
           _add_rev(full_path, rev)]
    ret = _call_svn_to_unicode(cmd, repos)  # to_unicode(ret, 'utf-8')

    if not ret:
        return None

    info = ret.split('\n')
    repo_info = {}
    for item in info:
        if item:
            key, nope, val = item.partition(':')
            repo_info[key.strip()] = val.strip()
    return repo_info


def _get_svn_history(repos, rev, path, limit=None):
    """Get the history for the given path at revision rev.

    :param repos: Repository object. This holds e.g. the repo root information
    :param rev: revision
    :param path: the file/directory path relative to the repository root
    :param limit: number of history items to return
    :return: a list of revisions

    This is called from Node.get_history() when showing the revision log.
    """
    # repos.log.info('### in _get_svn_history(%s, %s, %s, %s)' % (repos, rev, path, limit))
    cmd = ['svn', '--non-interactive',
           'log',
           '-q',
           '-r', '%s:1' % str(rev)]
    if limit:
        cmd += ['-l', str(limit)]
    # TODO: check if we should use @rev here
    cmd.append(_create_path(repos.repo_url, path))
    ret = _call_svn_to_unicode(cmd).split('\n')

    history = []
    for line in ret:
        if line and not line.startswith(u'---'):
            history.append(int(line.split('|')[0].strip('r ')))

    return history


class LogHandler(ContentHandler):

    def __init__(self, tzinfo=None):
        self.tzinfo = tzinfo
        self.clear()
        self.current_tag = ''
        self.log_entries = []
        ContentHandler.__init__(self)

    def clear(self):
        self.date = datetime(1970, 1, 1, tzinfo=utc)
        self.msg = ""
        self.author = ""
        self.rev = None
        self._date = u''

    def get_log_entries(self):
        return self.log_entries

    # Called when an element starts
    def startElement(self, tag, attributes):
        self.current_tag = tag
        if tag == 'logentry':
            self.rev = int(attributes["revision"])

    # Called when an elements ends
    def endElement(self, tag):
        if tag == "logentry":

            dt = parse_datetime(self._date)
            if dt:
                # TODO: tzinfo isn't used
                if self.tzinfo:
                    try:
                        dt = dt.astimezone(self.tzinfo)
                        print('  ## Rev: %s, %s, %s' % (self.rev, self._date, dt))
                    except AttributeError as e:
                        print('#####################################')
                        print('Rev: %s' % (self.rev,))
                        print('#####################################')
                        raise AttributeError(e)
                self.date = dt.replace(tzinfo=None)
            self.log_entries.append((self.rev, self.author, self.date, self.msg))
            self.clear()
        self.current_tag = ''

    # Called when a character is read
    def characters(self, content):
        if self.current_tag == "msg":
            self.msg += content
        elif self.current_tag == "date":
            self._date += content
        elif self.current_tag == "author":
            self.author = content


def _svn_changerev(repos, rev, path):
    """Get the change revision for the given change using 'svn info'.

    :param repos: Repository object. This holds e.g. the repo root information
    :param rev: revision number, must be an int
    :param path: the file/directory path relative to the repository root
    :return: revision the given path was created/changed as an int

    The current revision for a file is the repo revision. That is not necessarily
    the revision the file was altered.
    """
    info = _get_svn_info(repos, str(rev), path)
    if not info:
        return None
    return int(info['Last Changed Rev'])


def _svn_rev_info(repos, rev):
    """Get information about the revision rev.

    This calls 'svn log -r <xxx> path/to/repo' on the repository to get
    changeset information (no info about changeset diffs here).

    Returns author, datetime, message
    """
    # repos.log.info('### in _svn_rev_info(%s, %s)' % ('repos', rev))
    cmd = ['svn', 'log',
           '-r', str(rev),
           repos.repo_url]

    ret = _call_svn_to_unicode(cmd)
    if ret:
        info = ret.split('\n')
        # The date is something like '2021-03-07 14:59:56 +0100 (Sun, 07 Mar 2021)'
        rev_, author, date, numlines = [x.strip() for x in info[1].split('|')]
        date = [x.strip() for x in date.partition('(')[0].split()]  # ['2021-03-07', '14:59:56', '+0100']

        # author, datetime, message
        try:
            # Note there is a trailing \n in the log output thus an empty string at the end of info[]
            return author, parse_datetime(u'{} {}{}'.format(*date)), '\n'.join(info[3:-2])
        except IndexError:
            pass
    repos.log.info('#### Changeset %s is broken' % rev)
    return '', datetime.now(utc), ''


class SubversionConnector(Component):
    implements(IRepositoryConnector, ISystemInfoProvider)

    eol_style = ChoiceOption(
        'svn', 'eol_style', ['native', 'LF', 'CRLF', 'CR'], doc=
        """End-of-Line character sequences when `svn:eol-style` property is
        `native`.

        If `native`, substitute with the native EOL marker on the server.
        Otherwise, if `LF`, `CRLF` or `CR`, substitute with the specified
        EOL marker.""")

    error = None

    def __init__(self):
        self._version = None
        try:
            ver = subprocess.check_output(['svn', '--version', '-q'])
        except OSError as e:
            self.error = e
            self.log.info(e)
        else:
            self._version = str(parse_version(ver.strip('\n')))

    # IRepositoryConnector methods

    def get_supported_types(self):
        prio = 1
        if self.error:
            prio = -1
        yield ("svn-cli-direct", prio * 4)
        yield ("svn-cli-remote", prio * 4)

    def get_repository(self, type, dir, params):
        """Return a `SubversionRepository`.

        The repository is wrapped in a `CachedRepository`
        """
        params.setdefault('eol_style', self.eol_style)
        try:
            repos = SubversionRepositoryCli(dir, params, self.log)
        except (TracError, AttributeError, TypeError):
            raise InvalidRepository("Repository for '%s' can't be loaded." % dir)
        return repos

    # ISystemInfoProvider method

    def get_system_info(self):
        """Yield a sequence of `(name, version)` tuples describing the
        name and version information of external packages used by a
        component.
        """
        yield 'Subversion', self._version + u' (svn client)'


class SubversionRepositoryCli(Repository):

    has_linear_changesets = True

    def __init__(self, path, params, log):
        """
        :param path: path to local subversion repo directory
        :param params:
        :param log: logger object
        """

        self.log = log
        self.base = path  # This is a path specified on the admin page

        # Disable repositories for testing
        # if params['name'] != 'trac-hacks':
        #     raise InvalidRepository("Ignoring %s" % params['name'])

        if params['type'] == 'svn-cli-direct':
            prefix = 'file:///' if os.name == 'nt' else 'file://'
            url = '%s%s' % (prefix, path)  # we may use http with svn later
        elif params['type'] == 'svn-cli-remote':
            if os.name == 'nt':
                url = path[3:].strip()
            else:
                url = path.lstrip('/ ')
        else:
            raise InvalidRepository("A repository of type '%s' is not supported." % params['type'])

        self.repo_url = url  # May be local or remote

        self.info = _get_svn_info(self, 'HEAD')
        if not self.info:
            raise InvalidRepository("Repository for '%s' can't be loaded." % self.repo_url)
        self.uuid = self.info['Repository UUID']

        name = 'svn-cli:%s:%s' % (self.uuid, path)
        Repository.__init__(self, name, params, log)

        # log.info("#### Init repo %s\n%s" % (params, self.info))

        # Note that we don't need to clear the cache. The repo will be deleted right after
        # showing files or displaying a directory tree.
        # Whenever a new subtree is opened a new repository is created with an empty cache.
        self._lock = RLock()
        self.rev_cache = {}
        # self.msg_len = 0  # For testing only
        self.clear()

    def clear(self, youngest_rev=None):
        """Reset notion of `youngest` and `oldest`"""
        self.youngest = None
        if youngest_rev is not None:
            self.youngest = self.normalize_rev(youngest_rev)
        self.oldest = None
        self._tzinfo = None

    def __del__(self):
        # self.log.info('+++++++++++++++++ %s %s' % (len(self.rev_cache), self.msg_len))
        self.close()

    def close(self):
        """Close the connection to the repository."""
        # self.log.info('## In close')
        pass

    @property
    def tzinfo(self):
        """Get a tzinfo from datetime information found in 'svn info ...'.

        :return: tzinfo object

        note that self.info must be available and populated. This is done in
        __init__().

        When getting the log from svn as xml the time information is in UTC.
        Converting to local time isn't trivial (you need locale, timezone,
        dst, whatever information to do it properly).

        So we use a localized time from 'svn info ...' to extract the proper
        timezone/offset and apply this offset to the xml time. We assume svn
        knows what it's doing here...

        Note that this may fail (?) for a repo without any checkins.
        """
        if not self._tzinfo:
            datestr = self.info['Last Changed Date']

            date = [x.strip() for x in datestr.partition('(')[0].split()]  # ['2021-03-07', '14:59:56', '+0100']
            dt = parse_datetime(u'{} {}{}'.format(*date))
            self._tzinfo = dt.tzinfo
        return self._tzinfo

    def get_rev_info(self, rev):
        """Get information about the given revision rev.

        :param rev: revision (int)
        :return: author, date, message

        This method uses 'svn log --xml ...' to query information about the
        changeset 'rev'.
        """
        # self.log.info('#### Query revision %s' % rev)
        with self._lock:
            try:
                rev_, author, date, msg = self.rev_cache[rev]
                return author, date, msg
            except KeyError:
                pass

        start_rev = rev - (rev % NUM_REV_INFO)
        end_rev = start_rev + NUM_REV_INFO - 1
        youngest = self.get_youngest_rev()
        if end_rev > youngest:
            end_rev = youngest

        cmd = ['svn', 'log', '--xml',
               '-r', '%s:%s' % (start_rev, end_rev),
               self.repo_url]
        ret = _call_svn_to_unicode(cmd)

        if ret:
            # With 'svn --xml' all datetimes are UTC.
            # We use timezone info to convert datetimes from UTC to local time.
            # handler = LogHandler(self.tzinfo)
            handler = LogHandler()
            try:
                parseString(ret.encode('utf-8'), handler)
            except UnicodeEncodeError:
                raise TracError('Internal unicode error with revision %s (num revs: %s)' %
                                (rev, NUM_REV_INFO))

            # get_log_entries(): [(rev, author, date, msg), ...]
            with self._lock:
                for item in handler.get_log_entries():
                    self.rev_cache[item[0]] = item
                    # self.log.info('  #### %s: %s' % (item[0], item))
                    # self.msg_len += len(item[3])
                try:
                    rev_, author, date, msg = self.rev_cache[rev]
                except KeyError as e:
                    self.log.info('###### Rev: %s can not be found ##############' % (rev,))
                    # print(cmd)
                    # for item in handler.get_log_entries():
                    #     print("%s: %s" % (item[0], item))
                    return '', datetime(1970, 1, 1, tzinfo=utc), ''
                return author, date, msg
        else:
            self.log.info('#### Changeset %s is broken' % rev)
            return '', datetime.now(utc), ''

    def get_path_history(self, path, rev=None, limit=None):
        self.log.info('## In get_path_history(%s, %s, %s) NOT IMPLEMENTED' %
                      (path, rev, limit))

    def get_changeset(self, rev):
        """Retrieve a Changeset corresponding to the given revision `rev`."""
        rev = self.normalize_rev(rev)
        return SubversionCliChangeset(self, rev)

    def get_node(self, path, rev=None):
        """Retrieve a Node from the repository at the given path.

        A Node represents a directory or a file at a given revision in the
        repository.
        If the `rev` parameter is specified, the Node corresponding to that
        revision is returned, otherwise the Node corresponding to the youngest
        revision is returned.
        """
        # self.log.info('  ## In get_node()')
        path = path or ''

        if path and path != '/' and path[-1] == '/':
            path = path[:-1]

        rev = self.normalize_rev(rev) or self.youngest_rev
        try:
            node = SubversionCliNode(self, path, rev, self.log)
        except NoSuchNode:
            self.log.debug('###########################################')
            self.log.debug('No Node for %s %s' % (path, rev))
            self.log.debug('###########################################')
            return None
        return node

    def get_oldest_rev(self):
        """Return the oldest revision stored in the repository."""
        # self.log.info('## In get_oldest_rev()')
        return 1

    def get_youngest_rev(self):
        """Return the youngest revision in the repository."""
        if not self.youngest:
            self.youngest =  int(self.info['Last Changed Rev'])
        # self.log.info('## In get_youngest_rev %s' % self.youngest)
        return self.youngest

    def previous_rev(self, rev, path=''):
        """Return the revision immediately preceding the specified revision.

        If `path` is given, filter out ancestor revisions having no changes
        below `path`.

        In presence of multiple parents, this follows the first parent.
        """
        # This is called for the context navigation when a file is shown in the
        # source browser.

        # Note. rev is unicode
        rev_ = int(rev)
        if not path:
            if rev_ > 1:
                # self.log.info('  ## In previous_rev with %s %s, returning: %s' %
                #              (rev, path, rev_ - 1))
                return rev_ - 1
        # This must be called with the previous *repo* revision here. Otherwise we get
        # the current revision again.
        return _svn_changerev(self, rev_ -1 , path)
        # self.log.info('## In previous_rev(%s, %s) NOT IMPLEMENTED' % (rev, path))

    def next_rev(self, rev, path=''):
        """Return the revision immediately following the specified revision.

        If `path` is given, filter out descendant revisions having no changes
        below `path`.

        In presence of multiple children, this follows the first child.
        """
        rev_ = int(rev)
        if not path:
            if rev_ < self.youngest:
                return rev_ + 1
        #return _svn_changerev(self, rev_ + 1, path)
        self.log.info('#### In next_rev(%s, %s) NOT IMPLEMENTED' % (rev, path))

    def rev_older_than(self, rev1, rev2):
        """Provides a total order over revisions.

        Return `True` if `rev1` is an ancestor of `rev2`.
        """
        return self.normalize_rev(rev1) < self.normalize_rev(rev2)

    def normalize_path(self, path):
        """Return a canonical representation of path in the repos."""
        # self.log.info('## In normalize_path "%s"' % path)
        return path

    def normalize_rev(self, rev):
        """Return a (unique) canonical representation of a revision.

        It's up to the backend to decide which string values of `rev`
        (usually provided by the user) should be accepted, and how they
        should be normalized. Some backends may for instance want to match
        against known tags or branch names.

        In addition, if `rev` is `None` or '', the youngest revision should
        be returned.

        :raise NoSuchChangeset: If the given `rev` isn't found.
        """
        # self.log.info('## In normalize_rev')
        if rev is None or isinstance(rev, basestring) and \
                rev.lower() in ('', 'head', 'latest', 'youngest'):
            return self.youngest_rev
        else:
            try:
                normrev = int(rev)
                if 0 <= normrev <= self.youngest_rev:
                    return normrev
                else:
                    self.log.debug("%r cannot be normalized in %s: out of [0, "
                                   "%r]", rev, self.reponame or '(default)',
                                   self.youngest_rev)
            except (ValueError, TypeError) as e:
                self.log.debug("%r cannot be normalized in %s: %s", rev,
                               self.reponame or '(default)',
                               exception_to_unicode(e))
            raise NoSuchChangeset(rev)

    def get_changes(self, old_path, old_rev, new_path, new_rev,
                    ignore_ancestry=1):
        """Generates changes corresponding to generalized diffs.

        Generator that yields change tuples (old_node, new_node, kind, change)
        for each node change between the two arbitrary (path,rev) pairs.

        The old_node is assumed to be None when the change is an ADD,
        the new_node is assumed to be None when the change is a DELETE.
        """
        self.log.info('## Repository ## In get_changes old: %s %s, new: %s %s' %
                      (old_path,old_rev, new_path, new_rev))
        old_rev = self.normalize_rev(old_rev)
        new_rev = self.normalize_rev(new_rev)

        old_node = self.get_node(old_path, old_rev)
        new_node = self.get_node(new_path, new_rev)

        if new_node.kind != old_node.kind:
            raise TracError(_('Diff mismatch: Base is a %(oldnode)s '
                              '(%(oldpath)s in revision %(oldrev)s) and '
                              'Target is a %(newnode)s (%(newpath)s in '
                              'revision %(newrev)s).', oldnode=old_node.kind,
                              oldpath=old_path, oldrev=old_rev,
                              newnode=new_node.kind, newpath=new_path,
                              newrev=new_rev))
        self.log.info('  ## old_node: %s %s, new_node: %s %s' %
                      (old_node, old_node.kind, new_node, new_node.kind))
        #if new_node.isdir:

        yield (old_node, new_node, Node.FILE, Changeset.EDIT)


class SubversionCliEmptyNode(Node):
    def __init__(self, repos, path, rev, log, file_info=None):

        self.log = log
        # This is used for creating the correct links on the changeset page
        self.created_path = path
        self.rev = rev
        self.repos = repos
        self.path = path
        self.size = 0
        self.kind = Node.FILE

        Node.__init__(self, repos, path, rev, self.kind)

        def get_content_length(self):
            return self.size


class SubversionCliNode(Node):

    def __init__(self, repos, path, rev, log, file_info=None):
        def set_node_data_from_file_info():
            self.created_rev = file_info[1]
            if file_info[0] == None:
                self.size = None
                self.kind = Node.DIRECTORY
            else:
                self.size = file_info[0]
                self.kind = Node.FILE

        self.log = log
        # This is used for creating the correct links on the changeset page
        self.created_path = path
        self.rev = rev
        self.repos = repos
        self.path = path
        self.size = None

        # self.log.info('## Node __init__(%s, %s, ..., %s' % (path, rev, file_info))
        if file_info:
            # We are coming from self.get_entries() with the following information:
            #
            # file_info[0]: size for file, None for directories
            # file_info[1]: change revision
            self.info = None
            set_node_data_from_file_info()
        else:
            if path == '/':
                self.kind = Node.DIRECTORY
                self.created_rev = 1
            else:
                # self.log.info('  ## Calling self.get_file_size_rev(), %s, %s' % (rev, path))
                # file_info[0]: size for file, None for directories
                # file_info[1]: change revision
                try:
                    # path_, file_info = self._list_path(True)[0]
                    self.size, self.created_rev = self.get_file_size_rev()
                except IndexError:
                    raise NoSuchNode(path, rev)
                # set_node_data_from_file_info()
                if self.size == None:
                    self.kind = Node.DIRECTORY
                else:
                    self.kind = Node.FILE
                # self.log.info('  ## after self._list_path(): size %s, created_rev %s, kind %s\n' %
                #                (self.size, self.created_rev, self.kind))
        # self.log.info('### Node init: %s %s' % (self.size, file_info))

        Node.__init__(self, repos, path, rev, self.kind)
        # log.info('  ## Init done for %s %s (%s)' % (path, rev, file_info))

    def get_content(self):
        """Return a stream for reading the content of the node.

        This method will return `None` for directories.
        The returned object must support a `read([len])` method.
        """
        if self.isdir:
            return None
        # self.log.info('## Node ## In get_content')
        return FileContentStream(self)

    def _get_youngest_rev_for_path_rev(self, rev, path):
        """Go down the history for path until the youngest revision is found
        which is equal or older than rev.

        Subversion repo rev may be higher than the current path. In that case
        commands fail when the repo revision is used. We try to find the nearest revision
        here.
        """
        pass

    def _list_path(self, from_node_init=False):
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
        # TODO: there is the same function in svn_client. Use that one.
        full_path = _create_path(self.repos.repo_url, self.path)
        cmd = ['svn', '--non-interactive',
               'list', '-v',
               '-r', str(self.rev),
               # _create_path(self.repos.repo_url, self.path)]
               # We need to add the revision to the path. Otherwise any path copied, moved or removed
               # in a younger revision won't be found by svn. See changeset 11183 in https://trac-hacks.org/svn
               _add_rev(full_path, self.rev)]

        ret = _call_svn_to_unicode(cmd)
        if not ret:
            cmd = cmd[:-1] + [full_path]
            print('  ++ svn \'list\' failed WITH ../path@rev. Now trying without @rev %s\n' % cmd)
            ret = _call_svn_to_unicode(cmd)
            # Slow workaround for problem with some changesets notavly 15264
            if not ret:
                print('    ++++++ Failed with @rev. now trying with copy data...')
                copied = get_copy_info(self.repos, self.repos.youngest_rev)
                for item, val in copied.items():
                    if self.path.startswith(item):
                        path = self.path.replace(item, val)
                        path = _add_rev(_create_path(self.repos.repo_url, path), self.rev)
                        cmd = cmd[:-1] + [path]
                        ret = _call_svn_to_unicode(cmd)
                        if not ret:
                            print('    ++++++ svn \'list\' failed again. Giving up... ++++++\n')
                            return []
                        break

        res = []
        changerev, name, size = 0, -1, -5
        for line in ret.split('\n'):
            parts = line.split()
            if parts:
                if parts[name] == './':
                    if from_node_init:
                        # If we are from init we want to know the revision for the path, not the contents
                        # If this is a directory path we end here.
                        return [(None, (None, int(parts[changerev])))]
                    else:
                        # When querying the contents we don't want to return this entry but only real
                        # entries
                        continue
                path = _create_path(self.path, parts[name])
                if path and path != '/':
                    path = path.rstrip('/')
                if parts[name].strip().endswith('/'):
                    # directory
                    res.append((path, (None, int(parts[changerev]))))
                else:
                    res.append((path, (int(parts[size]), int(parts[changerev]))))
        return res

    def get_file_size_rev(self):
        """Get size of file represented by this node using 'svn list'.

        :param path: a directory or file path
        :return file size or Npne for directories

        'file size' is 'None' for directories.

        'snv list ...' gives all the directory entries when called for a
        directory path. Information includes change revision and filesizes
        (among others we ignore here):
           11177 author               Jan 23  2012 ./
           11168 author           497 Jan 23  2012 __init__.py
           10057 author          4416 Jan 23  2012 admin.py

        For a file path the same information is given for the single file:
           11168 author           497 Jan 23  2012 __init__.py

        Note that this is usually called from __init__(). No information is yet
        available if this is a file or a directory.
        """
        # TODO: there is the same function in svn_client. Use that one.
        full_path = _create_path(self.repos.repo_url, self.path)
        cmd = ['svn', '--non-interactive',
               'list', '-v',
               '-r', str(self.rev),
               # _create_path(self.repos.repo_url, self.path)]
               # We need to add the revision to the path. Otherwise any path copied, moved or removed
               # in a younger revision won't be found by svn. See changeset 11183 in https://trac-hacks.org/svn
               _add_rev(full_path, self.rev)]

        ret = _call_svn_to_unicode(cmd)
        if not ret:
            self.log.info('  ++ svn \'list\' failed WITH ../path@rev. Now trying without @rev\n')
            cmd = cmd[:-1] + [full_path]
            ret = _call_svn_to_unicode(cmd)
            # Slow workaround for problem with some changesets notavly 15264
            if not ret:
                copied = get_copy_info(self.repos, self.repos.youngest_rev)
                self.log.info('    Failed with @rev. now trying with copy data...')
                for item, val in copied.items():
                    if self.path.startswith(item):
                        path = self.path.replace(item, val)
                        path = _add_rev(_create_path(self.repos.repo_url, path), self.rev)
                        cmd = cmd[:-1] + [path]
                        ret = _call_svn_to_unicode(cmd)
                        if not ret:
                            self.log.info('    ++++++ svn \'list\' failed again. Giving up... ++++++\n')
                            return []
                        break

        changerev, name, size = 0, -1, -5
        for line in ret.split('\n'):
            parts = line.split()
            if parts:
                if parts[name] == './':
                    # We want to know the size and revision for the path, not the contents.
                    # If this is a directory path we end here.
                    return None, int(parts[changerev])
                return int(parts[size]), int(parts[changerev])
        raise TracError("Can't get file size and revision.")

    def get_entries(self):
        """Generator that yields the immediate child entries of a directory.

        The entries are returned in no particular order.
        If the node is a file, this method returns `None`.
        """
        # self.log.info('## Node ## In get_entries')
        if self.isfile:
            return

        for entry in self._list_path():
            path, info = entry
            yield SubversionCliNode(self.repos, path, self.rev, self.log, info)
        return


    def get_history(self, limit=None):
        """Provide backward history for this Node.

        Generator that yields `(path, rev, chg)` tuples, one for each revision
        in which the node was changed. This generator will follow copies and
        moves of a node (if the underlying version control system supports
        that), which will be indicated by the first element of the tuple
        (i.e. the path) changing.
        Starts with an entry for the current revision.

        :param limit: if given, yield at most ``limit`` results.
        """
        # self.log.info('## Node ## In get_history(%s)' % limit)
        history = get_history(self.repos, self.created_rev, self.path, limit)
        for item in history:
            yield item

    def get_annotations(self):
        """Provide detailed backward history for the content of this Node.

        Retrieve an array of revisions, one `rev` for each line of content
        for that node.
        Only expected to work on (text) FILE nodes, of course.
        """
        if self.isdir:
            return []
        return get_blame_annotations(self.repos, self.rev, self.path)

    def get_properties(self):
        """Returns the properties (meta-data) of the node, as a dictionary.

        The set of properties depends on the version control system.
        """
        return get_properties_list(self.repos, self.rev, self.path)

    def get_content_length(self):
        """The length in bytes of the content.

        Will be `None` for a directory.
        """
        # self.log.info('## Node ## In get_content_length for %s rev %s, size %s' % (self.path, self.rev, self.size))
        if self.isfile:
            return self.size
        else:
            return

    def get_content_type(self):
        """The MIME type corresponding to the content, if known.

        Will be `None` for a directory.
        """
        if self.isdir:
            return None

        # self.log.info('## Node ## In get_content_type')
        return ''

    def get_last_modified(self):
        self.log.info('###### Node ## In get_last_modified() NOT IMPLEMENTED ######')

        return None


class SubversionCliChangeset(Changeset):

    def __init__(self, repos, rev):
        self.repos = repos
        self.log = repos.log
        self.rev = rev

        # repos.log.info('## Changeset Rev %s' % rev)
        author, date, message = repos.get_rev_info(rev)
        date = to_datetime(date)
        Changeset.__init__(self, repos, rev, message, author, date)

    def get_changes(self):
        """Generator that produces a tuple for every change in the changeset.

        The tuple will contain `(path, kind, change, base_path, base_rev)`,
        where `change` can be one of Changeset.ADD, Changeset.COPY,
        Changeset.DELETE, Changeset.EDIT or Changeset.MOVE,
        and `kind` is one of Node.FILE or Node.DIRECTORY.
        The `path` is the targeted path for the `change` (which is
        the ''deleted'' path  for a DELETE change).
        The `base_path` and `base_rev` are the source path and rev for the
        action (`None` and `-1` in the case of an ADD change).
        """
        # self.log.info('  ## Changeset get_changes()')

        prev_repo_rev = self.repos.previous_rev(self.rev)

        # TODO: Changeset.COPY is missing. Could be similar to MOVE but without a deleted
        # path.
        # We intentionally crash here when seeing them
        change_map = {'A': Changeset.ADD,
                      'D': Changeset.DELETE,
                      'M': Changeset.EDIT,
                      'R': 'replace'}
        changes, copied, deleted = get_changeset_info(self.repos, self.rev)
        # copied: ['copy/from/path/file', 'copy/from/file2', ...]
        # changes:
        # ({'action': u'M', 'text-mods': u'true', 'kind': u'file', 'copyfrom-rev': '',
        #   'copyfrom-path': ''},
        #   u'/.../.../tests/__init__.py')
        # ({'action': u'A', 'text-mods': u'true', 'kind': u'file', 'copyfrom-rev': u'11170',
        #   'copyfrom-path': u'/.../.../.../tests/web_ui.py'},
        #   u'/customfieldadminplugin/0.11/customfieldadmin/tests/admin.py')
        copied_dirs = {}
        for item in changes:
            attrs, path = item
            kind = Node.FILE if attrs['kind'] == u'file' else Node.DIRECTORY
            try:
                change = change_type = change_map[attrs['action']]
            except KeyError:
                change = change_type = 'UNKNOWN_CHANGE'

            base_path = path
            base_rev = prev_repo_rev
            if change_type in (Changeset.ADD):
                base_path = None
                base_rev = -1
                if attrs['copyfrom-path']:
                    # This is either a svn-move or svn-copy
                    if attrs['copyfrom-path'] in deleted:
                        change = Changeset.MOVE
                    else:
                        change = Changeset.COPY
                    base_path = attrs['copyfrom-path']
                    base_rev = int(attrs['copyfrom-rev'])
                    # We need the following info for copied files from a modified working copy
                    if attrs['kind'] == 'dir':
                        copied_dirs[path] = attrs['copyfrom-path']  # key: destination, value: source
            elif change_type == 'replace':
                if attrs['copyfrom-path'] in deleted:
                    change = Changeset.MOVE
                else:
                    change = Changeset.COPY
                base_path = attrs['copyfrom-path']
                base_rev = int(attrs['copyfrom-rev'])
            elif change_type == Changeset.DELETE:
                if path in copied:
                    # This is a source path for a svn-move operation
                    continue
                path = 'deleted'
            elif change_type == Changeset.EDIT:
                base_rev = _svn_changerev(self.repos, prev_repo_rev, path)
                if base_rev == None:
                    # We have some special file here. There is no older version in
                    # that path but the log doesn't show it a s copied/moved.
                    # It may have been edited in the working copy and afterwards the
                    # working copy was svn-copied (e.g. tagged.). This way we have
                    # a copied destination directory with an edited file,
                    #
                    # See changeset 18045 for an example
                    #
                    for key, val in copied_dirs.iteritems():
                        # key: destination dir path, val: source dir path
                        if path.startswith(key):
                            base_path = base_path.replace(key, val)
                            base_rev = _svn_changerev(self.repos, prev_repo_rev, base_path)
                            break
                    else:
                        base_rev = get_change_rev(self.repos, self.rev, path)
            else:
                self.log.info('## Changeset get_changes() self.rev: %s, prev: %s, %s ' %
                              (self.rev, prev_repo_rev, changes))
                self.log.info('  ## Unknown change for %s in rev %s' % (path, base_rev))
                path += u'UNKNOWN_CHANGE_FIX_NEEDED'
            yield path, kind, change, base_path, base_rev


# ############################################################### #
# Mostly taken from svn_fs.py (Trac 1.2)
class FileContentStream(object):

    KEYWORD_GROUPS = {
        'rev': ['LastChangedRevision', 'Rev', 'Revision'],
        'date': ['LastChangedDate', 'Date'],
        'author': ['LastChangedBy', 'Author'],
        'url': ['HeadURL', 'URL'],
        'id': ['Id'],
        'header': ['Header'],
        }
    KEYWORDS = reduce(set.union, map(set, KEYWORD_GROUPS.values()))
    KEYWORD_SPLIT_RE = re.compile(r'[ \t\v\n\b\r\f]+')
    KEYWORD_EXPAND_RE = re.compile(r'%[abdDPrRu_%HI]')
    NATIVE_EOL = '\r\n' if os.name == 'nt' else '\n'
    NEWLINES = {'LF': '\n', 'CRLF': '\r\n', 'CR': '\r', 'native': NATIVE_EOL}
    KEYWORD_MAX_SIZE = 255
    CHUNK_SIZE = 4096

    keywords_re = None
    native_eol = None
    newline = '\n'

    def __init__(self, node, keyword_substitution=None, eol=None):
        # node.repos.log.info('## Init FileStream for rev: %s, path: %s' % (node.rev, node.path))
        error_msg = """Revision %s: ERROR in SubversionCliRemote while loading content!"""
        self.translated = ''
        self.buffer = ''
        self.repos = node.repos
        self.node = node
        f_contents = get_file_content(node.repos, node.rev, node.path)
        try:
            self.stream = BytesIO(initial_bytes=bytes(f_contents))
        except UnicodeEncodeError as e:
            self.repos.log.info('#### ERROR for %s. Using empty textfile instead.' % node)
            self.stream = BytesIO(initial_bytes=bytes(error_msg % node.rev))
        # self.stream = BytesIO(initial_bytes=f_contents)

        # Note: we _must_ use a detached pool here, as the lifetime of
        # this object can exceed those of the node or even the repository
        if keyword_substitution:
            pass

        # if self.NEWLINES.get(eol, '\n') != '\n' and \
        #   node._get_prop(core.SVN_PROP_EOL_STYLE) == 'native':
        #    self.native_eol = True
        #    self.newline = self.NEWLINES[eol]
        # self.stream = core.Stream(fs.file_contents(node.root,
        #                                           node._scoped_path_utf8,
        #                                           self.pool()))

    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        self.stream = None
        # self.fs_ptr = None

    def read(self, n=None):
        if self.stream is None:
            raise ValueError('I/O operation on closed file')
        return self.stream.read(n)
        if self.keywords_re is None and not self.native_eol:
            return self._read_dumb(self.stream, n)
        else:
            return self._read_substitute(self.stream, n)

    def _get_revprop(self, name, rev):
        return None
        #return fs.revision_prop(self.fs_ptr, rev, name, self.pool())

    def _split_keywords(self, keywords):
        return filter(None, self.KEYWORD_SPLIT_RE.split(keywords or ''))

    def _get_keyword_values(self, keywords):
        keywords = self._split_keywords(keywords)
        if not keywords:
            return None

        node = self.node
        mtime = to_datetime(node.last_modified, utc)
        shortdate = self._format_shortdate(mtime)
        longdate = self._format_longdate(mtime)
        created_rev = unicode(node.created_rev)
        # Note that the `to_unicode` has a small probability to mess-up binary
        # properties, see #4321.
        #author = to_unicode(self._get_revprop(core.SVN_PROP_REVISION_AUTHOR,
        #                                      node.created_rev))
        # TODO: fix author
        author = u'The Author in _get_keyword_values'
        path = node.path.lstrip('/')
        url = node.repos.get_path_url(path, node.rev) or path
        root_url = node.repos.get_path_url('', node.rev) or '/'
        id_ = ' '.join((node.name, created_rev, shortdate, author))
        data = {
            'rev': created_rev, 'author': author, 'url': url, 'date': longdate,
            'id': id_,
            'header': ' '.join((url, created_rev, shortdate, author)),
            '%a': author, '%b': node.name, '%d': shortdate, '%D': longdate,
            '%P': path, '%r': created_rev, '%R': root_url, '%u': url,
            '%_': ' ', '%%': '%', '%I': id_,
            '%H': ' '.join((path, created_rev, shortdate, author)),
        }

        def expand(match):
            match = match.group(0)
            return data.get(match, match)

        values = {}
        for name, aliases in self.KEYWORD_GROUPS.iteritems():
            if any(kw in keywords for kw in aliases):
                values.update((kw, data[name]) for kw in aliases)
        for keyword in keywords:
            if '=' not in keyword:
                continue
            name, definition = keyword.split('=', 1)
            if name not in self.KEYWORDS:
                values[name] = self.KEYWORD_EXPAND_RE.sub(expand, definition)

        if values:
            return dict((key, to_utf8(value))
                        for key, value in values.iteritems())
        else:
            return None

    def _build_keywords_re(self, keywords):
        if keywords:
            return re.compile("""
                [$]
                (?P<keyword>%s)
                (?:
                    :[ ][^$\r\n]+?[ ]   |
                    ::[ ](?P<fixed>[^$\r\n]+?)[ #]
                )?
                [$]""" % '|'.join(map(re.escape, keywords)),
                re.VERBOSE)
        else:
            return None

    def _format_shortdate(self, mtime):
        return mtime.strftime('%Y-%m-%d %H:%M:%SZ')

    def _format_longdate(self, mtime):
        text = mtime.strftime('%Y-%m-%d %H:%M:%S +0000 (%%(a)s, %d %%(b)s %Y)')
        weekdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
        months = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
        return text % {'a': weekdays[mtime.weekday()],
                       'b': months[mtime.month - 1]}

    def _read_dumb(self, stream, n):
        return stream.read(n)

    def _read_substitute(self, stream, n):
        if n is None:
            n = -1

        buffer = self.buffer
        translated = self.translated
        while True:
            if 0 <= n <= len(translated):
                self.buffer = buffer
                self.translated = translated[n:]
                return translated[:n]

            if len(buffer) < self.KEYWORD_MAX_SIZE:
                buffer += stream.read(self.CHUNK_SIZE) or ''
                if not buffer:
                    self.buffer = buffer
                    self.translated = ''
                    return translated

            # search first "$" character
            pos = buffer.find('$') if self.keywords_re else -1
            if pos == -1:
                translated += self._translate_newline(buffer)
                buffer = ''
                continue
            if pos > 0:
                # move to the first "$" character
                translated += self._translate_newline(buffer[:pos])
                buffer = buffer[pos:]

            match = None
            while True:
                # search second "$" character
                pos = buffer.find('$', 1)
                if pos == -1:
                    translated += self._translate_newline(buffer)
                    buffer = ''
                    break
                if pos < self.KEYWORD_MAX_SIZE:
                    match = self.keywords_re.match(buffer)
                    if match:
                        break  # found "$Keyword$" in the first 255 bytes
                # move to the second "$" character
                translated += self._translate_newline(buffer[:pos])
                buffer = buffer[pos:]
            if pos == -1 or not match:
                continue

            # move to the next character of the second "$" character
            pos += 1
            translated += self._translate_keyword(buffer[:pos], match)
            buffer = buffer[pos:]
            continue

    def _translate_newline(self, data):
        if self.native_eol:
            data = data.replace('\n', self.newline)
        return data

    def _translate_keyword(self, text, match):
        keyword = match.group('keyword')
        value = self.keywords.get(keyword)
        if value is None:
            return text
        fixed = match.group('fixed')
        if fixed is None:
            n = self.KEYWORD_MAX_SIZE - len(keyword) - 5
            return '$%s: %.*s $' % (keyword, n, value) if n >= 0 else text
        else:
            n = len(fixed)
            return '$%s:: %-*.*s%s$' % \
                   (keyword, n, n, value, '#' if n < len(value) else ' ')

