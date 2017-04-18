# Copyright 2010-2011, 2014 Stefan Goebel - <tracsecdl -at- subtype -dot- de>
#
# This file is part of TracSecDl.
#
# TracSecDl is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# TracSecDl is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# TracSecDl. If not, see <http://www.gnu.org/licenses/>.

from trac.db import Table, Column, Index, DatabaseManager

"""Performs a database upgrade.

The do_upgrade() function will upgrade the environment's TracSecDl specific
database stuff to version 1. This is the initial version. Do not change this
script on database updates, create a new one according to the new database
version that performs an incremental update instead.
"""

# Prefix to use for the table names to avoid name clashes with other plugins.
# If you change the prefix here you also need to change it in model/base.py!

prefix = 'sdl_'

# The tables used by TracSecDl, one for the downloads, and one for each of the
# architectures, platforms and types. The components, milestones and versions
# are provided by Trac's ticket system:

tables = [

    Table (prefix + 'download', key = 'id') [
        Column ('id',           type = 'integer', auto_increment = True),
        Column ('name'                                                 ),
        Column ('url',                                                 ),
        Column ('description'                                          ),
        Column ('size',         type = 'integer'                       ),
        Column ('time',         type = 'integer'                       ),
        Column ('last_request', type = 'integer'                       ),
        Column ('count',        type = 'integer'                       ),
        Column ('author'                                               ),
        Column ('ip',           type = 'bigint'                        ),
        Column ('component'                                            ),
        Column ('milestone'                                            ),
        Column ('version'                                              ),
        Column ('architecture', type = 'integer'                       ),
        Column ('platform',     type = 'integer'                       ),
        Column ('type',         type = 'integer'                       ),
        Column ('hidden',       type = 'integer'                       ),
        Column ('checksum_md5',                                        ),
        Column ('checksum_sha'                                         ),
    ],

    Table (prefix + 'architecture', key = 'id') [
        Column ('id',           type = 'integer', auto_increment = True),
        Column ('name'                                                 ),
        Column ('description'                                          ),
        Index  (['name'],                         unique = True        ),
    ],

    Table (prefix + 'platform', key = 'id') [
        Column ('id',           type = 'integer', auto_increment = True),
        Column ('name'                                                 ),
        Column ('description'                                          ),
        Index  (['name'],                         unique = True        ),
    ],

    Table (prefix + 'type', key = 'id') [
        Column ('id',           type = 'integer', auto_increment = True),
        Column ('name'                                                 ),
        Column ('description'                                          ),
        Index  (['name'],                         unique = True        ),
    ]

]

def do_upgrade (env, db, cursor):

    """Upgrade TracSecDl specific database stuff to this script's version.

    DB version 1: * create all required tables
                  * insert the db version into the system table
                  * store a default description in the system table
    """

    db_backend, _ = DatabaseManager (env)._get_connector ()

    try:
        for table in tables:
            for statement in db_backend.to_sql (table):
                cursor.execute (statement)
        cursor.execute (
                'INSERT INTO system (name, value) VALUES (%s, %s)',
                ('secdl_version', '1')
            )
        cursor.execute (
                'INSERT INTO system (name, value) VALUES (%s, %s)',
                ('secdl_description', 'Available downloads:')
            )
        db.commit ()
    except:
        raise

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: