# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#

import hashlib
import os
import posixpath
from trac.versioncontrol.api import NoSuchNode, RepositoryManager
from .model import ReviewFileModel

__author__ = 'Cinc'
__license__ = "BSD"


def hash_from_file_node(node):
    content = node.get_content()
    blocksize = 4096
    hasher = hashlib.sha256()

    buf = content.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = content.read(blocksize)
    return hasher.hexdigest()


def repo_path_exists(env, path, reponame=''):
    repos = RepositoryManager(env).get_repository(reponame)
    if not repos:
        return False

    rev = repos.youngest_rev
    try:
        node = repos.get_node(path, rev)
        return node.isdir
    except NoSuchNode as e:
        return False


def get_node(repos, path, rev):
    try:
        return repos.get_node(path, rev)
    except NoSuchNode as e:
        return None

from svn_externals import parse_externals


def get_nodes_for_dir(self, repodict, dir_node, fnodes, ignore_ext, incl_ext, excl_path, follow_ext, repo_name=''):
    """Get file nodes recursively for a given directory node.

    :param env: Trac environment object
    :param repodict: dict holding info about known repositories
    :param dir_node: a trac directory node
    :param fnodes: list of file info nodes. Info for found files will be appended.
    :param ignore_ext: list of file extensions to be ignored
    :param follow_ext: if True follow externals to folders in the same or another repository

    :return errors: list of errors. Empty list if no errors occurred.
    """
    if not self._externals_map:
        for dummykey, value in self.external_map_section.options():
            value = value.split()
            if len(value) != 3:
                self.log.warn("peerreview:repomap entry %s doesn't contain "
                              "a space-separated list of three items, "
                              "skipping.", dummykey)
                continue
            key, value, repo = value
            self._externals_map[key] = [value, repo]

    env = self.env
    errors = []
    for node in dir_node.get_entries():
        if node.isdir:
            errors += get_nodes_for_dir(self, repodict, node, fnodes, ignore_ext, incl_ext, excl_path, follow_ext,
                                        repo_name)
            if follow_ext:
                props = node.get_properties()
                try:
                    for external in parse_externals(props['svn:externals']):
                        try:
                            # Create a valid paths from externals information. The path may point to virtual
                            # repositories.
                            base_url = external['url']
                            while base_url:
                                if base_url in self._externals_map or base_url == u'/':
                                    break
                                base_url, pref = posixpath.split(base_url)
                            # base_url is the path head of the external
                            ext_info = self._externals_map.get(base_url)
                            file_path = repos = reponame = None
                            if ext_info:
                                file_path, reponame = ext_info
                                file_path = file_path + external['url'][len(base_url):]
                                repos = repodict[reponame]['repo']

                            if file_path:
                                rev = external['rev']
                                if rev:
                                    rev = repos.normalize_rev(rev)
                                rev_or_latest = rev or repos.youngest_rev
                                ext_node = get_node(repos, file_path, rev_or_latest)
                            else:
                                ext_node = None

                            if ext_node and ext_node.isdir:
                                errors += get_nodes_for_dir(self, repodict, ext_node, fnodes, ignore_ext, incl_ext,
                                                            excl_path, follow_ext, reponame)
                            else:
                                txt = "No node for external path '%s' in repository '%s'. " \
                                      "External: '%s %s' was ignored for directory '%s'." \
                                      % (file_path, reponame, external['url'], external['dir'], node.name)
                                env.log.warning(txt)
                                errors.append(txt)
                        except KeyError:  # Missing data in dictionary e.g. we try to use an unnamed repository
                            txt = "External: '%s %s' was ignored for directory '%s'." %\
                                  (external['url'], external['dir'], node.name)
                            env.log.warning(txt)
                            errors.append(txt)
                except KeyError:  # property has no svn:externals
                    pass
        else:
            for p in excl_path:
                if node.path.startswith(p):
                    break
            else:
                if incl_ext:
                    if os.path.splitext(node.path)[1].lower() in incl_ext:
                        fnodes.append({
                            'path': node.path,
                            'rev': node.rev,
                            'change_rev':node.created_rev,
                            'hash': hash_from_file_node(node),
                            'reponame': repo_name
                        })
                else:
                    if os.path.splitext(node.path)[1].lower() not in ignore_ext:
                        fnodes.append({
                            'path': node.path,
                            'rev': node.rev,
                            'change_rev':node.created_rev,
                            'hash': hash_from_file_node(node),
                            'reponame': repo_name
                        })
    return errors


def file_data_from_repo(node, keyword_substitution=False):

    if not node:
        return u''

    dat = u''
    if keyword_substitution:
        content = node.get_processed_content()
    else:
        content = node.get_content()
    res = content.read()
    while res:
        dat += res.decode('utf-8')  # We assume 'utf-8' here. In fact it may be anything.
        res = content.read()
    return dat.splitlines()


def get_repository_dict(env):
    """Get a dict with information about all repositories.

    :param env: Trac environment object
    :return: dict with key = reponame, value = dict with information about repository.

    The information about a repository is queried using ''get_all_repositories'' from
    RepositoryManager.
    - For any real repository (that means not an alias) the Repository object
      is inserted into the dictionary using the key 'repo'.
    - For any real repository (that means not an alias) a prefix is calculated from the url info
      and inserted using the key 'prefix'. This prefix is used to build paths into the repository.

    """
    repoman = RepositoryManager(env)

    repolist = repoman.get_all_repositories()  # repolist is a dict with key = reponame, val = dict
    for repo in repoman.get_real_repositories():
        repolist[repo.reponame]['repo'] = repoman.get_repository(repo.reponame)
        # We need the last part of the path later when following externals
        try:
            repolist[repo.reponame]['prefix'] = '/' + os.path.basename(repolist[repo.reponame]['url'].rstrip('/'))
        except KeyError:
            repolist[repo.reponame]['prefix'] = ''
    return repolist


def insert_project_files(self, src_path, project, ignore_ext, incl_ext, excl_path,
                         follow_ext=False, rev=None, repo_name=''):
    """Add project files to the database.

    :param self: Trac component object
    :param src_path
    """
    repolist = get_repository_dict(self.env)
    try:
        repos = repolist[repo_name]['repo']
    except KeyError:
        return

    if not repos:
        return

    if rev:
        rev = repos.normalize_rev(rev)
    rev_or_latest = rev or repos.youngest_rev

    root_node = get_node(repos, src_path, rev_or_latest)

    fnodes = []
    if root_node.isdir:
        errors = get_nodes_for_dir(self, repolist, root_node, fnodes, ignore_ext, incl_ext, excl_path, follow_ext,
                                   repo_name)
    else:
        errors = []

    ReviewFileModel.delete_files_by_project_name(self.env, project)
    with self.env.db_transaction as db:
        cursor = db.cursor()
        for item in fnodes:
            cursor.execute("INSERT INTO peerreviewfile"
                           "(review_id,path,line_start,line_end,repo,revision, changerevision,hash,project)"
                           "VALUES (0, %s, 0, 0, %s, %s, %s, %s, %s)",
                           (item['path'], item['reponame'], item['rev'], item['change_rev'], item['hash'], project))

    return errors, len(fnodes)
