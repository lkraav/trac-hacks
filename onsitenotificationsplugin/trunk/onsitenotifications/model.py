# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index


SCHEMA = [
    Table('onsitenotification', key='id')[
        Column('id', auto_increment=True),
        Column('sid'),
        Column('authenticated', type='int'),
        Column('message'),
        Column('realm'),
        Column('target'),
        Index(['sid'])],
]


class OnSiteMessage(object):

    __slots__ = ('env', 'values')

    fields = ('id', 'sid', 'authenticated', 'message', 'realm', 'target')

    def __init__(self, env):
        self.env = env
        self.values = {}

    def __getitem__(self, name):
        if name not in self.fields:
            raise KeyError(name)
        return self.values.get(name)

    def __setitem__(self, name, value):
        if name not in self.fields:
            raise KeyError(name)
        self.values[name] = value

    def _from_database(self, id, sid, authenticated, message, realm, target):
        self['id'] = id
        self['sid'] = sid
        self['authenticated'] = int(authenticated)
        self['message'] = message
        self['realm'] = realm
        self['target'] = target

    @classmethod
    def add(cls, env, sid, authenticated, message, realm, target):
        with env.db_transaction as db:
            db("""
                INSERT INTO onsitenotification (sid, authenticated, message,
                                                realm, target)
                VALUES (%s, %s, %s, %s, %s)
            """, (sid, int(authenticated), message, realm, target))

    @classmethod
    def delete(cls, env, message_id):
        with env.db_transaction as db:
            db("DELETE FROM onsitenotification WHERE id = %s", (message_id,))

    @classmethod
    def delete_by_sid(cls, env, sid, authenticated):
        with env.db_transaction as db:
            db("""
                DELETE FROM onsitenotification
                WHERE sid = %s AND authenticated = %s
            """, (sid, int(authenticated)))

    @classmethod
    def select(cls, env, order=None, **kwargs):
        with env.db_query as db:
            conditions = []
            args = []
            for name, value in sorted(kwargs.iteritems()):
                if name.endswith('_'):
                    name = name[:-1]
                conditions.append(db.quote(name) + '=%s')
                args.append(value)
            query = 'SELECT id, sid, authenticated, message, realm, target ' \
                    'FROM onsitenotification'
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            if order:
                if not isinstance(order, (tuple, list)):
                    order = (order,)
                query += ' ORDER BY ' + \
                         ', '.join(db.quote(name) for name in order)
            cursor = db.cursor()
            cursor.execute(query, args)
            for row in cursor:
                message = OnSiteMessage(env)
                message._from_database(*row)
                yield message

    @classmethod
    def select_by_id(cls, env, message_id):
        r = list(cls.select(env, id=message_id))
        return r[0] if r else None

    @classmethod
    def select_by_sid(cls, env, sid, authenticated):
        return list(cls.select(env, sid=sid, authenticated=int(authenticated)))
