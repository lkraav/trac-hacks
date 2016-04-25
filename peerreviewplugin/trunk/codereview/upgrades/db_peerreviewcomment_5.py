from trac.db import Table, Column, Index, DatabaseManager


def do_upgrade(env, ver, db_backend, db):
    """Change 'created' from seconds to microseconds."""
    cursor = db.cursor()

    realm = 'peerreviewcomment'

    cursor.execute("CREATE TEMPORARY TABLE peerreviewcomment_old AS SELECT * FROM peerreviewcomment")
    cursor.execute("DROP TABLE peerreviewcomment")

    table_metadata = Table('peerreviewcomment', key=('comment_id', 'file_id', 'author'))[
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

    env.log.info("Updating table values for 'created' of class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO peerreviewcomment "
                   "(comment_id,file_id,parent_id,line_num,author,comment,attachment_path,created,refs,type,status) "
                   "SELECT comment_id,file_id,parent_id,line_num,author,comment,attachment_path,created * 1000000,refs,type,status "
                   "FROM peerreviewcomment_old")

    cursor.execute("DROP TABLE peerreviewcomment_old")