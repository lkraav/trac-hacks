#!/usr/bin/env python2.4
"""
Import a PhpBugTracker bugs into a Trac database.

Requires:  Trac 0.10 from http://trac.edgewall.org/
       Python 2.4 from http://www.python.org/ m

Copyright 2007, Lucas Stephanou <domluc@gmail.com>

startdate: 2007-06-01

Inspired by bugzilla2trac

$Id$
"""

import re

###
### Conversion Settings -- edit these before running if desired


# Bugzilla version.  You can find this in Bugzilla's globals.pl file.
#
# Currently, the following bugzilla versions are known to work:
#   2.11 (2110), 2.16.5 (2165), 2.18.3 (2183), 2.19.1 (2191)
#
# If you run this script on a version not listed here and it is successful,
# please report it to the Trac mailing list and drop a note to
# asmodai@tendra.org so we can update the list.
BT_VERSION = 2180

# MySQL connection parameters for the Bugzilla database.  These can also
# be specified on the command line.
BT_DB = ""
BT_HOST = ""
BT_USER = ""
BT_PASSWORD = ""

# Path to the Trac environment.
TRAC_ENV = "/usr/local/trac"

# If true, all existing Trac tickets and attachments will be removed
# prior to import.
TRAC_CLEAN = True

# Enclose imported ticket description and comments in a {{{ }}}
# preformat block?  This formats the text in a fixed-point font.
PREFORMAT_COMMENTS = False

# Replace bug numbers in comments with #xyz
REPLACE_BUG_NO = False

# Severities
SEVERITIES = [
  ("blocker",  "1"),
  ("critical", "2"),
  ("major",  "3"),
  ("normal",   "4"),
  ("minor",  "5"),
  ("trivial",  "6")
]

# Priorities
# If using the default Bugzilla priorities of P1 - P5, do not change anything
# here.
# If you have other priorities defined please change the P1 - P5 mapping to
# the order you want.  You can also collapse multiple priorities on bugzilla's
# side into the same priority on Trac's side, simply adjust PRIORITIES_MAP.
PRIORITIES = [
  ("highest", "1"),
  ("high",  "2"),
  ("normal",  "3"),
  ("low",   "4"),
  ("lowest",  "5")
]

# Bugzilla: Trac
# NOTE: Use lowercase.
PRIORITIES_MAP = {
  "p1": "highest",
  "p2": "high",
  "p3": "normal",
  "p4": "low",
  "p5": "lowest"
}

# By default, all bugs are imported from Bugzilla.  If you add a list
# of products here, only bugs from those products will be imported.
PRODUCTS = []
# These Bugzilla products will be ignored during import.
IGNORE_PRODUCTS = []

# These milestones are ignored
IGNORE_MILESTONES = ["---"]

# These logins are converted to these user ids
LOGIN_MAP = {
  #'some.user@example.com': 'someuser',
}

# These emails are removed from CC list
IGNORE_CC = [
  #'loser@example.com',
]

# The 'component' field in Trac can come either from the Product or
# or from the Component field of Bugzilla. COMPONENTS_FROM_PRODUCTS
# switches the behavior.
# If COMPONENTS_FROM_PRODUCTS is True:
# - Bugzilla Product -> Trac Component
# - Bugzilla Component -> Trac Keyword
# IF COMPONENTS_FROM_PRODUCTS is False:
# - Bugzilla Product -> Trac Keyword
# - Bugzilla Component -> Trac Component
COMPONENTS_FROM_PRODUCTS = False

# If COMPONENTS_FROM_PRODUCTS is True, the default owner for each
# Trac component is inferred from a default Bugzilla component.
DEFAULT_COMPONENTS = ["default", "misc", "main"]

# This mapping can assign keywords in the ticket entry to represent
# products or components (depending on COMPONENTS_FROM_PRODUCTS).
# The keyword will be ignored if empty.
KEYWORDS_MAPPING = {
  #'Bugzilla_product_or_component': 'Keyword',
  "default": "",
  "misc": "",
  }

# If this is True, products or components are all set as keywords
# even if not mentionned in KEYWORDS_MAPPING.
MAP_ALL_KEYWORDS = True


# Bug comments that should not be imported.  Each entry in list should
# be a regular expression.
IGNORE_COMMENTS = [
   "^Created an attachment \(id="
]

