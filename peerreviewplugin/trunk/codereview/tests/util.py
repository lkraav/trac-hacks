# -*- coding: utf-8 -*-
# Copyright (c) 2019 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from codereview.model import ReviewFileModel
from datetime import datetime
from trac.util.datefmt import to_datetime, to_utimestamp


def prepare_review_data(env):
    # owner, status, created, name, notes, parent_id
    revs = [
        ['Rev1', 'bar', to_utimestamp(to_datetime(datetime(2019, 2, 4))), 'name1', 'note1', 0],
        ['Rev1', 'closed', to_utimestamp(to_datetime(datetime(2019, 3, 4))), 'name2', 'note2', 0],  # review_id = 2
        ['Rev2', 'bar', to_utimestamp(to_datetime(datetime(2019, 3, 14))), 'name3', 'note3', 1],
        ['Rev3', 'foo', to_utimestamp(to_datetime(datetime(2019, 4, 4))), 'name4', 'note4', 2]
    ]

    with env.db_transaction as db:
        cursor = db.cursor()
        for rev in revs:
            cursor.execute("INSERT INTO peerreview (owner, status, created, name, notes, parent_id) "
                           "VALUES (%s,%s,%s,%s,%s,%s)", rev)


def prepare_file_data(env):
    # review_id, path, start, end, revision, status
    files = [
        [1, '/foo/bar', 5, 100, '1234', 'new', None, 'repo1'],  # file_id = 1
        [1, '/foo/bar/2', 6, 101, '1234', 'new', None, 'repo1'],  # file_id = 2
        [2, '/foo/bar/3', 5, 100, '1234', 'closed', None, 'repo1'],  # file_id = 3. Belongs to closed review
        [2, '/foo/bar', 6, 101, '12346', 'closed', None, 'repo1'],
        [2, '/foo/bar3', 7, 102, '12347', 'closed', None, 'repo1'],
        [3, '/foo/bar2', 6, 101, '1234', 'new', None, 'repo1'],
        [4, '/foo/bar', 5, 100, '1234', 'new', None, 'repo1'],
        [4, '/foo/bar2', 6, 101, '1234', 'new', None, 'repo1'],
        # File list data for several projects
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar2', 6, 101, '12346', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar3', 7, 102, '12347', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar/baz', 6, 101, '1234', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBaz', 'repo1'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjBaz', 'repo1'],
    ]
    for f in files:
        rfm = ReviewFileModel(env)
        rfm['review_id'] = f[0]
        rfm['path'] = f[1]
        rfm['line_start'] = f[2]
        rfm['line_end'] = f[3]
        rfm['revision'] = f[4]
        rfm['status'] = f[5]
        rfm['project'] = f[6]
        rfm['repo'] = f[7]
        rfm.insert()


def prepare_comments(env):
    # file_id, parent_id, line_num, author, created, comment
    comments = [[1, -1, 123, 'user1', to_utimestamp(to_datetime(datetime(2019, 2, 4))), 'Comment 1'],
                [1, 1, 123, 'user4', to_utimestamp(to_datetime(datetime(2019, 2, 5))), 'Comment 2'],
                [2, -1, 12, 'user1', to_utimestamp(to_datetime(datetime(2019, 2, 5))), 'Comment 3'],
                [2, -1, 13, 'user2', to_utimestamp(to_datetime(datetime(2019, 2, 6))), 'Comment 4'],
                [2, 4, 13, 'user3', to_utimestamp(to_datetime(datetime(2019, 2, 7))), 'Comment 5'],
                [3, -1, 15, 'user3', to_utimestamp(to_datetime(datetime(2019, 2, 8))), 'Comment 6'],  # closed review
                [3, -1, 16, 'user4', to_utimestamp(to_datetime(datetime(2019, 2, 9))), 'Comment 7'],
    ]
    with env.db_transaction as db:
        cursor = db.cursor()
        for comm in comments:
            cursor.execute("INSERT INTO peerreviewcomment (file_id, parent_id, line_num, author, created, comment) "
                           "VALUES (%s,%s,%s,%s,%s,%s)", comm)
