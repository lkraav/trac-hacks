from trac.db import Table, Column, Index, DatabaseManager

# Add an additional column "comment" to the task table.
# When upgrading the old existing rows:
#   put the old "description" string in this new "comment" column.
#   put the empty string into the "description" column.

new_table = Table('timetrackingtasks', key='id')[
        Column('id', auto_increment=True),
        Column('name'),
        Column('description'),
        Column('comment'),
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
        INSERT INTO timetrackingtasks (id, name, description, comment, project, category, year, estimated_hours)
        SELECT o.id, o.name, '', o.description, o.project, o.category, o.year, o.estimated_hours
        FROM timetrackingtasks_old o
        """)
    cursor.execute("DROP TABLE timetrackingtasks_old")
