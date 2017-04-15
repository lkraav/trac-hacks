# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2006-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.db import *
from trac.env import IEnvironmentSetupParticipant

# Current discussion database schema version.
schema_version = 5


class DiscussionInit(Component):
    """[main] Initialises database and environment for discussion storage."""

    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self):
        schema_ver = self._get_schema_version()
        if schema_ver == schema_version:
            return False
        elif schema_ver > schema_version:
            raise TracError("A newer plugin version has been installed "
                            "before, but downgrading is unsupported.")
        self.log.info("TracDiscussion database schema version is %d, "
                      "should be %d", schema_ver, schema_version)
        return True

    def upgrade_environment(self):
        """Each schema version should have its own upgrade module, named
        upgrades/dbN.py, where 'N' is the version number (int).
        """
        schema_ver = self._get_schema_version()

        with self.env.db_transaction as db:
            cursor = db.cursor()
            # Always perform incremental upgrades.
            for i in range(schema_ver + 1, schema_version + 1):
                script_name = 'db%i' % i
                try:
                    upgrades = __import__('tracdiscussion.db', globals(),
                                          locals(), [script_name])
                    script = getattr(upgrades, script_name)
                except AttributeError:
                    raise TracError("No upgrade module for version %s "
                                    "(%s.py)" % (i, script_name))
                script.do_upgrade(self.env, cursor)

            self.log.info("Upgraded TracDiscussion db schema from version "
                          "%d to %d", schema_ver, schema_version)

    # Internal methods

    def _get_schema_version(self):
        """Return the current schema version for this plugin."""
        for version, in self.env.db_query("""
                SELECT value FROM system WHERE name='discussion_version'
                """):
            return int(version)
        return 0
