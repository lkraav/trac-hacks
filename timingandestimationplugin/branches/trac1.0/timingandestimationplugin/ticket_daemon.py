from trac.ticket import ITicketChangeListener, Ticket, ITicketManipulator
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
    cursor = db.cursor()
    cursor.execute("UPDATE ticket_custom SET value=%s "
                   "WHERE ticket=%s AND name=%s", (value, ticket_id, field))

    if cursor.rowcount==0:
        cursor.execute("INSERT INTO ticket_custom (ticket,name, "
                       "value) VALUES(%s,%s,%s)", (ticket_id, field, value))

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


class TimeTrackingTicketObserver(Component):
    implements(ITicketChangeListener)
    def __init__(self):
        pass

    def watch_hours(self, ticket):
        ticket_id = ticket.id
        @self.env.with_transaction()
        def fn(db):
            save_custom_field_value( db, ticket_id, "hours", '0')
            insert_totalhours_changes( db, ticket_id )
            update_totalhours_custom ( db, ticket_id )

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        self.watch_hours(ticket)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified."""
        self.watch_hours(ticket)

    def ticket_change_deleted(ticket, cdate, changes):
        """called when a ticket change is deleted"""
        self.watch_hours(ticket)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        pass


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
        #some european countries use , as the decimal separator
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
