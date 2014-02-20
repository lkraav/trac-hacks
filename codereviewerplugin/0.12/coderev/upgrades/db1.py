from trac.db import Table, Column, Index, DatabaseManager

def do_upgrade(env, cursor):

    db_tables = [
        Table('codereviewer')[
            Column('repo', type='text'),
            Column('changeset', type='text'),
            Column('status', type='text'),
            Column('reviewer', type='text'),
            Column('summary', type='text'),
            Column('time', type='integer'),
            Index(columns=['repo', 'changeset', 'time']),
        ],
    ]

    # create the initial table (and index)
    db_connector = DatabaseManager(env).get_connector()[0]
    for table in db_tables:
        for sql in db_connector.to_sql(table):
            cursor.execute(sql)
