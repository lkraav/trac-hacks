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


def get_nodes_for_dir(repo, dir_node, nodes, ignore_ext):
    """Get file nodes recursively for a given directory node.

    :param repo: the repository holding the nodes
    :param dir_node: a trac directory node
    :param nodes: list of nodes. Found file nodes will be appended.
    :param ignore_ext: list of file extensions to be ignored
    :return:
    """
    for node in dir_node.get_entries():
        if node.isdir:
            get_nodes_for_dir(repo, node, nodes, ignore_ext)
        else:
            if os.path.splitext(node.path)[1].lower() not in ignore_ext:
                nodes.append({
                    'path': node.path,
                    'rev': node.rev,
                    'change_rev':node.created_rev,
                    'hash': hash_from_file_node(node)
                })


def file_data_from_repo(node):

    dat = ''
    content = node.get_content()
    res = content.read()
    while res:
        dat += res
        res = content.read()
    return dat.splitlines()


def insert_project_files(env, src_path, project, ignore_ext, rev=None, reponame=''):
    """Add project files to the database.

    :param env: Trac environment object
    :param src_path
    """
    repos = RepositoryManager(env).get_repository(reponame)
    if not repos:
        return

    if rev:
        rev = repos.normalize_rev(rev)
    rev_or_latest = rev or repos.youngest_rev

    root_node = get_node(repos, src_path, rev_or_latest)

    nodes = []
    if root_node.isdir:
        get_nodes_for_dir(repos, root_node, nodes, ignore_ext)

    ReviewFileModel.delete_files_by_project_name(env, project)
    @env.with_transaction()
    def insert_data(db):
        cursor = db.cursor()
        for item in nodes:
            cursor.execute("INSERT INTO peerreviewfile"
                           "(review_id,path,line_start,line_end,repo,revision, changerevision,hash,project)"
                           "VALUES (0, %s, 0, 0, %s, %s, %s, %s, %s)",
                           (item['path'], reponame, item['rev'], item['change_rev'], item['hash'], project))