###########################################################################
### You probably don't need to change any configuration past this line. ###
###########################################################################

# Bugzilla status to Trac status translation map.
#
# NOTE: bug activity is translated as well, which may cause bug
# activity to be deleted (e.g. resolved -> closed in Bugzilla
# would translate into closed -> closed in Trac, so we just ignore the
# change).
#
# There is some special magic for open in the code:  if there is no
# Bugzilla owner, open is mapped to 'new' instead.
STATUS_TRANSLATE = {
  "unconfirmed": "new",
  "open":    "assigned",
  "resolved":  "closed",
  "verified":  "closed",
  "released":  "closed"
}

# Translate Bugzilla statuses into Trac keywords.  This provides a way
# to retain the Bugzilla statuses in Trac.  e.g. when a bug is marked
# 'verified' in Bugzilla it will be assigned a VERIFIED keyword.
STATUS_KEYWORDS = {
  "verified": "VERIFIED",
  "released": "RELEASED"
}

# Some fields in Bugzilla do not have equivalents in Trac.  Changes in
# fields listed here will not be imported into the ticket change history,
# otherwise you'd see changes for fields that don't exist in Trac.
IGNORED_ACTIVITY_FIELDS = ["everconfirmed"]

# Regular expression and its replacement
BUG_NO_RE = re.compile(r"\b(bug #?)([0-9])")
BUG_NO_REPL = r"#\2"

###
### Script begins here
###

import os
import sys
import string
import StringIO

try:
    from pyPgSQL import PgSQL
except:
    print sys.exc_info()[0]

try:
    from trac.env import Environment
except:
    from trac.Environment import Environment
from trac.attachment import Attachment

if not hasattr(sys, 'setdefaultencoding'):
    reload(sys)

sys.setdefaultencoding('latin1')

# simulated Attachment class for trac.add
#class Attachment:
#  def __init__(self, name, data):
#    self.filename = name
#    self.file = StringIO.StringIO(data.tostring())

# simple field translation mapping.  if string not in
# mapping, just return string, otherwise return value
class FieldTranslator(dict):
    def __getitem__(self, item):
        if not dict.has_key(self, item):
            return item

        return dict.__getitem__(self, item)

statusXlator = FieldTranslator(STATUS_TRANSLATE)

