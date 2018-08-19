from trac.db import Table, Column, Index, DatabaseManager


def do_upgrade(env, ver, db_backend, db):
    """
    Change primary key to sane default.
    """
    cursor = db.cursor()

    realm = 'peerreviewfile'

    cursor.execute("CREATE TEMPORARY TABLE peerreviewer_old AS SELECT * FROM peerreviewer")
    cursor.execute("DROP TABLE peerreviewer")

    table_metadata = Table('peerreviewer', key=('reviewer_id'))[
                              Column('reviewer_id', auto_increment=True, type='int'),
                              Column('review_id', type='int'),
                              Column('reviewer'),
                              Column('status'),
                              Column('vote', type='int'),
                              Index(['reviewer']),
                              Index(['review_id'])
                              ]

    env.log.info("Updating table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO peerreviewer (reviewer_id,review_id,reviewer,status,vote) "
                   "SELECT reviewer_id,review_id,reviewer,status,vote FROM peerreviewer_old")
    cursor.execute("DROP TABLE peerreviewer_old")
