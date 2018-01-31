# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.db.schema import Table, Column, Index

schema = [
    Table('backlink', key='id')[
        Column('id', type='int64', auto_increment=True),
        Column('time', type='int64'),
        Column('author'),
        Column('ref_realm', size=30),
        Column('ref_id'),
        Column('ref_parent_realm', size=30),
        Column('ref_parent_id'),
        Column('src_realm', size=30),
        Column('src_id'),
        Column('src_parent_realm', size=30),
        Column('src_parent_id'),
        Index(('ref_realm', 'ref_id')),
        Index(('ref_parent_realm', 'ref_parent_id')),
        Index(('src_realm', 'src_id')),
        Index(('src_parent_realm', 'src_parent_id')),
    ],
]
