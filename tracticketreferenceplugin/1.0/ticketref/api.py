# -*- coding: utf-8 -*-
from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.api import ITicketChangeListener, ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.translation import domain_functions
from tracopt.ticket.commit_updater import CommitTicketUpdater

from model import CUSTOM_FIELDS, TICKETREF, TicketLinks
from utils import cnv_sorted_refs

_, add_domain = domain_functions("ticketref", ("_", "add_domain"))


class TicketRefsPlugin(Component):
    """ Extend custom field for ticket cross-reference """

    implements(IEnvironmentSetupParticipant,
               ITicketChangeListener, ITicketManipulator)

    def __init__(self):
        add_domain(self.env.path, resource_filename(__name__, "locale"))

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        for field in CUSTOM_FIELDS:
            if field["name"] not in self.config["ticket-custom"]:
                return True
        return False

    def upgrade_environment(self, db):
        custom = self.config["ticket-custom"]
        for field in CUSTOM_FIELDS:
            if field["name"] not in custom:
                custom.set(field["name"], field["type"])
                for key, value in field["properties"]:
                    custom.set(key, value)
                self.config.save()

    def has_ticket_refs(self, ticket):
        refs = ticket[TICKETREF]
        return refs and refs.strip()

    # ITicketChangeListener methods
    def ticket_created(self, ticket):
        links = None
        desc_refs = self._get_refs(ticket["description"])
        if desc_refs:
            ticket[TICKETREF] = cnv_sorted_refs(ticket[TICKETREF], desc_refs)
            links = TicketLinks(self.env, ticket)
            links.add_reference(desc_refs)

        if self.has_ticket_refs(ticket):
            if not links:
                links = TicketLinks(self.env, ticket)
            try:
                links.create()
            except Exception, err:
                self.log.error("TicketRefsPlugin: ticket_created %s" % err)

    def ticket_changed(self, ticket, comment, author, old_values):
        links = None
        need_change = TICKETREF in old_values

        com_refs = self._get_refs(comment, [ticket.id])
        if com_refs:
            links = TicketLinks(self.env, ticket)
            links.add_reference(com_refs)
            need_change = True

        if need_change:
            if not links:
                links = TicketLinks(self.env, ticket)
            try:
                links.change(author, old_values.get(TICKETREF))
            except Exception, err:
                self.log.error("TicketRefsPlugin: ticket_changed %s" % err)

    def ticket_deleted(self, ticket):
        if self.has_ticket_refs(ticket):
            links = TicketLinks(self.env, ticket)
            try:
                links.delete()
            except Exception, err:
                self.log.error("TicketRefsPlugin: ticket_deleted %s" % err)

    def _get_refs(self, message, except_ids=None):
        ref_ids = set([])
        ticket_updator = self._get_commit_ticket_updator()
        tickets = ticket_updator._parse_message(message or u"")
        if tickets:
            ref_ids = set(tickets.keys())
        if except_ids:
            exc_ids = [i for i in ref_ids if i in except_ids]
            for id_ in exc_ids:
                ref_ids.remove(id_)
        return ref_ids

    def _get_commit_ticket_updator(self):
        ticket_updator = self.compmgr.components.get(CommitTicketUpdater)
        if not ticket_updator:
            ticket_updator = CommitTicketUpdater(self.compmgr)
            self.compmgr.components[CommitTicketUpdater] = ticket_updator
        return ticket_updator

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        if self.has_ticket_refs(ticket):
            _prop = ("ticket-custom", "ticketref.label")
            for _id in ticket[TICKETREF].replace(",", " ").split():
                try:
                    ref_id = int(_id)
                    assert ref_id != ticket.id
                    Ticket(self.env, ref_id)
                except ValueError:
                    msg = _("Input only numbers for ticket ID: %s") % _id
                    yield self.env.config.get(*_prop), msg
                except AssertionError:
                    msg = _("Ticket %s is this ticket ID, remove it.") % ref_id
                    yield self.env.config.get(*_prop), msg
                except Exception, err:
                    yield self.env.config.get(*_prop), err
