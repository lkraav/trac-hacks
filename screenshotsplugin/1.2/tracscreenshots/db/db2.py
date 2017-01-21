# -*- coding: utf-8 -*-

from trac.db import Column, DatabaseManager, Table

from tracscreenshots.init import db_version_key

tables = [
    Table('screenshot', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('name'),
        Column('description'),
        Column('time', type='integer'),
        Column('author'),
        Column('tags'),
        Column('large_file'),
        Column('medium_file'),
        Column('small_file'),
    ],
    Table('screenshot_component', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('screenshot', type='integer'),
        Column('component')
    ],
    Table('screenshot_version', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('screenshot', type='integer'),
        Column('version')
    ]
]


def do_upgrade(env, version, cursor):
    dbm = DatabaseManager(env)
    dbm.create_tables(tables[1:])
    dbm.upgrade_tables([tables[0]])
    dbm.set_database_version(version, db_version_key)
