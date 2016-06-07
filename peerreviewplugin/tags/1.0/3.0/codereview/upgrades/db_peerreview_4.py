from trac.db import Table, Column

def do_upgrade(env, ver, db_backend, db):
    """
    Change primary key.
    """
    cursor = db.cursor()

    realm = 'peerreview'

    cursor.execute("CREATE TEMPORARY TABLE peerreview_old AS SELECT * FROM peerreview")
    cursor.execute("DROP TABLE peerreview")

    table_metadata = Table('peerreview', key=('review_id', 'owner', 'status'))[
                              Column('review_id', auto_increment=True, type='int'),
                              Column('owner'),
                              Column('status'),
                              Column('created', type='int'),
                              Column('name'),
                              Column('notes'),
                              Column('parent_id', type='int'),
                              Column('project'),
                              Column('keywords')
                              ]

    env.log.info("Updating table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO peerreview "
                   "(review_id,owner,status,created,name,notes,parent_id,project,keywords) "
                   "SELECT review_id,owner,status,created,name,notes,parent_id,project,keywords FROM peerreview_old")

    cursor.execute("DROP TABLE peerreview_old")

