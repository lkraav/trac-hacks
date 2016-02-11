from trac.db import Table, Column, Index, DatabaseManager


def do_upgrade(env, ver, db_backend, db):
    """

    """
    cursor = db.cursor()

    realm = 'peerreviewfile'

    cursor.execute("CREATE TEMPORARY TABLE peerreviewer_old AS SELECT * FROM peer_reviewer")
    cursor.execute("DROP TABLE peer_reviewer")

    table_metadata = Table('peerreviewer', key=('reviewer_id', 'reviewer'))[
                              Column('reviewer_id', auto_increment=True, type='int'),
                              Column('review_id', type='int'),
                              Column('reviewer'),
                              Column('status'),
                              Column('vote', type='int')
                              ]

    env.log.info("Updating table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO peerreviewer (review_id,reviewer,status,vote) "
                   "SELECT review_id,reviewer,status,vote FROM peerreviewer_old")
    cursor.execute("UPDATE peerreviewer SET status= 'new' WHERE status=0")
    cursor.execute("DROP TABLE peerreviewer_old")

    # Add default workflow

    wf_data = [['reviewing', 'new -> in-review'],
               ['review_done', 'in-review -> reviewed'],
               ['reopen', 'in-review, reviewed -> new']]
    wf_section = 'peerreviewer-resource_workflow'

    if 'peer-review_' not in env.config.sections():
        print "Adding default workflow for 'peerreviewer' to config."
        for item in wf_data:
            env.config.set(wf_section, item[0], item[1])
        env.config.save()