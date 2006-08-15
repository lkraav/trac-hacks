# Copyright (C) 2006 Sam Bloomquist <spooninator@hotmail.com>
# All rights reserved.
# vi: et ts=4 sw=4
# This software may at some point consist of voluntary contributions made by
# many individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Sam Bloomquist <spooninator@hotmail.com>

import time
import sys

from trac.core import *
from trac.util import format_date
from trac.env import open_environment

def main():
    if len(sys.argv) != 2:
        print >> sys.stderr, 'Must supply a trac_env as an argument to the burndown_job'
        sys.exit(1)
        
    env_path = sys.argv[1]
    
    # today's date
    today = format_date(int(time.time()))
    
    # open up a connection to the trac database
    env = open_environment(env_path)
    db = env.get_db_cnx()
    cursor = db.cursor()
    
    # make sure that there isn't already an entry for today in the burndown table
    cursor.execute("SELECT id FROM burndown WHERE date = '%s'" % today)
    row = cursor.fetchone()
    if row:
        print >> sys.stderr, 'burndown_job.py has already been run today'
        sys.exit(1)
    
    # get arrays of the various components and milestones in the trac environment
    cursor.execute("SELECT name AS comp FROM component")
    components = cursor.fetchall()
    cursor.execute("SELECT name, started, completed FROM milestone")
    milestones = cursor.fetchall()
    
    for mile in milestones:
        if mile[1] and not mile[2]: # milestone started, but not completed
            for comp in components:
                sqlSelect =     "SELECT est.value AS estimate, ts.value AS spent "\
                                    "FROM ticket t "\
                                    "    LEFT OUTER JOIN ticket_custom est ON (t.id = est.ticket AND est.name = 'current_estimate') "\
                                    "    LEFT OUTER JOIN ticket_custom ts ON (t.id = ts.ticket AND ts.name = 'time_spent') "\
                                    "WHERE t.component = '%s' AND t.milestone = '%s' "
                #print sqlSelect % (comp[0], mile[0])
                cursor.execute(sqlSelect % (comp[0], mile[0]))
            
                rows = cursor.fetchall()
                hours = 0
                estimate = 0
                spent = 0
                if rows:
                    for estimate, spent in rows:
                        if not estimate:
                            estimate = 0
                        if not spent:
                            spent = 0
                    
                        hours += int(estimate) - int(spent)
                        
                else:
                    print "no results for %s component in %s milestone" % (comp[0], mile[0])
                # print "last id was %s" % (db.get_last_id(cursor, 'burndown'))
                # Sometimes db.get_last_id(cursor, 'burndown') returns "None".. 
                print 'burndown: %s, %s, %s, %s, %i' % (db.get_last_id(cursor, 'burndown'), comp[0], mile[0], today, hours)
                cursor.execute("INSERT INTO burndown(id,component_name, milestone_name, date, hours_remaining) "\
                                     "    VALUES(NULL,'%s','%s','%s',%i)" % (comp[0], mile[0], today, hours))
                                     
    db.commit()

if __name__ == '__main__':
    main()
