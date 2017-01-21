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
        Column('large_file'),
        Column('medium_file'),
        Column('small_file'),
        Column('component'),
        Column('version')
    ]
]


def do_upgrade(env, version, cursor):
    dbm = DatabaseManager(env)
    dbm.create_tables(tables)
    dbm.set_database_version(version, db_version_key)
