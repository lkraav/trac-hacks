from trac.db import Table, Column, Index, DatabaseManager


def do_upgrade(env, ver, db_backend, db):
    """

    """
    cursor = db.cursor()

    realm = 'peerreviewfile'

    cursor.execute("CREATE TEMPORARY TABLE peerreviewfile_old AS SELECT * FROM peerreviewfile")
    cursor.execute("DROP TABLE peerreviewfile")

    table_metadata = Table('peerreviewfile', key=('file_id', 'hash', 'project', 'review_id', 'status'))[
                              Column('file_id', auto_increment=True, type='int'),
                              Column('review_id', type='int'),
                              Column('path'),
                              Column('line_start', type='int'),
                              Column('line_end', type='int'),
                              Column('repo'),
                              Column('revision'),
                              Column('changerevision'),
                              Column('hash'),
                              Column('status'),
                              Column('project')]

    env.log.info("Updating table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO peerreviewfile "
                   "(file_id,review_id,path,line_start,line_end,repo,revision,changerevision,hash,status, project) "
                   "SELECT file_id,review_id,path,line_start,line_end,repo,revision,changerevision,hash,status, '' "
                   "FROM peerreviewfile_old")

    cursor.execute("DROP TABLE peerreviewfile_old")