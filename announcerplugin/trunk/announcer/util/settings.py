# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Robert Corsaro
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import pickle

from announcer.api import istrue


def encode(*args):
    return pickle.dumps(args)


def decode(v):
    try:
        return pickle.loads(str(v))
    except Exception:
        return tuple(), None


class SubscriptionSetting(object):
    """Encapsulate user text subscription and filter settings.

    Subscription settings have default values, usually trac properties,
    and user session attribute settings.  If the user setting is unset,
    then the default value will be returned.
    """

    def __init__(self, env, name, default_value=None,
                 default_dists=('email',)):
        self.default = {
            'value': default_value,
            'dists': default_dists
        }
        self.env = env
        self.name = name

    def set_user_setting(self, session, value=None, dists=('email',),
                         save=True):
        """Sets session attribute."""
        session[self._attr_name()] = encode(dists, value)
        if save:
            session.save()

    def get_user_setting(self, sid):
        """Returns tuple of (value, authenticated)."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value, authenticated
              FROM session_attribute
             WHERE sid=%s
               AND name=%s
        """, (sid, self._attr_name()))
        row = cursor.fetchone()
        if row:
            pair = decode(row[0])
            authenticated = istrue(row[1])
        else:
            pair = (self.default['dists'], self.default['value'])
            authenticated = False

        # We use None here so that Genshi templates check their checkboxes
        # properly and without confusion.
        return pair + (authenticated,)

    def get_subscriptions(self, match):
        """Generates tuples of (distributor, sid, authenticated, email).

        `match` should is passed the string value of the setting and should
        return true or false depending on whether the subscription matches.

        Tuples are suitable for yielding from IAnnouncementSubscriber's
        subscriptions method.
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT sid, authenticated, value
              FROM session_attribute
             WHERE name=%s
        """, (self._attr_name(),))
        for result in cursor.fetchall():
            dists, val = decode(result[2])
            for dist in dists:
                if match(dist, val):
                    authenticated = istrue(result[1])
                    yield (dist, result[0], authenticated, None)

    def _attr_name(self):
        return 'sub_%s' % self.name


class BoolSubscriptionSetting(object):
    """Encapsulate boolean user subscription and filter settings.

    Subscription settings have default values, usually trac properties,
    and user session attribute settings.  If the user setting is unset,
    then the default value will be returned.
    """

    def __init__(self, env, name, default_value=None,
                 default_dists=('email',)):
        self.default = {
            'value': default_value,
            'dists': default_dists
        }
        self.env = env
        self.name = name

    def set_user_setting(self, session, value=None, dists=('email',),
                         save=True):
        """Sets session attribute to 1 or 0."""
        if istrue(value):
            session[self._attr_name()] = encode(dists, '1')
        else:
            session[self._attr_name()] = encode(dists, '0')
        if save:
            session.save()

    def get_user_setting(self, sid):
        """Returns tuple of (value, authenticated).

        Value is always True or None.  This will work with Genshi template
        checkbox logic.
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value, authenticated
              FROM session_attribute
             WHERE sid=%s
               AND name=%s
        """, (sid, self._attr_name()))
        row = cursor.fetchone()
        if row:
            dists, v = decode(row[0])
            value = istrue(v)
            authenticated = istrue(row[1])
        else:
            dists = self.default['dists']
            value = istrue(self.default['value'])
            authenticated = False

        # We use None here so that Genshi templates check their checkboxes
        # properly and without confusion.
        return dists, value and True or None, authenticated

    def get_subscriptions(self):
        """Generates tuples of (distributor, sid, authenticated, email).

        Tuples are suitable for yielding from IAnnouncementSubscriber's
        subscriptions method.
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT sid, authenticated, value
              FROM session_attribute
             WHERE name=%s
        """, (self._attr_name(),))
        for result in cursor.fetchall():
            dists, val = decode(result[2])
            for dist in dists:
                if istrue(val):
                    authenticated = istrue(result[1])
                    yield (dist, result[0], authenticated, None)

    def _attr_name(self):
        return 'sub_%s' % self.name
