# Copyright 2010-2011, 2014 Stefan Goebel - <tracsecdl -at- subtype -dot- de>
#
# This file is part of TracSecDl.
#
# TracSecDl is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# TracSecDl is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# TracSecDl. If not, see <http://www.gnu.org/licenses/>.

from trac.core import Component, implements
from trac.env  import IEnvironmentSetupParticipant

class SecDlEnv (Component):

    """Environment setup stuff."""

    implements (IEnvironmentSetupParticipant)

    # This needs to be incremented on every database update:
    _secdl_db_version = 1

    # IEnvironmentSetupParticipant methods:

    def environment_created (self):
        """Performs a database initialization on environment creation."""
        db = self.env.get_db_cnx ()
        return self._upgrade_environment (db)

    def environment_needs_upgrade (self, db):
        """Returns True if the database is out of date."""
        return self._get_version (db) != self._secdl_db_version

    def upgrade_environment (self, db):
        """Called when an environment is upgraded."""
        return self._upgrade_environment (db)

    def _upgrade_environment (self, db):
        """Perform the environment upgrade for TracSecDl.

        The database setup scripts are located in the database folder, named
        'database_<version>.py', <version> being the (two digit) version number
        for the script (eg. the setup script for the first version of the
        database is called 'database_01.py'). On version updates new scripts
        must be provided - named accordingly - that perform all necessary
        actions to update the database from the previous version. All scripts
        will be run in correct order, but skipping all scripts for previous
        database versions. All scripts must make sure that no data is lost!
        """
        version = self._get_version (db)
        cursor  = db.cursor ()
        for i in range (version + 1, self._secdl_db_version + 1):
            script_name = 'database_%02i' % i
            module = __import__ (
                    'tracsecdl.database.%s' % script_name,
                    globals (),
                    locals (),
                    ['do_upgrade']
                )
            module.do_upgrade (self.env, db, cursor)

    def _get_version (self, db):
        """Returns the current TracSecDl database version.

        The current version is stored in the 'system' table, the key being
        'secdl_version'. Exceptions will not be handled but passed on to the
        caller instead.
        """
        cursor = db.cursor ()
        try:
            query = 'SELECT value FROM system WHERE name=%s'
            cursor.execute (query, ['secdl_version'])
            for row in cursor:
                return int (row [0])
            return 0
        except:
            raise

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: