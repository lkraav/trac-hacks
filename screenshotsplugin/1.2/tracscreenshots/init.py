# -*- coding: utf-8 -*-

import os

from trac.core import Component, implements
from trac.config import PathOption
from trac.db import Column, DatabaseManager, Table
from trac.env import IEnvironmentSetupParticipant

from tracscreenshots.core import _

last_db_version = 4
db_version_key = 'screenshots_version'

tables = [
    Table('screenshot', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('name'),
        Column('description'),
        Column('time', type='integer'),
        Column('author'),
        Column('tags'),
        Column('file'),
        Column('width', type='integer'),
        Column('height', type='integer'),
        Column('priority', type='integer')
    ],
    Table('screenshot_component', key = 'id')[
        Column('id', type='integer', auto_increment=True),
        Column('screenshot', type='integer'),
        Column('component')
    ],
    Table('screenshot_version', key = 'id')[
        Column('id', type='integer', auto_increment=True),
        Column('screenshot', type='integer'),
        Column('version')
    ]
]


class ScreenshotsInit(Component):
    """Initialises database and environment for screenshots plugin.
    """
    implements(IEnvironmentSetupParticipant)

    # Configuration options.
    path = PathOption('screenshots', 'path', '../screenshots',
                      doc=_("Path where to store uploaded screenshots."))

    # IEnvironmentSetupParticipant

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(last_db_version, db_version_key)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)

        # Create screenshots directory if not exists.
        if not os.path.isdir(self.path):
            os.mkdir(os.path.normpath(self.path))

        # Is this clean installation?
        db_version = dbm.get_database_version(db_version_key)
        if db_version == 0:
            dbm.create_tables(tables)
            dbm.set_database_version(last_db_version, db_version_key)

        dbm.upgrade(last_db_version, db_version_key, 'tracscreenshots.db')
