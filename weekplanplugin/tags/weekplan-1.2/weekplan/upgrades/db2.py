from trac.db import Table, Column, Index, DatabaseManager

new_table = Table('weekplan', key='id')[
        Column('id', auto_increment=True),
        Column('plan'),
        Column('title'),
        Column('start', type='int64'),
        Column('end', type='int64'),
        Index(['plan', 'start', 'end']),
    ]


def do_upgrade(env, ver, cursor):
    cursor.execute("CREATE TEMPORARY TABLE weekplan_old AS SELECT * FROM weekplan")
    cursor.execute("DROP TABLE weekplan")
    
    connector, _ = DatabaseManager(env)._get_connector()
    for stmt in connector.to_sql(new_table):
        cursor.execute(stmt)

    # Round start and end to full days (integer division is truncate, so add half a day to get rounding instead)
    # Add one day to end as this is now "exclusive"
    cursor.execute("""
        INSERT INTO weekplan (id, plan, title, start, end)
        SELECT o.id, o.plan, o.title,
            ((o.start + 12*60*60*1000*1000)/(24*60*60*1000*1000))*(24*60*60*1000*1000),
            ((o.end   + 12*60*60*1000*1000)/(24*60*60*1000*1000)+1)*(24*60*60*1000*1000)
        FROM weekplan_old o
        """)
    cursor.execute("DROP TABLE weekplan_old")
