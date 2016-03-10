# Copyright (C) 2009, 2012 John Szakmeister
# All rights reserved.
#
# This software is licensed as described in the file LICENSE.txt, which
# you should have received as part of this distribution.

from trac.db import Table, Column, Index


# The version of the database schema
schema_version = 1

# The database schema for the multiprojectbacklog module
schema = [
  Table('mp_backlog', key='ticket_id')[
    Column('ticket_id', type='int'),
    Column('rank', type='int'),
    Column('project', type='text'),
    Index(['ticket_id'], unique=True),
    Index(['project']),
  ]
]

