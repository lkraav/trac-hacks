# -*- coding: utf-8 -*-

from datetime import datetime

from trac.ticket.model import Ticket
from trac.util.datefmt import utc, to_utimestamp

from utils import cnv_list2text, cnv_sorted_refs, cnv_text2list

CUSTOM_FIELDS = [
    {
        "name": "ticketref",
        "type": "textarea",
        "properties": [
                        ("ticketref.label", "Relationships"),
                        ("ticketref.cols", "68"),
                        ("ticketref.rows", "1"),
        ],
    },
]
TICKETREF = CUSTOM_FIELDS[0]["name"]

UPDATE_TICKET = "UPDATE ticket SET changetime=%s WHERE id=%s"

SELECT_TICKETREF = "SELECT value FROM ticket_custom "\
                   "WHERE ticket=%%s AND name='%s'" % TICKETREF
INSERT_TICKETREF = "INSERT INTO ticket_custom (ticket, name, value) "\
                   "VALUES (%%s, '%s', %%s)" % TICKETREF
UPDATE_TICKETREF = "UPDATE ticket_custom SET value=%%s "\
                   "WHERE ticket=%%s AND name='%s'" % TICKETREF
DELETE_TICKETREF = "DELETE FROM ticket_custom "\
                   "WHERE ticket=%%s AND name='%s'" % TICKETREF

INSERT_TICKETCHG = "INSERT INTO ticket_change "\
                   "(ticket, time, author, field, oldvalue, newvalue) "\
                   "VALUES (%%s, %%s, %%s, '%s', %%s, %%s)" % TICKETREF


class TicketLinks(object):
    """A model for the ticket links as cross reference."""

    def __init__(self, env, ticket):
        self.env = env
        if not isinstance(ticket, Ticket):
            ticket = Ticket(self.env, ticket)
        self.ticket = ticket
        self.time_stamp = to_utimestamp(datetime.now(utc))

    def add_reference(self, refs):
        with self.env.db_transaction as db:
            for ref_id in refs:
                for value, in db(SELECT_TICKETREF, (self.ticket.id,)):
                    target_refs = cnv_text2list(value)
                    if ref_id not in target_refs:
                        target_refs.add(ref_id)
                        new_text = cnv_list2text(target_refs)
                        db(UPDATE_TICKETREF, (new_text, self.ticket.id))
                        self.ticket[TICKETREF] = \
                            cnv_sorted_refs(self.ticket[TICKETREF],
                                            set([ref_id]))
                    break
                else:
                    db(INSERT_TICKETREF, (self.ticket.id, ref_id))
                    self.ticket[TICKETREF] = u"%s" % ref_id

    def remove_cross_reference(self, refs, author):
        with self.env.db_transaction as db:
            for ref_id in refs:
                value = None
                for value, in db(SELECT_TICKETREF, (ref_id,)):
                    break
                value = value or ""
                target_refs = cnv_text2list(value)
                target_refs.remove(self.ticket.id)
                if target_refs:
                    new_text = cnv_list2text(target_refs)
                    db(UPDATE_TICKETREF, (new_text, ref_id))
                else:
                    new_text = ""
                    db(DELETE_TICKETREF, (ref_id,))
                db(INSERT_TICKETCHG, (ref_id, self.time_stamp, author,
                                      value.strip(), new_text))
                db(UPDATE_TICKET, (self.time_stamp, ref_id))

    def add_cross_reference(self, refs, author):
        with self.env.db_transaction as db:
            for ref_id in refs:
                for value, in db(SELECT_TICKETREF, (ref_id,)):
                    target_refs = cnv_text2list(value)
                    if self.ticket.id not in target_refs:
                        target_refs.add(self.ticket.id)
                        new_text = cnv_list2text(target_refs)
                        db(UPDATE_TICKETREF, (new_text, ref_id))
                        db(INSERT_TICKETCHG,
                           (ref_id, self.time_stamp, author, value.strip(),
                            new_text))
                        db(UPDATE_TICKET, (self.time_stamp, ref_id))
                    break
                else:
                    db(INSERT_TICKETREF, (ref_id, self.ticket.id))
                    db(INSERT_TICKETCHG,
                       (ref_id, self.time_stamp, author, "",
                        self.ticket.id))
                    db(UPDATE_TICKET, (self.time_stamp, ref_id))

    def create(self):
        refs = cnv_text2list(self.ticket[TICKETREF])
        self.add_cross_reference(refs, self.ticket["reporter"])

    def change(self, author, old_refs_text):
        old_refs = cnv_text2list(old_refs_text)
        new_refs = cnv_text2list(self.ticket[TICKETREF])
        with self.env.db_transaction as db:
            self.remove_cross_reference(old_refs - new_refs, author)
            self.add_cross_reference(new_refs - old_refs, author)

    def delete(self):
        refs = cnv_text2list(self.ticket[TICKETREF])
        self.remove_cross_reference(refs, "admin")
