from trac.db import Table, Column, Index, DatabaseManager

# Split estimates into separate table.

new_tables = [
    Table('timetrackingtasks', key='id')[
        Column('id', auto_increment=True),
        Column('name'),
        Column('description'),
        Column('project'),
        Column('category'),
        Column('year', type='int'),
        Index(['year', 'category', 'project']),
    ],
    Table('timetrackingestimates', key=('task_id', 'name'))[
        Column('task_id', type='int'),
        Column('name'),
        Column('comment'),
        Column('estimated_hours', type='int'),
    ]
]


def do_upgrade(env, ver, cursor):
    cursor.execute("CREATE TEMPORARY TABLE timetrackingtasks_old AS SELECT * FROM timetrackingtasks")
    cursor.execute("DROP TABLE timetrackingtasks")
    
    connector, _ = DatabaseManager(env)._get_connector()
    for new_table in new_tables:
        for stmt in connector.to_sql(new_table):
            cursor.execute(stmt)

    cursor.execute("""
        INSERT INTO timetrackingtasks (id, name, description, project, category, year)
        SELECT o.id, o.name, o.description, o.project, o.category, o.year
        FROM timetrackingtasks_old o
        """)
    cursor.execute("""
        INSERT INTO timetrackingestimates (task_id, name, comment, estimated_hours)
        SELECT o.id, 'final', o.comment, o.estimated_hours
        FROM timetrackingtasks_old o
        """)
    cursor.execute("DROP TABLE timetrackingtasks_old")
