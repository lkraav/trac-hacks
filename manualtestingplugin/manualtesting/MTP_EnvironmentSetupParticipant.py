# ManualTesting.MTP_EnvironmentSetupParticipant

from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant


# Database schema variables
db_version_key = 'manualtesting_version'
db_version_value = 1
db_installed_version_value = 0

"""
Extension point interface for components that need to participate in the
creation and upgrading of Trac environments, for example to create
additional database tables."""
class MTP_EnvironmentSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    """
    Called when a new Trac environment is created."""
    def environment_created(self):
        # Initialise database schema version tracking.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (db_version_key,))
        try:
            db_installed_version_value = int( cursor.fetchone()[0] )
        except:
            db_installed_version_value = 0
            cursor.execute("INSERT INTO system (name,value) VALUES(%s,%s)", (db_version_key, db_version_value) )
            db.commit()
            db.close()
        print "ManualTestingPlugin database version %s initialized." % db_version_value


    """
    Called when Trac checks whether the environment needs to be upgraded.
    Should return `True` if this participant needs an upgrade to be
    performed, `False` otherwise."""
    def environment_needs_upgrade(self, db):
        needsUpgrade = (db_installed_version_value < db_version_value)
        print "ManualTesting needs upgrade: %s" % needsUpgrade
        return needsUpgrade


    """
    Actually perform an environment upgrade.
    Implementations of this method should not commit any database
    transactions. This is done implicitly after all participants have
    performed the upgrades they need without an error being raised."""
    def upgrade_environment(self, db):
        cursor = db.cursor()
        dbImportModuleName = ('DBSchema_version_%s' % db_version_value)
        DB_module = __import__(dbImportModuleName, globals(), locals(), ['do_upgrade'])
        DB_module.do_upgrade(self.env, cursor)