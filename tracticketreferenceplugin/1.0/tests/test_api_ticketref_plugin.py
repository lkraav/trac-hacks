# -*- coding: utf-8 -*-

import pytest
from trac.ticket.model import Ticket
from tracopt.ticket.commit_updater import CommitTicketUpdater

from ticketref.model import TICKETREF

from utils import (create_ticket, create_tickets,
                   make_simple_ticketref, make_multi_ticketref)


# CommitTicketUpdater settings for test
CommitTicketUpdater.commands_close = "close closed closes fix fixed fixes"
CommitTicketUpdater.commands_refs = "ref ref. refs refer reference dup see"


@pytest.mark.parametrize(("message", "except_ids", "expected"), [
    (None, None, set([])),
    (u"", None, set([])),
    (u"refs. #1", None, set([1])),
    (u"refs. #1ab", None, set([1])),
    (u"refs. a#1b", None, set([])),
    (u"some refer #1, #3, some", None, set([1, 3])),
    (u"some refer #1,#3,#5 # 7 some", None, set([1, 3, 5])),
    (u"ref #1,#3  ref, #5 #7 refs", None, set([1, 3, 5, 7])),
    (u"ref #1,#3  ref #5, #7", None, set([1, 3, 5, 7])),
    (u"refs#1", None, set([1])),
    (u"reference#1 #3, #5", None, set([1, 3, 5])),
    (u"adding.\nrefs #1", None, set([1])),
    (u"adding.\nrefs #1 #3, #5", None, set([1, 3, 5])),
    (u"adding.\nsecond\nrefs #2", None, set([2])),
    (u"except ids\nrefs #1 #3", [3], set([1])),
    (u"except ids\nrefs #1 #3 #5", [1, 5], set([3])),
    (u"ref. #21", [23], set([21])),
    (u"ref. #21 #22", [23, 24], set([21, 22])),
    (u"ref. #3 #4", [1], set([3, 4])),
    (u"ref. #3 #4", [1, 3], set([4])),
    (u"ref. #6\ndup #7\nsee #8", None, set([6, 7, 8])),
    (u"ref. #6\ndup #7\nsee #8", [6], set([7, 8])),
    (u"fix #7\n - test\nfixed #8\n - test\nfixes #9", None, set([7, 8, 9])),
])
def test_tref_get_refs(tref, message, except_ids, expected):
    assert expected == tref._get_refs(message, except_ids)

def test_tref_has_ticket_refs(env, tref):
    ticket = create_ticket(env)
    assert not tref.has_ticket_refs(ticket)
    ticket[TICKETREF] = u"1"
    assert tref.has_ticket_refs(ticket)

@pytest.mark.parametrize(("value", "expected_msg"), [
    (u"abc", "Input only numbers for ticket ID: abc"),
])
def test_tref_validate_ticket(env, tref, value, expected_msg):
    ticket = create_ticket(env)
    ticket[TICKETREF] = value
    expected_field = env.config.get("ticket-custom", "ticketref.label")
    for field, msg in tref.validate_ticket(None, ticket):
        assert expected_field == field and expected_msg == msg
        break
    else:
        assert False

def test_tref_validate_ticket_with_own_id(env, tref):
    ticket = create_ticket(env)
    ticket[TICKETREF] = u"%s" % ticket.id
    expected_field = env.config.get("ticket-custom", "ticketref.label")
    expected_msg = "Ticket %s is this ticket ID, remove it." % ticket.id
    for field, msg in tref.validate_ticket(None, ticket):
        assert expected_field == field and expected_msg == msg
        break
    else:
        assert False

def test_tref_ticket_created_with_desc(env):
    target = create_ticket(env)
    ticket = Ticket(env)
    ticket["summary"] = u"reference in description"
    ticket["description"] = "refs #%s" % target.id
    ticket.insert()  # called TicketRefsPlugin.ticket_created()
    assert ticket.exists
    target = Ticket(env, target.id)
    assert target[TICKETREF] == u"%s" % ticket.id

def test_tref_ticket_created_with_field(env):
    target = create_ticket(env)
    ticket = Ticket(env)
    ticket["summary"] = u"has %s field" % TICKETREF
    ticket[TICKETREF] = u"%s" % target.id
    ticket.insert()  # called TicketRefsPlugin.ticket_created()
    assert ticket.exists
    target = Ticket(env, target.id)
    assert target[TICKETREF] == u"%s" % ticket.id

def test_tref_ticket_created_with_mixed(env):
    t1, t2 = create_tickets(env, 2)
    ticket = Ticket(env)
    ticket["summary"] = u"has desc and %s field" % TICKETREF
    ticket["description"] = "refs #%s" % t1.id
    ticket[TICKETREF] = u"%s" % t2.id
    ticket.insert()  # called TicketRefsPlugin.ticket_created()
    assert ticket.exists
    assert ticket[TICKETREF] == u"%s, %s" % (t1.id, t2.id)
    t1, t2 = Ticket(env, t1.id), Ticket(env, t2.id)
    assert t1[TICKETREF] == u"%s" % ticket.id
    assert t2[TICKETREF] == u"%s" % ticket.id

def test_tref_ticket_changed_with_comment(env):
    t1, t2, t3 = create_tickets(env, 3)
    # called TicketRefsPlugin.ticket_changed()
    assert t1.save_changes(author="user1",
                           comment="refs #%s, #%s" % (t2.id, t3.id))
    assert t1[TICKETREF] == u"%s, %s" % (t2.id, t3.id)
    t2, t3 = Ticket(env, t2.id), Ticket(env, t3.id)
    assert t2[TICKETREF] == u"%s" % t1.id
    assert t3[TICKETREF] == u"%s" % t1.id

def test_tref_ticket_changed_with_field(env):
    t1, t2, t3 = create_tickets(env, 3)
    t1[TICKETREF] = u"%s, %s" % (t2.id, t3.id)
    assert t1.save_changes()  # called TicketRefsPlugin.ticket_changed()
    t2, t3 = Ticket(env, t2.id), Ticket(env, t3.id)
    assert t2[TICKETREF] == u"%s" % t1.id
    assert t3[TICKETREF] == u"%s" % t1.id

def test_tref_ticket_changed_with_mixed(env):
    t1, t2, t3 = create_tickets(env, 3)
    t1[TICKETREF] = u"%s" % t3.id
    # called TicketRefsPlugin.ticket_changed()
    assert t1.save_changes(author="user1", comment="refs #%s" % t2.id)
    assert t1[TICKETREF] == u"%s, %s" % (t2.id, t3.id)
    t2, t3 = Ticket(env, t2.id), Ticket(env, t3.id)
    assert t2[TICKETREF] == u"%s" % t1.id
    assert t3[TICKETREF] == u"%s" % t1.id

def test_tref_ticket_deleted(env):
    t1, t2 = make_simple_ticketref(env)
    assert t2[TICKETREF] == u"%s" % t1.id
    t1.delete()  # called TicketRefsPlugin.ticket_deleted()
    t2 = Ticket(env, t2.id)
    assert t2[TICKETREF] is None
