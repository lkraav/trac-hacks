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

    wf_data = [['review', 'new -> reviewed'],
               ['review.name', 'Mark as reviewed'],
               ['approve', 'reviewed -> approved'],
               ['approve.name', 'Approve the review'],
               ['disapprove', 'reviewed -> disapproved'],
               ['disapprove.name', 'Deny this review'],
               ['close', 'new, reviewed -> closed'],
               ['close.name', 'Close review'],
               ['reopen', 'closed, reviewed -> new'],
               ['reopen.permissions', 'CODE_REVIEW_MGR'],
               ]
    wf_section = 'peerreview-resource_workflow'

    if wf_section not in env.config.sections():
        print "Adding default workflow for 'peerreview' to config."
        for item in wf_data:
            env.config.set(wf_section, item[0], item[1])
        env.config.save()