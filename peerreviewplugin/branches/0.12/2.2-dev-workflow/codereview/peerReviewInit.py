#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.util.text import _

db_name_old = 'codereview_version'  # for database version 1
db_name = 'peerreview_version'
db_version = 2

class PeerReviewInit(Component):
    """ Initialise database and environment for codereview plugin """
    implements(IEnvironmentSetupParticipant)

    current_db_version = 0

    # IEnvironmentSetupParticipant
    def environment_created(self):
        self.current_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        self.current_db_version = self._get_version(db.cursor())

        if self.current_db_version < db_version:
            self.log.info("PeerReview plugin database schema version is %d, should be %d",
                          self.current_db_version, db_version)
            return True
        if self.current_db_version > db_version:
            raise TracError(_("Database newer than PeerReview plugin version"))
        return False

    def upgrade_environment(self, db):
        # 0.10 compatibility hack (thanks Alec)
        try:
            from trac.db import DatabaseManager
            db_manager = DatabaseManager(self.env)._get_connector()[0]
        except ImportError:
            db_manager = db

        return

        # Insert the default table
        cursor = db.cursor()
        for i in range(self.current_db_version + 1, db_version + 1):
            name = 'db%i' % i
            print "PeerReview: running upgrade ", name
            try:
                upgrades = __import__('upgrades', globals(), locals(), [name])
                script = getattr(upgrades, name)
            except AttributeError:
                raise TracError(_("No PeerReview upgrade module %(num)i "
                                  "(%(version)s.py)", num=i, version=name))
            script.do_upgrade(self.env, i, cursor)

            self._set_version(cursor, i)
            db.commit()

        return

    def _get_version(self, cursor):
        cursor.execute("SELECT value FROM system WHERE name = %s", (db_name_old,))
        value = cursor.fetchone()
        val = int(value[0]) if value else 0
        if not val:
            # Database version > 1 or no datavase yet
            cursor.execute("SELECT value FROM system WHERE name = %s", (db_name,))
            value = cursor.fetchone()
            val = int(value[0]) if value else 0
        return val

    def _set_version(self, cursor, cur_ver):
        if not self.current_db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",
                           (db_name, cur_ver))
        else:
            cursor.execute("UPDATE system SET value = %s WHERE name = %s",
                           (db_version, db_name))
            if cursor.rowcount == 0:
                cursor.execute("INSERT INTO system (name,value) VALUES (%s,%s)",
                               (db_name, db_version))
        self.current_db_version = cur_ver