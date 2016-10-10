# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2016 Philippe Normand <phil@base-art.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import svn.client
import svn.core
import svn.fs
import svn.repos
import libsvn
import os
import tempfile


class SVNHelper:

    def __init__(self, repository_path):

        try:
            pool = svn.core.application_pool
        except AttributeError:
            # cope with old python subversion bindings
            pool = libsvn.core.svn_pool_create(None)

        repos_ptr = svn.repos.svn_repos_open(repository_path, pool)
        self.fs_ptr = svn.repos.svn_repos_fs(repos_ptr)
        self.pool = pool
        self.repository_path = repository_path

    def _rev2optrev(self, rev):
        assert type(rev) is int
        rt = svn.core.svn_opt_revision_t()
        rt.kind = svn.core.svn_opt_revision_number
        rt.value.number = rev
        return rt

    def get_youngest(self):
        youngest = svn.fs.youngest_rev(self.fs_ptr, self.pool)
        return youngest

    def cat(self, path, rev=None):
        """dump the contents of a file"""
        if not rev:
            rev = self.get_youngest()
        contents = ''
        fs_ptr = self.fs_ptr
        taskpool = self.pool
        root = svn.fs.revision_root(fs_ptr, rev, taskpool)
        if not len(path):
            print "You must supply a file path."
            return contents
        kind = svn.fs.check_path(root, path, taskpool)
        if kind == svn.core.svn_node_none:
            print "Path '%s' does not exist." % path
            return contents
        if kind == svn.core.svn_node_dir:
            print "Path '%s' is not a file." % path
            return contents

        client_ctx = svn.client.svn_client_create_context(self.pool)
        path = 'file://' + self.repository_path + path
        fd, f = tempfile.mkstemp()
        rev = self._rev2optrev(rev)

        stream_t = svn.core.svn_stream_from_aprfile(f, self.pool)
        stream = svn.core.Stream(stream_t)
        try:
            svn.client.svn_client_cat(stream, path, rev, client_ctx, self.pool)
        except Exception, ex:
            stream = stream_t
            svn.client.svn_client_cat(stream, path, rev, client_ctx, self.pool)

        contents = open(f).read()
        os.unlink(f)
        return contents

    def cached_cat(self, file_path, cache_dir, rev=None):

        if not rev:
            rev = self.get_youngest()

        base = file_path[1:].replace(os.path.sep, '_')
        cache_file_path = os.path.join(cache_dir, "%s.%s" % (base, rev))
        previous = os.path.join(cache_dir, "%s.%s" % (base, rev-1))

        if os.path.exists(cache_file_path):
            # get cached data
            data = open(cache_file_path).read()

            # delete previous version
            if os.path.exists(previous):
                os.unlink(previous)
        else:
            # fill the bloody cache
            data = self.cat(file_path, rev)
            f = open(cache_file_path, 'w')
            f.write(data)
            f.close()

        return data
