from trac.db import Table, Column, Index, DatabaseManager


def do_upgrade(env, ver, db_backend, db):
    """

    """
    cursor = db.cursor()

    realm = 'peerreviewcomment'

    cursor.execute("CREATE TEMPORARY TABLE peerreviewcomment_old AS SELECT * FROM peer_review_comment")
    cursor.execute("DROP TABLE peer_review_comment")

    table_metadata = Table('peerreviewcomment', key='comment_id')[
                              Column('comment_id', auto_increment=True, type='int'),
                              Column('file_id', type='int'),
                              Column('parent_id', type='int'),
                              Column('line_num', type='int'),
                              Column('author'),
                              Column('comment'),
                              Column('attachment_path'),
                              Column('created', type='int'),
                              Column('refs'),
                              Column('type'),
                              Column('status')]

    env.log.info("Updating table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO peerreviewcomment "
                   "(comment_id,file_id,parent_id,line_num,author,comment,attachment_path,created) "
                   "SELECT comment_id,file_id,parent_id,line_num,author,comment,attachment_path,created "
                   "FROM peerreviewcomment_old")

    cursor.execute("DROP TABLE peerreviewcomment_old")
