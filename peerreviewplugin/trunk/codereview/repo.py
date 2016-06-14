# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#

import hashlib
import os
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
    except NoSuchNode, e:
        return False


def get_node(repos, path, rev):
    try:
        return repos.get_node(path, rev)
    except NoSuchNode, e:
        return None

from svn_externals import parse_externals


def get_nodes_for_dir(env, repodict, dir_node, fnodes, ignore_ext, follow_ext):
    """Get file nodes recursively for a given directory node.

    :param env: Trac environment object
    :param repodict: dict holding info about known repositories
    :param dir_node: a trac directory node
    :param fnodes: list of file info nodes. Info for found files will be appended.
    :param ignore_ext: list of file extensions to be ignored
    :param follow_ext: if True follow externals to folders in the same or another repository

    :return errors: list of errors. Empty list if no errors occurred.
    """
    errors = []
    for node in dir_node.get_entries():
        if node.isdir:
            errors += get_nodes_for_dir(env, repodict, node, fnodes, ignore_ext, follow_ext)
            if follow_ext:
                props = node.get_properties()
                try:
                    for external in parse_externals(props['svn:externals']):
                        try:

                            # list of lists. First item is len of common prefix, second is repository object
                            len_common = []
                            for key, val in repodict.iteritems():
                                try:
                                    len_common.append([len(os.path.commonprefix([external['url'], val['url']])),
                                                       val['repo']])
                                except KeyError:
                                    pass
                            len_common.sort(reverse=True)
                            # First item in list is repo holding the external path because it has the longest
                            # common prefix
                            repos = len_common[0][1]
                            repo_path = repodict[repos.reponame]['prefix'] + '/' + \
                                external['url'][len_common[0][0]:].lstrip('/')
                            ext_node = get_node(repos, repo_path, external['rev'])
                            if ext_node:
                                errors += get_nodes_for_dir(env, repodict, ext_node, fnodes, ignore_ext, follow_ext)
                            else:
                                txt = "No node for external path '%s' in repository '%s'. " \
                                      "External: '%s %s' was ignored for directory '%s'." \
                                      % (repo_path, repos.reponame, external['url'], external['dir'], node.name)
                                env.log.warning(txt)
                                errors.append(txt)
                        except KeyError:  # Missing data in dictionary e.g. we try to use aan unnamed repository
                            txt = "External: '%s %s' was ignored for directory '%s'." %\
                                  (external['url'], external['dir'], node.name)
                            env.log.warning(txt)
                            errors.append(txt)
                except KeyError:  # property has no svn:externals
                    pass
        else:
            if os.path.splitext(node.path)[1].lower() not in ignore_ext:
                fnodes.append({
                    'path': node.path,
                    'rev': node.rev,
                    'change_rev':node.created_rev,
                    'hash': hash_from_file_node(node)
                })
    return errors


def file_data_from_repo(node):

    dat = ''
    content = node.get_content()
    res = content.read()
    while res:
        dat += res
        res = content.read()
    return dat.splitlines()


def insert_project_files(self, src_path, project, ignore_ext, follow_ext=False, rev=None, reponame=''):
    """Add project files to the database.

    :param self: Trac component object
    :param src_path
    """
    repoman = RepositoryManager(self.env)
    repos = repoman.get_repository(reponame)
    if not repos:
        return

    repolist = repoman.get_all_repositories()  # repolist is a dict with key = reponame, val = dict
    for repo in repoman.get_real_repositories():
        repolist[repo.reponame]['repo'] = repoman.get_repository(repo.reponame)
        # We need the last part of the path later when following externals
        try:
            repolist[repo.reponame]['prefix'] = '/' + os.path.basename(repolist[repo.reponame]['url'].rstrip('/'))
        except KeyError:
            repolist[repo.reponame]['prefix'] = ''

    if rev:
        rev = repos.normalize_rev(rev)
    rev_or_latest = rev or repos.youngest_rev

    root_node = get_node(repos, src_path, rev_or_latest)

    fnodes = []
    if root_node.isdir:
        errors = get_nodes_for_dir(self.env, repolist, root_node, fnodes, ignore_ext, follow_ext)
    else:
        errors = []

    ReviewFileModel.delete_files_by_project_name(self.env, project)
    @self.env.with_transaction()
    def insert_data(db):
        cursor = db.cursor()
        for item in fnodes:
            cursor.execute("INSERT INTO peerreviewfile"
                           "(review_id,path,line_start,line_end,repo,revision, changerevision,hash,project)"
                           "VALUES (0, %s, 0, 0, %s, %s, %s, %s, %s)",
                           (item['path'], reponame, item['rev'], item['change_rev'], item['hash'], project))

    return errors, len(fnodes)
