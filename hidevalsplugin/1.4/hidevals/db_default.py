# -*- coding: utf-8 -*-
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.db.schema import Column, Table

name = 'hidevals'
version = 1
tables = [
    Table('hidevals', key=('sid', 'field', 'value'))[
        Column('sid'),
        Column('field'),
        Column('value'),
    ],
]