class TracDatabase(object):
    def __init__(self, path):
        self.env = Environment(path)
        self._db = self.env.get_db_cnx()
        self._db.autocommit = False
        self.loginNameCache = {}
        self.fieldNameCache = {}

    def db(self):
        return self._db

    def hasTickets(self):
        c = self.db().cursor()
        c.execute("SELECT count(*) FROM Ticket")
        return int(c.fetchall()[0][0]) > 0

    def assertNoTickets(self):
        if self.hasTickets():
            raise Exception("Will not modify database with existing tickets!")

    def setSeverityList(self, s):
        """Remove all severities, set them to `s`"""
        self.assertNoTickets()

        c = self.db().cursor()
        c.execute("DELETE FROM enum WHERE type='severity'")
        for value, i in s:
            print "  inserting severity '%s' - '%s'" % (value, i)
            c.execute("""INSERT INTO enum (type, name, value)
                         VALUES (%s, %s, %s)""",
                  ("severity", value.encode('utf-8'), i))
        self.db().commit()

    def setPriorityList(self, s):
        """Remove all priorities, set them to `s`"""
        self.assertNoTickets()

        c = self.db().cursor()
        c.execute("DELETE FROM enum WHERE type='priority'")
        for value, i in s:
            print "  inserting priority '%s' - '%s'" % (value, i)
            c.execute("""INSERT INTO enum (type, name, value)
                         VALUES (%s, %s, %s)""",
                  ("priority", value.encode('utf-8'), i))
        self.db().commit()


    def setComponentList(self, l, key):
        """Remove all components, set them to `l`"""
        self.assertNoTickets()

        c = self.db().cursor()
        c.execute("DELETE FROM component")
        for comp in l:
            if (comp['owner'] == None):
                comp['owner'] = 'admin' # if doesn't have owner, set to admin

            print "  inserting component '%s', owner '%s'" % \
                    (comp[key], comp['owner'])
            c.execute("INSERT INTO component (name, owner) VALUES (%s, %s)",
                  (comp[key].encode('utf-8'),comp['owner'].encode('utf-8')))
        self.db().commit()

    def setVersionList(self, v):
        """Remove all versions, set them to `v`"""
        self.assertNoTickets()

        c = self.db().cursor()
        c.execute("DELETE FROM version")
        for vers in v:
            print "  inserting version '%s'" % (vers['name'])
            c.execute("INSERT INTO version (name,description) VALUES (%s,%s)",
                  (vers['name'].encode('utf-8'),vers['description'].encode('utf-8')))
        self.db().commit()

    def setMilestoneList(self, m, key):
        """Remove all milestones, set them to `m`"""
        self.assertNoTickets()

        c = self.db().cursor()
        c.execute("DELETE FROM milestone")
        for ms in m:
            milestone = ms[key]
            print "  inserting milestone '%s'" % (milestone)
            c.execute("INSERT INTO milestone (name) VALUES (%s)",
                  (milestone.encode('utf-8'),))
        self.db().commit()

    def addTicket(self, id, time, changetime, component, severity, priority,
            owner, reporter, cc, version, milestone, status, resolution,
            summary, description, keywords):
        c = self.db().cursor()

        desc = description.encode('utf-8')
        type = "defect"

        if severity.lower() == "enhancement":
            severity = "minor"
            type = "enhancement"

        if PREFORMAT_COMMENTS:
            desc = '{{{\n%s\n}}}' % desc

        if REPLACE_BUG_NO:
            if BUG_NO_RE.search(desc):
                desc = re.sub(BUG_NO_RE, BUG_NO_REPL, desc)

        if PRIORITIES_MAP.has_key(priority):
            priority = PRIORITIES_MAP[priority]

        print "  inserting ticket %s -- %s" % (id, summary)

        c.execute("""INSERT INTO ticket (id, type, time, changetime, component,
                         severity, priority, owner, reporter,
                         cc, version, milestone, status,
                         resolution, summary, description,
                         keywords)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                         %s, %s, %s, %s, %s, %s, %s, %s)""",
              (id, type, time, changetime, component.encode('utf-8'),
               severity.encode('utf-8'), priority, owner.encode('utf-8'),
               reporter.encode('utf-8'), cc.encode('utf-8'), version.encode('utf-8'), milestone,
               status.encode('utf-8').lower(), resolution.encode('utf-8'), summary.encode('utf-8'), desc,
               keywords.encode('utf-8')))

        self.db().commit()
        return self.db().get_last_id(c, 'ticket')

    def addTicketComment(self, ticket, time, author, value):
        comment = value

        if PREFORMAT_COMMENTS:
            comment = '{{{\n%s\n}}}' % comment

        if REPLACE_BUG_NO:
            if BUG_NO_RE.search(comment):
                comment = re.sub(BUG_NO_RE, BUG_NO_REPL, comment)

        c = self.db().cursor()
        c.execute("""INSERT INTO ticket_change (ticket, time, author, field,
                            oldvalue, newvalue)
                        VALUES (%s, %s, %s, %s, %s, %s)""",
              (ticket, time, author, 'comment', '', comment.encode('utf-8')))
        self.db().commit()

    def addTicketChange(self, ticket, time, author, field, oldvalue, newvalue):
        c = self.db().cursor()

        if field == "owner":
            if LOGIN_MAP.has_key(oldvalue):
                oldvalue = LOGIN_MAP[oldvalue]
            if LOGIN_MAP.has_key(newvalue):
                newvalue = LOGIN_MAP[newvalue]

        if field == "priority":
            if PRIORITIES_MAP.has_key(oldvalue.lower()):
                oldvalue = PRIORITIES_MAP[oldvalue.lower()]
            if PRIORITIES_MAP.has_key(newvalue.lower()):
                newvalue = PRIORITIES_MAP[newvalue.lower()]

        # Doesn't make sense if we go from highest -> highest, for example.
        if oldvalue == newvalue:
            return

        c.execute("""INSERT INTO ticket_change (ticket, time, author, field,
                            oldvalue, newvalue)
                        VALUES (%s, %s, %s, %s, %s, %s)""",
              (ticket, time, author.encode('utf-8'), field.encode('utf-8'),
               oldvalue.encode('utf-8'), newvalue.encode('utf-8')))
        self.db().commit()

    def addAttachment(self, author, a):
        description = a['description'].encode('utf-8')
        id = a['bug_id']
        filename = a['filename'].encode('utf-8')
        filedata = StringIO.StringIO(a['thedata'])
        filesize = len(filedata.getvalue())
        time = a['creation_ts']
        print "  ->inserting attachment '%s' for ticket %s -- %s" % \
            (filename, id, description)

        attachment = Attachment(self.env, 'ticket', id)
        attachment.author = author
        attachment.description = description
        attachment.insert(filename, filedata, filesize, time.strftime('%s'))
        del attachment

    def getLoginName(self, cursor, userid):
        if userid not in self.loginNameCache:
            cursor.execute("SELECT * FROM profiles WHERE userid = %s", (userid))
            loginName = cursor.fetchall()

            if loginName:
                loginName = loginName[0]['login_name']
            else:
                print """WARNING: unknown bugzilla userid %d, recording as
                     anonymous""" % (userid)
                loginName = "anonymous"

            loginName = LOGIN_MAP.get(loginName, loginName)

            self.loginNameCache[userid] = loginName

        return self.loginNameCache[userid]

    def getFieldName(self, cursor, fieldid):
        if fieldid not in self.fieldNameCache:
            cursor.execute("SELECT * FROM fielddefs WHERE fieldid = %s",
                     (fieldid))
            fieldName = cursor.fetchall()

            if fieldName:
                fieldName = fieldName[0]['name'].lower()
            else:
                print "WARNING: unknown bugzilla fieldid %d, \
                        recording as unknown" % (userid)
                fieldName = "unknown"

            self.fieldNameCache[fieldid] = fieldName

        return self.fieldNameCache[fieldid]

