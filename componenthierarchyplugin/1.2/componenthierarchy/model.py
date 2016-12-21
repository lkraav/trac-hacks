# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 falkb
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.db import Column, DatabaseManager, Table
from trac.env import IEnvironmentSetupParticipant

db_version_key = 'component_hierarchy'
db_version = 1

tables_v1 = [
    Table('component_hierarchy', key='component')[
        Column('component', type='varchar'),
        Column('parent_component', type='varchar')
    ],
]


class ComponentHierarchyEnvironmentSetupParticipant(Component):

    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(db_version, db_version_key)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        with self.env.db_transaction:
            dbm.create_tables(tables_v1)
            dbm.set_database_version(db_version, db_version_key)


class ComponentHierarchyModel(Component):

    def get_parent_component(self, component):
        for result, in self.env.db_query("""
                SELECT parent_component
                FROM component_hierarchy
                WHERE component=%s
                """, (component,)):
            return result

    def has_parent_component(self, component):
        return self.get_parent_component(component) is not None

    def set_parent_component(self, component, parent_component):
        if parent_component is None or parent_component == "":
            query = """
                DELETE FROM component_hierarchy
                WHERE component=%s
                """
            args = (component,)
        else:
            if self.has_parent_component(component):
                query = """
                    UPDATE component_hierarchy SET parent_component=%s
                    WHERE component=%s
                    """
                args = (parent_component, component)
            else:
                query = """
                    INSERT INTO component_hierarchy
                     (component, parent_component)
                    VALUES (%s, %s)
                    """
                args = (component, parent_component)

        self.env.db_transaction(query, args)

    def rename_component(self, component, new_name):
        with self.env.db_transaction as db:
            db("""
                UPDATE component_hierarchy SET component=%s
                WHERE component=%s
                """, (new_name, component))
            db("""
                UPDATE component_hierarchy SET parent_component=%s
                WHERE parent_component=%s
                """, (new_name, component))

    def remove_parent_component(self, component):
        self.set_parent_component(component, None)

    def is_child(self, parent_component, child_component):
        parent = self.get_parent_component(child_component)
        if parent is None:
            return False
        elif parent == parent_component:
            return True
        else:
            return self.is_child(parent_component, parent)

    def get_direct_children(self, component):
        return [c for c, in self.env.db_query("""
                SELECT component FROM component_hierarchy
                WHERE parent_component=%s ORDER BY component
                """, (component,))]
