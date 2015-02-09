from trac.ticket import ITicketChangeListener, Ticket, ITicketManipulator
from trac.perm import PermissionCache
from trac.core import *
import datetime
import dbhelper

def identity(x):
    return x;

def convertfloat(x):
    "some european countries use , as the decimal separator"
    x = str(x).strip()
    if len(x) > 0:
        return float(x.replace(',','.'))
    else: 
        return 0.0

try:
    import trac.util.datefmt
    to_timestamp = trac.util.datefmt.to_utimestamp
except Exception:
    to_timestamp = identity


def save_custom_field_value( db, ticket_id, field, value ):
    cursor = db.cursor();
    cursor.execute("SELECT * FROM ticket_custom " 
                   "WHERE ticket=%s and name=%s", (ticket_id, field))
    if cursor.fetchone():
        cursor.execute("UPDATE ticket_custom SET value=%s "
                       "WHERE ticket=%s AND name=%s",
                       (value, ticket_id, field))
    else:
        cursor.execute("INSERT INTO ticket_custom (ticket,name, "
                       "value) VALUES(%s,%s,%s)",
                       (ticket_id, field, value))

def update_hours_to_floats(db, ticket_id):
    cursor = db.cursor()
    cursor.execute("SELECT time, newvalue FROM ticket_change"
                   " WHERE newvalue like '%,%' AND  ticket=%s AND field='hours'", 
                   (ticket_id,))
    data = list(cursor.fetchall())
    for (time, newvalue) in data:
        cursor.execute("UPDATE ticket_change SET newvalue=%s "
                       "WHERE ticket=%s AND time=%s AND field='hours'",
                       (str(convertfloat(newvalue)), ticket_id, time))
    
def update_totalhours_custom( db, ticket_id):
    cursor = db.cursor()
    sumSql = """
       (SELECT SUM( CASE WHEN newvalue = '' OR newvalue IS NULL THEN 0
                         ELSE CAST( newvalue AS DECIMAL ) END ) as total 
          FROM ticket_change
         WHERE ticket=%s and field='hours')  """
    cursor.execute("UPDATE ticket_custom SET value="+sumSql+
                   "WHERE ticket=%s AND name='totalhours'",
               (ticket_id,ticket_id))
    if cursor.rowcount==0:
        cursor.execute("INSERT INTO ticket_custom (name, value, ticket) "+
                       "VALUES('totalhours',"+sumSql+",%s)",
                       (ticket_id,ticket_id))

def insert_totalhours_changes( db, ticket_id):
    sql = """
       INSERT INTO ticket_change (ticket, author, time, field, oldvalue, newvalue)
       SELECT ticket, author, time, 'totalhours',  
               (SELECT SUM( CASE WHEN newvalue = '' OR newvalue IS NULL THEN 0
                           ELSE CAST( newvalue AS DECIMAL ) END ) as total
               FROM ticket_change as guts 
               WHERE guts.ticket = ticket_change.ticket AND guts.field='hours'
                 AND guts.time < ticket_change.time
              ) as oldvalue, 
              (SELECT SUM( CASE WHEN newvalue = '' OR newvalue IS NULL THEN 0
                           ELSE CAST( newvalue AS DECIMAL ) END ) as total
               FROM ticket_change as guts 
               WHERE guts.ticket = ticket_change.ticket AND guts.field='hours'
                 AND guts.time <= ticket_change.time
              ) as newvalue
          FROM ticket_change
         WHERE ticket=%s and field='hours'
           AND NOT EXISTS( SELECT ticket
                             FROM ticket_change as guts 
                            WHERE guts.ticket=ticket_change.ticket
                              AND guts.author=ticket_change.author
                              AND guts.time=ticket_change.time
                              AND field='totalhours')
    """
    cursor = db.cursor()
    cursor.execute(sql, (ticket_id,))

def delete_ticket_change( comp, ticket_id, change_time, field):
    """ removes a ticket change from the database """
    if isinstance(change_time, datetime.datetime):
        change_time = to_timestamp(change_time)
    sql = """DELETE FROM ticket_change  
             WHERE ticket=%s and time=%s and field=%s""" 
    dbhelper.execute_non_query(comp.env, sql, ticket_id, change_time, field)

class TimeTrackingTicketObserver(Component):
    implements(ITicketChangeListener)
    def __init__(self):
        pass

    def watch_hours(self, ticket, author=None):
        ticket_id = ticket.id
        hours = convertfloat(ticket['hours'])
        change_time = ticket['changetime']
        # no hours, changed
        if hours == 0:
            return

        # if we dont have an author just skip permissions check
        # its probably not important as this is generated data
        # and it was probably caused by someone with ticket admin modifying history
        if author:
            self.log.debug("Checking permissions")        
            perm = PermissionCache(self.env, author)
            if not perm or not perm.has_permission("TIME_RECORD"):
                self.log.debug("Skipping recording because no permission to affect time")
                tup = (ticket_id, change_time, "hours")
                self.log.debug("deleting ticket change %s %s %s %s" % tup)
                try:
                    delete_ticket_change(self, ticket_id, change_time, "hours")
                except Exception, e:
                    self.log.exception("FAIL: %s" % e)
                self.log.debug("hours change deleted")
                return
            self.log.debug("passed permissions check")
        @self.env.with_transaction()
        def fn(db):
            update_hours_to_floats(db, ticket_id)
            save_custom_field_value( db, ticket_id, "hours", '0')
            insert_totalhours_changes( db, ticket_id )
            update_totalhours_custom ( db, ticket_id )

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        hours = convertfloat(ticket['hours'])
        self.watch_hours(ticket, ticket['reporter']) # clears the hours
        #makes the hours a ticket change like all the other hours records
        t = Ticket (self.env, ticket.id)
        if hours > 0:
            t['hours']=str(hours);
            t.save_changes(ticket['reporter'])

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        self.watch_hours(ticket, author)

    def ticket_change_deleted(ticket, cdate, changes):
        """called when a ticket change is deleted"""
        self.watch_hours(ticket)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""

class TimeTrackingTicketValidator(Component):
    implements(ITicketManipulator)

    def __init__(self):
        pass

    def prepare_ticket(req, ticket, fields, actions):
        """not currently called"""

    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.

        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
        errors = []
        try:
            convertfloat(ticket.values['hours'])
        except KeyError:
            self.log.exception("The hours field was not submitted")
        except ValueError:
            errors.append(('Add Hours to Ticket', 'Value must be a number'))
        try:
            convertfloat(ticket.values['estimatedhours'])
        except KeyError:
            self.log.exception("The estimatedhours field was not submitted")
        except ValueError:
            errors.append(('Estimated Number of Hours', 'Value must be a number'))
        return errors
