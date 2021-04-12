# -*- coding: utf-8 -*-
"""
TracFullBlogPlugin: The code managing the database setup and upgrades.

License: BSD

(c) 2007 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from trac.core import *
from trac.db.api import DatabaseManager
from trac.db.schema import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant

# Database version identifier for upgrades.
db_version = 2
db_version_key = 'fullblog_version'

# Database schema
schema = [
    # Blog posts
    Table('fullblog_posts', key=('name', 'version'))[
        Column('name'),
        Column('version', type='int'),
        Column('title'),
        Column('body'),
        Column('publish_time', type='int'),
        Column('version_time', type='int'),
        Column('version_comment'),
        Column('version_author'),
        Column('author'),
        Column('categories'),
        Index(['version_time'])],
    # Blog comments
    Table('fullblog_comments', key=('name', 'number'))[
        Column('name'),
        Column('number', type='int'),
        Column('comment'),
        Column('author'),
        Column('time', type='int'),
        Index(['time'])],
]

# Upgrades

def add_timeline_time_indexes(env):
    """ Add time-based indexes to blog post and comment tables. """
    with env.db_transaction as db:
        db("""
           CREATE INDEX fullblog_comments_time_idx
           ON fullblog_comments (time)
           """)
        db("""
           CREATE INDEX fullblog_posts_version_time_idx
           ON fullblog_posts (version_time)
           """)

upgrade_map = {
        2: add_timeline_time_indexes
    }


class FullBlogSetup(Component):
    """Component that deals with database setup and upgrades."""

    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        return DatabaseManager(self.env). \
                needs_upgrade(db_version, db_version_key)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        if dbm.get_database_version(db_version_key) == 0:
            dbm.create_tables(schema)
            with self.env.db_transaction as db:
                db("INSERT into system values ('fullblog_infotext', '')")
        else:
            with self.env.db_transaction as db:
                current_ver = 1
                while current_ver + 1 <= db_version:
                    upgrade_map[current_ver + 1](self.env)
                    current_ver += 1
        dbm.set_database_version(db_version, db_version_key)
