from trac.db import Table, Column, Index

def do_upgrade(env, ver, db_backend, db):
    """Change back primary key modified in version 4 to a more sane default.
    Create index.
    """
    cursor = db.cursor()

    realm = 'peerreview'

    cursor.execute("CREATE TEMPORARY TABLE peerreview_old AS SELECT * FROM peerreview")
    cursor.execute("DROP TABLE peerreview")

    table_metadata = Table('peerreview', key=('review_id'))[
                              Column('review_id', auto_increment=True, type='int'),
                              Column('owner'),
                              Column('status'),
                              Column('created', type='int'),
                              Column('closed', type='int'),
                              Column('name'),
                              Column('notes'),
                              Column('parent_id', type='int'),
                              Column('project'),
                              Column('keywords'),
                              Index(['owner']),
                              Index(['status'])
                              ]

    env.log.info("Updating table of class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO peerreview "
                   "(review_id,owner,status,created,closed,name,notes,parent_id,project,keywords) "
                   "SELECT review_id,owner,status,created,closed,name,notes,parent_id,project,keywords "
                   "FROM peerreview_old")

    cursor.execute("DROP TABLE peerreview_old")
