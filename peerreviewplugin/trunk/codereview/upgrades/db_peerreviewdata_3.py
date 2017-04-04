from trac.db import Table, Column, Index

def do_upgrade(env, ver, db_backend, db):
    """
    Change primary key to a sane default.
    """
    cursor = db.cursor()

    realm = 'peerreview'

    cursor.execute("CREATE TEMPORARY TABLE peerreviewdata_old AS SELECT * FROM peerreviewdata")
    cursor.execute("DROP TABLE peerreviewdata")

    table_metadata = Table('peerreviewdata', key=('data_id'))[
                              Column('data_id', auto_increment=True, type='int'),
                              Column('review_id', type='int'),
                              Column('comment_id', type='int'),
                              Column('file_id', type='int'),
                              Column('reviewer_id', type='int'),
                              Column('type'),
                              Column('data'),
                              Column('owner'),
                              Column('data_key'),
                              Index(['review_id']),
                              Index(['comment_id']),
                              Index(['file_id'])
                              ]

    env.log.info("Updating table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO peerreviewdata "
                   "(data_id,review_id,comment_id,file_id,reviewer_id, type, data,owner, data_key) "
                   "SELECT data_id,review_id,comment_id,file_id,reviewer_id,type,data,owner,data_key "
                   "FROM peerreviewdata_old")

    cursor.execute("DROP TABLE peerreviewdata_old")
