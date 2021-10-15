def revert_schema(env):
    with env.db_transaction as db:
        for table in ('smp_project', 'smp_milestone_project',
                      'smp_version_project', 'smp_component_project'):
            db("DROP TABLE IF EXISTS %s" % db.quote(table))
        db("DELETE FROM system WHERE name='simplemultiproject_version'")