def makeWhereClause(fieldName, values, negative=False):
    if not values:
        return ''
    if negative:
        connector, op = ' AND ', '!='
    else:
        connector, op = ' OR ', '='
    clause = connector.join(["%s %s '%s'" % (fieldName, op, value) for value in values])
    return ' ' + clause

def convert(_db, __db_prefix, _host, _user, _password, _env, _force):
    activityFields = FieldTranslator()

    # init PhpBugTracker environment
    print "PhpBugTracker Postgresql('%s':'%s':'%s':'%s'): connecting..." % \
        (_db, _host, _user, ("*" * len(_password)))
    #pg_con = PgSQL.connect(host=_host, user=_user, password=_password, database=_db)
    dsn = '%s:%s:%s:%s:%s' % (_host,5432,_db,_user,_password)

    pg_con = PgSQL.connect(dsn)
    pg_cur = pg_con.cursor()

    # init Trac environment
    print "Trac SQLite('%s'): connecting..." % (_env)
    trac = TracDatabase(_env)

    # force mode...
    if _force == 1:
        print "\nCleaning all tickets..."
        c = trac.db().cursor()
        c.execute("DELETE FROM ticket_change")
        trac.db().commit()

        c.execute("DELETE FROM ticket")
        trac.db().commit()

        c.execute("DELETE FROM attachment")

        print "All tickets cleaned..."

    print "\n1. Import severities..."
    sql = """ select sort_order
              , severity_name
          from %(PREFIX)sseverity
        order by sort_order """
    sql = sql%{'PREFIX':__db_prefix}

    pg_cur.execute(sql)
    lines = pg_cur.fetchall()
    severities_list = []


    for line in lines:
        severities_list.append([line['severity_name'], line['sort_order']])

    trac.setSeverityList(severities_list)

    print "\n2. Import components..."
    sql = """  select component_name
             , ( select login from %(PREFIX)sauth_user where user_id = %(PREFIX)scomponent.owner ) as owner
             , component_desc
            from %(PREFIX)scomponent
            where substring(component_name from 1 for 1) = '0'
      group by component_name, owner, component_desc
      order by component_name """
    sql = sql%{'PREFIX':__db_prefix}

    pg_cur.execute(sql)
    lines = pg_cur.fetchall()
    component_list = []
    for line in lines:
        component_list.append({'product': line['component_name'], 'owner': line['owner']})

    trac.setComponentList(component_list, 'product')

    print "\n4. Import versions..."
    sql = """select distinct version_name as name
         , version_name as description
        from %(PREFIX)sversion"""
    sql = sql%{'PREFIX':__db_prefix}

    pg_cur.execute(sql)
    lines = pg_cur.fetchall()

    versions_list = []

    for line in lines:
        versions_list.append({'name': line['name'], 'description': line['name']})

    trac.setVersionList(versions_list)

    print "\n6. Retrieving bugs..."
    sql = """select bug_id
         , title as summary
         , created_date
         , last_modified_date
         , description as description
         , priority
         , ( select component_name from %(PREFIX)scomponent where component_id=%(PREFIX)sbug.component_id ) as component
         , ( select login from %(PREFIX)sauth_user where user_id=%(PREFIX)sbug.assigned_to ) as owner
         , ( select login from %(PREFIX)sauth_user where user_id=%(PREFIX)sbug.created_by ) as reporter
         , ( select version_name from %(PREFIX)sversion where version_id=%(PREFIX)sbug.version_id) as version
         , ( select severity_name from %(PREFIX)sseverity where severity_id=%(PREFIX)sbug.severity_id) as severity
         , '' as milestone
         , ( select status_name from %(PREFIX)sstatus where status_id = %(PREFIX)sbug.status_id ) as status
         , ( select resolution_name from %(PREFIX)sresolution where resolution_id = %(PREFIX)sbug.resolution_id) as resolution
         , 'imported, phpbugtracker' as keywords
        from %(PREFIX)sbug limit 50"""
    sql = sql%{'PREFIX':__db_prefix}
    pg_cur.execute(sql)
    bugs = pg_cur.fetchall()


    print "\n7. Import bugs and bug activity..."

    for bug in bugs:
        bugid = bug['bug_id']

        ticket = {}
        keywords = []
        ticket['id'] = bugid
        ticket['time'] = bug['created_date']
        ticket['changetime'] = bug['last_modified_date']

        if(bug['component'] == None):
            bug['component'] = ' '
        ticket['component'] = bug['component']

        if(bug['severity'] == None):
            bug['severity'] = ' '
        ticket['severity'] = bug['severity']

        if(bug['priority'] == None):
            bug['priority'] = ' '
        ticket['priority'] = bug['priority']

        if(bug['owner'] == None):
            bug['owner'] = ' '
        ticket['owner'] = bug['owner']

        if(bug['reporter'] == None):
            bug['reporter'] = ' '
        ticket['reporter'] = bug['reporter']

        if(bug['version'] == None):
            bug['version'] = ' '
        ticket['version'] = bug['version']

        if(bug['status'] == None):
            bug['status'] = ' '
        ticket['status'] = bug['status'].lower()

        ticket['milestone'] = 'imported'

        # if resolution is NoneType
        if(bug['resolution'] == None):
            bug['resolution'] = ''

        ticket['resolution'] = bug['resolution'].lower()

        if(bug['summary'] == None):
            ticket['summary'] = ' '
        ticket['summary'] = bug['summary']

        longdescs = bug['description']

        if len(longdescs) == 0:
            ticket['description'] = ''
        else:
            ticket['description'] = bug['description']

        # comentarios
        sql = """ select distinct comment_text as comment
                   , created_date as time
                 , 'comment' as field
                 , ( select login from %(PREFIX)sauth_user where user_id = %(PREFIX)scomment.created_by ) as author
               from %(PREFIX)scomment
              where bug_id = %(BUGID)s
             order by created_date asc """
        sql = sql%{'PREFIX':__db_prefix,'BUGID':bug['bug_id']}
        pg_cur.execute(sql)
        comments = pg_cur.fetchall()

        for comment in comments:
            print 'Chamando Ticket: %s, Time: %s, Author: %s' % (bugid,comment['time'],comment['author'])
            trac.addTicketComment(ticket=bugid,
              time = comment['time'],
              author=comment['author'],
              value = comment['comment'])

        # ticket changes
        sql = """   select 0 as ticket
                 , created_date as time
                 , ( select login from %(PREFIX)sauth_user where user_id = %(PREFIX)sbug_history.created_by ) as author
                 , changed_field as field
                 , old_value as oldvalue
                 , new_value as newvalue
                from %(PREFIX)sbug_history
               where changed_field
                   in (  'component'
                    ,'resolution'
                    ,'severity'
                    ,'status'
                    ,'version')
                and bug_id = %(BUGID)s
              order by created_date asc """

        sql = sql%{'PREFIX':__db_prefix,'BUGID':bug['bug_id']}
        pg_cur.execute(sql)
        bugs_activity = pg_cur.fetchall()

        resolution = ''
        ticketChanges = []
        keywords = []

        for activity in bugs_activity:
            field_name = activity['field'].lower()

            removed = activity['oldvalue']
            added = activity['newvalue']

            # statuses and resolutions are in lowercase in trac
            if field_name == "resolution" or field_name == "bug_status":
                removed = removed.lower()
                added = added.lower()

            ticketChange = {}
            ticketChange['ticket'] = bugid
            ticketChange['time'] = activity['time']

            if(activity['author']==None):
                activity['author'] = ' '
            ticketChange['author'] = activity['author']

            if(field_name==None):
                field_name = ' '
            ticketChange['field'] = field_name

            if(removed==None):
                removed = ' '
            ticketChange['oldvalue'] = removed

            if(added==None):
                added = ' '
            ticketChange['newvalue'] = added

            ticketChanges.append (ticketChange)

        for ticketChange in ticketChanges:
            trac.addTicketChange (**ticketChange)

        # end activity information

        ticket['keywords'] = 'imported,phpbugtracker' # mark imported tickets
        ticket['cc'] = ''

        ticketid = trac.addTicket(**ticket)

    print "\nAll tickets converted."

