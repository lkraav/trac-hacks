from trac.db import Table, Column, Index, DatabaseManager


new_table = Table('cards', key='id')[
    Column('id', auto_increment=True),
    Column('stack'),
    Column('rank', type='int64'),
    Column('title'),
    Column('color'),
    Index(['stack', 'rank']),
]


def do_upgrade(env, ver, cursor):
    DatabaseManager(env).upgrade_tables([new_table])
