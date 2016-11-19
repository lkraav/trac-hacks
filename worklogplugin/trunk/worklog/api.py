# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2012 Colin Guthrie <trac@colin.guthr.ie>
# Copyright (c) 2011-2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from datetime import datetime

from trac.core import *
from trac.db import Column, DatabaseManager, Table
from trac.env import IEnvironmentSetupParticipant
from trac.util.datefmt import to_utimestamp, utc

from usermanual import *
try:
    from xmlrpc import *
except:
    pass

schema = [
    Table('work_log')[
        Column('worker'),
        Column('comment'),
        Column('ticket', type='int'),
        Column('lastchange', type='int'),
        Column('starttime', type='int'),
        Column('endtime', type='int'),
    ]
]


class WorkLogSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    db_version_key = 'WorklogPlugin_Db_Version'
    db_version = 3
    db_installed_version = None

    def __init__(self):
        self.db_installed_version = self._get_db_version()

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        with self.env.db_transaction as db:
            self.upgrade_environment(db)

    def environment_needs_upgrade(self, db):
        return self._system_needs_upgrade() or self._needs_user_man()

    def upgrade_environment(self, db):
        print "Worklog needs an upgrade"
        with self.env.db_transaction:
            if self._system_needs_upgrade():
                print " * Upgrading Database"
                self._do_db_upgrade(db)
            if self._needs_user_man():
                print " * Upgrading usermanual"
                self._do_user_man_update()
            print "Done upgrading Worklog"

    # Internal methods

    def _system_needs_upgrade(self):
        return self.db_installed_version < self.db_version

    def _do_db_upgrade(self, db):
        with self.env.db_transaction as db:
            skip = False
            if self.db_installed_version < 1:
                print 'Creating work_log table'
                self._create_tables(schema)
                skip = True

            if self.db_installed_version < 2:
                if not skip:
                    print 'Updating work_log table (v2)'
                    db("ALTER TABLE work_log ADD COLUMN comment TEXT")

            if self.db_installed_version < 3:
                if not skip:
                    print 'Updating work_log table (v3)'
                    # Rename 'user' column to 'worker', to support psql
                    db("""
                        CREATE TABLE work_log_tmp
                         (worker TEXT, comment TEXT, ticket INTEGER,
                          lastchange INTEGER, starttime INTEGER,
                          endtime INTEGER)
                        """)
                    db("""
                        INSERT INTO work_log_tmp
                          (worker,comment,ticket,lastchange,starttime,
                           endtime,comment)
                        SELECT user,comment, ticket,lastchange,starttime,
                               endtime,comment
                        FROM work_log
                        """)
                    db("DROP TABLE work_log")
                    db("ALTER TABLE work_log_tmp RENAME TO work_log")

            db("UPDATE system SET value=%s WHERE name=%s",
                (self.db_version, self.db_version_key))

    def _needs_user_man(self):
        for maxversion, in self.env.db_transaction("""
                SELECT MAX(version) FROM wiki WHERE name=%s
                """, (user_manual_wiki_title,)):
            maxversion = int(maxversion) if maxversion else 0
            break
        else:
            maxversion = 0

        return maxversion < user_manual_version

    def _do_user_man_update(self):
        when = to_utimestamp(datetime.now(utc))
        self.env.db_transaction("""
                INSERT INTO wiki
                  (name,version,time,author,ipnr,text,comment,readonly)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (user_manual_wiki_title, user_manual_version,
                      when, 'WorkLog Plugin', '127.0.0.1',
                      user_manual_content, '', 0))

    def _get_db_version(self):
        with self.env.db_transaction as db:
            for version, in db("""
                    SELECT value FROM system WHERE name=%s
                    """, (self.db_version_key,)):
                version = int(version)
                break
            else:
                version = 0
                db("""
                    INSERT INTO system (name,value) VALUES(%s,%s)
                    """, (self.db_version_key, version))
        return version

    def _create_tables(self, schema):
        connector = DatabaseManager(self.env).get_connector()[0]
        with self.env.db_transaction as db:
            for table in schema:
                for sql in connector.to_sql(table):
                    db(sql)
