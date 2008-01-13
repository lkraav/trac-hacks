from trac.core import *
from trac.config import BoolOption
from trac.ticket.api import ITicketChangeListener
from announcerplugin.api import AnnouncementSystem, AnnouncementEvent

class TicketChangeEvent(AnnouncementEvent):
    def __init__(self, realm, category, target, 
                 comment=None, author=None, changes={},
                 attachment=None):
        AnnouncementEvent.__init__(self, realm, category, target)

        self.author = author
        self.comment = comment
        self.changes = changes
        self.attachment = attachment

class TicketChangeProducer(Component):
    implements(ITicketChangeListener)
    
    ignore_cc_changes = BoolOption('announcer', 'ignore_cc_changes', False,
        doc="""When true, the system will not send out announcement events if
        the only field that was changed was CC. A change to the CC field that
        happens at the same as another field will still result in an event
        being created.""")
    
    def __init__(self, *args, **kwargs):
        pass
        
    def ticket_created(self, ticket):
        announcer = AnnouncementSystem(ticket.env)
        announcer.send(
            TicketChangeEvent("ticket", "created", ticket,
                author=ticket['reporter']
            )
        )
        
    def ticket_changed(self, ticket, comment, author, old_values):
        if old_values.keys() == ['cc'] and not comment:
            return
            
        announcer = AnnouncementSystem(ticket.env)
        announcer.send(
            TicketChangeEvent("ticket", "changed", ticket, 
                comment, author, old_values
            )
        )

    def ticket_deleted(self, ticket):
        pass
    
