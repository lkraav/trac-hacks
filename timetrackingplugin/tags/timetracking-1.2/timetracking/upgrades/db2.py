from trac.db import Table, Column, Index, DatabaseManager


new_table = Table('timetrackingtasks', key='id')[
        Column('id', auto_increment=True),
        Column('name'),
        Column('description'),
        Column('project'),
        Column('category'),
        Column('year', type='int'),
        Column('estimated_hours', type='int'),
        Index(['year', 'category', 'project']),
    ]


def do_upgrade(env, ver, cursor):
    cursor.execute("CREATE TEMPORARY TABLE timetrackingtasks_old AS SELECT * FROM timetrackingtasks")
    cursor.execute("DROP TABLE timetrackingtasks")

    DatabaseManager(env).create_tables([new_table])

    cursor.execute("""
        INSERT INTO timetrackingtasks (id, name, description, project, category, year, estimated_hours)
        SELECT o.id, o.name, o.description, o.project, o.category, 2014, o.estimated_hours
        FROM timetrackingtasks_old o
        """)
    cursor.execute("DROP TABLE timetrackingtasks_old")
