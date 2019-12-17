# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Roberto Longobardi
#

import time
from datetime import datetime

from trac.core import *
from trac.db import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant
from trac.util.datefmt import utc, to_timestamp
from trac.util.text import CRLF


class TestManagerModelProvider(Component):
    implements(IEnvironmentSetupParticipant)

    SCHEMA = [
        Table('resreservation', key = ('res_type', 'name', 'res_from'))[
              Column('res_type'),
              Column('name'),
              Column('assignee'),
              Column('res_from', type='date'),
              Column('res_to', type='date'),
              Index(['res_type', 'name', 'res_from']),],
        ]
        
    # Set this to True to drop all tables before creating them again
    need_clean = False

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        print 'creating environment'
        
        db = self.env.get_db_cnx()
        
        if (self.need_clean):
            self._clean_environment(db)
        
        self._create_db(db)

        print 'environment created'
        
    def environment_needs_upgrade(self, db):
        if self.need_clean or self._need_initialization(db):
            return True

        return False

    def upgrade_environment(self, db):
        # Create db
        print 'upgrade_environment'
        if (self.need_clean):
            self._clean_environment(db)

        if self._need_initialization(db):
            self._upgrade_db(db)

    def _clean_environment(self, db):
        # Delete tables
        print 'clean_environment'
        cursor = db.cursor()
        
        try:
            cursor.execute("drop table resreservation")
            db.commit()
        except:
            db.rollback()
            print("unable to drop the tables")
        
    def _need_initialization(self, db):
        cursor = db.cursor()
        
        try:
            cursor.execute("select count(*) from resreservation")
            cursor.fetchone()
            return False
        except:
            db.rollback()
            print("resreservation needs to create the db")
            return True
        
    def _create_db(self, db):
        self._upgrade_db(db)
            
    def _upgrade_db(self, db):
        print("_upgrade_db")
        try:
            try:
                from trac.db import DatabaseManager
                db_backend, _ = DatabaseManager(self.env)._get_connector()
            except ImportError:
                db_backend = self.env.get_db_cnx()

            #cursor = db.cursor()
            #cursor.execute('drop table resreservation')
            
            cursor = db.cursor()
            
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    self.env.log.debug(stmt)
                    cursor.execute(stmt)
            db.commit()

            # Create the basic "ResourceReservation" Wiki page
            cursor = db.cursor()
            cursor.execute("INSERT INTO wiki (name,version,time,author,ipnr,"
                           "text,comment,readonly) VALUES (%s,%s,%s,%s,%s,%s,"
                           "%s,%s)", ('ResourceReservation', 1,
                                      to_timestamp(datetime.now(utc)), 'System', '127.0.0.1',
                                      '== Resource Reservation ==' + CRLF +'[[ResourceReservationList(type=resource,period=3,title=Resource)]][[BR]][[BR]][[BR]][[BR]][[BR]]', '', 0))
                    
            db.commit()
            
        except:
            print("exception in the database creation")
            db.rollback()
            raise

