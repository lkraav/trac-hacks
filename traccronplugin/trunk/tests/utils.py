# -*- coding: utf-8 -*-
import sys
from datetime import datetime, timedelta

from trac.ticket.api import TicketSystem
from trac.ticket.model import Milestone, Ticket

_IGNORE_UNLOGGED_MESSAGES = [
    'stop existing ticker',
]


def has_log_message(caplog, expected_messages, strict=True):
    log_status = dict((msg, False) for msg in expected_messages)
    for log in caplog.records():
        for msg in expected_messages:
            if log.message.startswith(msg):
                log_status[msg] = True
                break
        else:
            assert False, 'unknown message: "%s"' % log.message

    if strict:
        for msg, is_logged in log_status.items():
            if msg in _IGNORE_UNLOGGED_MESSAGES:
                continue
            assert is_logged, 'unlogged message: "%s"' % msg
    return True


def compat_attrgetter(*args):
    from operator import attrgetter
    if sys.version_info[:2] == (2, 4):
        return lambda obj: tuple(attrgetter(attr)(obj) for attr in args)
    else:  # version >= 2.5
        return attrgetter(*args)


def compat_itemgetter(*args):
    from operator import itemgetter
    if sys.version_info[:2] == (2, 4) and len(args) != 1:
        return lambda obj: tuple(itemgetter(item)(obj) for item in args)
    else:  # version >= 2.5
        return itemgetter(*args)


def update_value(field, value):
    def _update_value(f):
        def __update_value(*args, **kwargs):
            ticket = f(*args, **kwargs)
            ticket[field] = value
            when = kwargs.get('when')
            if when is not None:
                changetime = ticket['changetime']
                if changetime is not None:
                    when = changetime
                when += timedelta(seconds=1)
            assert ticket.save_changes(when=when)
            return ticket
        return __update_value
    return _update_value


def create_ticket(env, **kwargs):
    ticket_fields = map(compat_itemgetter('name'),
                        TicketSystem(env).get_ticket_fields())
    t = Ticket(env)
    t['summary'] = '%s - test ticket' % datetime.now().strftime('%H:%M:%S.%f')
    t['description'] = 'this ticket is for testing'
    for field in kwargs:
        if field in ticket_fields:
            t[field] = kwargs.get(field)
    t.insert(when=kwargs.get('when'))
    assert t.exists
    return t


@update_value('status', 'new')
def create_new_ticket(env, **kwargs):
    return create_ticket(env, **kwargs)


def create_new_tickets(env, num, owner='user1', when=None):
    return [create_new_ticket(env, owner=owner, when=when) for _ in range(num)]


def create_orphaned_ticket(env, reporter='user1', when=None):
    t = Ticket(env)
    t['summary'] = 'orphaned test'
    t['description'] = 'orphaned ticket for test'
    t['reporter'] = reporter
    t.insert(when=when)
    assert t.exists
    # update manually since 'orphaned' means it is never changed
    db = env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute("update ticket set status='new' where id=%s", (t.id,))
    db.commit()
    return t


def get_or_create_milestone(env, name='ms1', duedate=0):
    from trac.resource import ResourceNotFound
    try:
        m = Milestone(env, name=name)
    except ResourceNotFound:
        m = Milestone(env)
        m.name = name
        m.due = duedate
        m.insert()
        assert m.exists
    return m


def create_milestone_ticket(env, name, duedate, owner, reporter):
    @update_value('milestone', name)
    def create_ticket_with_milestone(env, **kwargs):
        return create_ticket(env, **kwargs)

    m = get_or_create_milestone(env, name=name, duedate=duedate)
    t = create_ticket_with_milestone(env, owner=owner, reporter=reporter)
    return m, t
