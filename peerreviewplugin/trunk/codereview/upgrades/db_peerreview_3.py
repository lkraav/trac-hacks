from trac.db import Table, Column

def do_upgrade(env, ver, db_backend, db):
    """
    Add 'page_version' column to testcaseinplan table
    """
    cursor = db.cursor()

    realm = 'peerreview'

    status_update = [["new", "Open for review"],
                     ["reviewed", "Reviewed"],
                     ["closed", "Closed"],
                     ["forinclusion", "Ready for inclusion"]]

    for status in status_update:
        cursor.execute("UPDATE peer_review SET status=%s WHERE status=%s", status)

    cursor.execute("CREATE TEMPORARY TABLE peerreview_old AS SELECT * FROM peer_review")
    cursor.execute("DROP TABLE peer_review")

    table_metadata = Table('peerreview', key='review_id')[
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

    cursor.execute("INSERT INTO peerreview (review_id,owner,status,created,name,notes,parent_id,keywords) "
                   "SELECT review_id,owner,status,created,name,notes,parent_id,keywords FROM peerreview_old")

    cursor.execute("DROP TABLE peerreview_old")

    # Add default workflow

    wf_data = [['reviewing', 'new -> in-review'],
               ['reviewing.name', 'Start review'],
               ['review_done', 'in-review -> reviewed'],
               ['review_done.name', 'Mark review as done.'],
               ['reopen', 'in-review, reviewed -> new'],
               ['reopen.name', "Reset review state to 'new'"],
               ]
    wf_section = 'peerreviewer-resource_workflow'

    if wf_section not in env.config.sections():
        print "Adding default workflow for 'peerreviewer' to config."
        for item in wf_data:
            env.config.set(wf_section, item[0], item[1])
        env.config.save()