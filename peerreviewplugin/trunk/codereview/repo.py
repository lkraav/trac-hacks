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
from trac.versioncontrol.api import RepositoryManager, NoSuchNode
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


def get_nodes_for_dir(repos, dir_node, nodes, ignore_ext):

    for node in dir_node.get_entries():
        if node.isdir:
            get_nodes_for_dir(repos, node, nodes, ignore_ext)
        else:
            if os.path.splitext(node.path)[1].lower() not in ignore_ext:
                nodes.append({
                    'path': node.path,
                    'rev': node.rev,
                    'change_rev':node.created_rev,
                    'hash': hash_from_file_node(node)
                })


def insert_project_files(env, src_path, project, ignore_ext, rev=None):

    repos = RepositoryManager(env).get_repository('')
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
                           "VALUES (0, %s, 0, 0, '', %s, %s, %s, %s)",
                           (item['path'], item['rev'], item['change_rev'], item['hash'], project))
