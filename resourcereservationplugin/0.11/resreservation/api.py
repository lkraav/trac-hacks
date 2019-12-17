# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Roberto Longobardi
#

import re
import time
import sys
import traceback
import logging

from datetime import datetime
from trac.core import *
from trac.perm import IPermissionRequestor, PermissionError
from trac.util import get_reporter_id
from trac.util.compat import sorted
from trac.util.datefmt import utc, to_timestamp
from trac.web.api import IRequestHandler


# Public methods

class ResourceReservationSystem(Component):
    """Resource Reservation system for Trac."""

    implements(IPermissionRequestor, IRequestHandler)

    # Public API
    def list_all_resources(self, res_type, res_from, res_to):
        """Get a list of all the reserved resources, optionally in the specified period."""

        result = []
        reservations = {}            
        
        try:
            db = self.env.get_db_cnx()

            # Get all different resource names
            cursor = db.cursor()
            sql = "SELECT DISTINCT name FROM resreservation WHERE res_type = '" + res_type +"'"
            cursor.execute(sql)

            for row in cursor:
                reservations[row[0]] = []

            # Then get the reservations
            cursor = db.cursor()
            sql = "SELECT name, assignee, res_from, res_to FROM resreservation WHERE res_type = '" + res_type +"'"
            
            if res_from != None and res_from != '' and res_to != None and res_to != '':
                sql += " AND res_from >= date(%s) AND res_to <= date(%s)"
                cursor.execute(sql, (res_from, res_to))
            else:
                cursor.execute(sql)

            for row in cursor:
                name = row[0]
                assignee = row[1]
                res_from = row[2]
                res_to = row[3]
                
                reservations[name].append({'assignee': assignee, 'res_from': res_from, 'res_to': res_to})

            for name in sorted(iter(reservations)):
                result.append({'name': name, 'reservations': reservations[name]})
                
        except:
            print "list_all_resources - Error!!!"
            db.rollback()
            raise

        return result


    def assign_resource(self, res_type, resource_name, res_date, curr_assignee, new_assignee, override):
        """Assign a resource."""

        try:
            db = self.env.get_db_cnx()

            # Check for overriding a previous reservation
            if override == 'false':
                # Let's see if a previous reservation is in place that includes this date on another person
                cursor = db.cursor()
                sql = "SELECT assignee FROM resreservation WHERE res_type = %s AND name = %s AND res_from <= date(%s) AND res_to >= date(%s)"
                cursor.execute(sql, (res_type, resource_name, res_date, res_date))
                
                row = cursor.fetchone();
                if (row and row[0] != curr_assignee and row[0] != new_assignee):
                    return False
            
            # Remove any previous reservation that includes the specified date
            cursor = db.cursor()
            sql = "DELETE FROM resreservation WHERE res_type = %s AND name = %s AND res_from <= date(%s) AND res_to >= date(%s)"
            cursor.execute(sql, (res_type, resource_name, res_date, res_date))

            # Now insert the new reservation
            if new_assignee != '':
                cursor = db.cursor()
                sql = "INSERT INTO resreservation (res_type, name, assignee, res_from, res_to) VALUES (%s, %s, %s, date(%s), date(%s))"
                cursor.execute(sql, (res_type, resource_name, new_assignee, res_date, res_date))
                
            db.commit()
            
            return True
            
        except:
            print "assign_resource - Error!!!"
            db.rollback()
            raise
            
            return False

            
    def add_resource(self, res_type, resource_name):
        """Add a resource."""
        
        try:
            db = self.env.get_db_cnx()
            
            cursor = db.cursor()
            sql = "INSERT INTO resreservation (res_type, name, assignee, res_from, res_to) VALUES (%s, %s, %s, date(%s), date(%s))"
            cursor.execute(sql, (res_type, resource_name, 'none', '2000-01-01', '2000-01-01'))
                
            db.commit()

        except:
            print "add_resource - Error!!!"
            db.rollback()
            raise

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['RES_RESERVE_VIEW', 'RES_RESERVE_MODIFY']

        
    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/resreservation') and ('RES_RESERVE_VIEW' in req.perm)

    def process_request(self, req):
        """Handles Ajax requests to set the resource reservation."""

        req.perm.require('RES_RESERVE_MODIFY')
        
        data = {'title': 'Results'}
        command = req.args.get('command')

        if (command == 'assignresource'):
            resource_type = req.args.get('resourceType')
            resource_name = req.args.get('resourceName')
            res_date = req.args.get('resDate')
            curr_assignee = req.args.get('currAssignee')
            new_assignee = req.args.get('newAssignee')
            override = req.args.get('override')

            result = self.assign_resource(resource_type, resource_name, res_date, curr_assignee, new_assignee, override)
            
            # Put the result in the Json object to return to the browser
            if result:
                data['result'] = '"true"'
            else:
                data['result'] = '"false"'
        
        elif (command == 'addresource'):
            resource_type = req.args.get('resourceType')
            resource_name = req.args.get('resourceName')
        
            self.add_resource(resource_type, resource_name)

            data['result'] = '"true"'
            
        return 'result.html', data, None

        
    # Internal methods