def log(msg):
    print "DEBUG: %s" % (msg)

def usage():
    print """phpbt2trac - Imports a bug database from PhpBugTracker into Trac.

  Usage: phpbt2trac.py [options]

  Available Options:
    --db <dbname>                 - PHPBugTracker's database name
    --db-prefix <prefix>          - PHPBugTracker's table prefix(phpbt)
    --srv <server_type>           - Database Server Type(mysql|postgres)
    --tracenv /path/to/trac/env   - Full path to Trac db environment
    -h | --host <hostname>        - PHPBugTracker's DNS host name
    -u | --user <username>        - PHPBugTracker's database user
    -p | --passwd <password>      - PHPBugTracker's user password
    -c | --clean                  - Remove current Trac tickets before
                                    importing
    --help | help                 - This help info

  Additional configuration options can be defined directly in the script.
  """
    sys.exit(0)

def main():
    global BT_DB, BT_HOST, BT_USER, BT_PASSWORD, BT_PREFIX, TRAC_ENV, TRAC_CLEAN
    if len (sys.argv) > 1:
        if sys.argv[1] in ['--help','help'] or len(sys.argv) < 4:
            usage()
        iter = 1
        while iter < len(sys.argv):
            if sys.argv[iter] in ['--db'] and iter+1 < len(sys.argv):
                BT_DB = sys.argv[iter+1]
                iter = iter + 1
            elif sys.argv[iter] in ['--db-prefix'] and iter+1 < len(sys.argv):
                BT_PREFIX = sys.argv[iter+1]
                iter = iter + 1
            elif sys.argv[iter] in ['-h', '--host'] and iter+1 < len(sys.argv):
                BT_HOST = sys.argv[iter+1]
                iter = iter + 1
            elif sys.argv[iter] in ['-u', '--user'] and iter+1 < len(sys.argv):
                BT_USER = sys.argv[iter+1]
                iter = iter + 1
            elif sys.argv[iter] in ['-p', '--passwd'] and iter+1 < len(sys.argv):
                BT_PASSWORD = sys.argv[iter+1]
                iter = iter + 1
            elif sys.argv[iter] in ['--tracenv'] and iter+1 < len(sys.argv):
                TRAC_ENV = sys.argv[iter+1]
                iter = iter + 1
            elif sys.argv[iter] in ['-c', '--clean']:
                TRAC_CLEAN = 1
            else:
                print "Error: unknown parameter: " + sys.argv[iter]
                sys.exit(0)
            iter = iter + 1

    convert(BT_DB, BT_PREFIX, BT_HOST, BT_USER, BT_PASSWORD, TRAC_ENV, TRAC_CLEAN)

if __name__ == '__main__':
    main()
