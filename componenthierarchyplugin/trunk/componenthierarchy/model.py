# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Doering, falkb
#

from trac import __version__ as VERSION
from trac.core import *
from trac.ticket import model
from trac.db import with_transaction

class ComponentHierarchyModel(Component):

    # DB Method
    def __start_transaction(self):
        if VERSION < '0.12':
            # deprecated in newer versions
            self.db.commit()
            self.db.close()

    def get_parent_component(self, component):
        if VERSION < '0.12':
            db = self.env.get_db_cnx()
        else:
            db = self.env.get_read_db()
        cursor = db.cursor()
                 
        query = "SELECT parent_component FROM component_hierarchy WHERE component='%s'" % component
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result and len(result) > 0:
            return result[0]
        else:
            return None

    def has_parent_component(self, component):
        return self.get_parent_component(component) != None

    def set_parent_component(self, component, parent_component):
        if parent_component == None or parent_component == "":
            query = "DELETE FROM component_hierarchy WHERE component='%s'" % component
        else:
            if self.has_parent_component(component):
                query = "UPDATE component_hierarchy SET parent_component='%s' WHERE component='%s'" % (parent_component, component)
            else:
                query = "INSERT INTO component_hierarchy (component, parent_component) VALUES ('%s', '%s')" % (component, parent_component)

        if VERSION < '0.12':
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute(query)
            self.__start_transaction(db)
        else:
            @with_transaction(self.env)
            def execute_sql_statement(db):
                cursor = db.cursor()
                cursor.execute(query)

    def rename_component(self, component, new_name):
        query1 = "UPDATE component_hierarchy SET component='%s' WHERE component='%s'" % (new_name, component)
        query2 = "UPDATE component_hierarchy SET parent_component='%s' WHERE parent_component='%s'" % (new_name, component)

        if VERSION < '0.12':
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute(query1)
            cursor.execute(query2)
            self.__start_transaction(db)
        else:
            @with_transaction(self.env)
            def execute_sql_statement(db):
                cursor = db.cursor()
                cursor.execute(query1)
                cursor.execute(query2)
        
    def remove_parent_component(self, component):
        self.set_parent_component(component, None)

    def is_child(self, parent_component, child_component):
        parent = self.get_parent_component(child_component)
        if parent == None:
            return False
        elif parent == parent_component:
            return True
        else:
            return self.is_child(parent_component, parent)

    def get_direct_children(self, component):
        if VERSION < '0.12':
            db = self.env.get_db_cnx()
        else:
            db = self.env.get_read_db()
        cursor = db.cursor()
                 
        query = "SELECT component FROM component_hierarchy WHERE parent_component='%s'" % component
        cursor.execute(query)

        result = cursor.fetchall()
        if result:
            result = [row[0] for row in sorted(result)]

        return result
        