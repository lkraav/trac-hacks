from trac.db import Table, Column, Index, DatabaseManager


new_table = Table('cards_stacks', key='name')[
        Column('name'),
        Column('version', type='int64'),
    ]


def do_upgrade(env, ver, cursor):
    DatabaseManager(env).create_tables([new_table])
