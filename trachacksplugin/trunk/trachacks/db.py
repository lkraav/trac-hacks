# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Trac-Hacks.org
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import pkg_resources

from trac.core import Component, TracError, implements
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import _
from trac.wiki.admin import WikiAdmin

PLUGIN_NAME = 'trachacks_version'
PLUGIN_VERSION = 1


class EnvironmentSetup(Component):

    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        version = self._get_version()
        if version == PLUGIN_VERSION:
            return False
        elif version > PLUGIN_VERSION:
            raise TracError(_("A newer plugin version has been installed "
                              "before, but downgrading is unsupported."))
        self.log.info("TracHacks database schema version is %d, should be %d"
                      % (version, PLUGIN_VERSION))
        return True

    def upgrade_environment(self, db):
        if self._get_version() == 0:
            pages_dir = pkg_resources.resource_filename('trachacks',
                                                        'default-pages')
            WikiAdmin(self.env).load_pages(pages_dir)
            self._set_version(PLUGIN_VERSION)

    def _get_version(self):
        version = self.env.db_query("""
            SELECT value FROM system WHERE name=%s
            """, (PLUGIN_NAME,))
        return int(version[0][0]) if version else 0

    def _set_version(self, version):
        if self._get_version() == 0:
            with self.env.db_transaction as db:
                db("INSERT INTO system (name, value) VALUES (%s, %s)",
                   (PLUGIN_NAME, version))
        else:
            with self.env.db_transaction as db:
                db("UPDATE system SET value=%s WHERE name=%s",
                   (version, PLUGIN_NAME))
