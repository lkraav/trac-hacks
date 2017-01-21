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
        Column('file'),
        Column('width', type='integer'),
        Column('height', type='integer'),
        Column('priority', type='integer')
    ],
]


def do_upgrade(env, version, cursor):
    dbm = DatabaseManager(env)
    dbm.upgrade_tables(tables)
    dbm.set_database_version(version, db_version_key)
