from trac.db import Table, Column, Index, DatabaseManager


new_table = Table('cards_stacks', key='name')[
        Column('name'),
        Column('version', type='int64'),
    ]


def do_upgrade(env, ver, cursor):
    connector, _ = DatabaseManager(env)._get_connector()
    for stmt in connector.to_sql(new_table):
        cursor.execute(stmt)
