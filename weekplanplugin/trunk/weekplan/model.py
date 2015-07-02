# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index
from trac.util.datefmt import from_utimestamp, to_utimestamp
from trac.wiki.formatter import format_to_html

SCHEMA = [
    Table('weekplan', key='id')[
        Column('id', auto_increment=True),
        Column('plan'),
        Column('title'),
        Column('start', type='int64'),
        Column('end', type='int64'),
        Index(['plan', 'start', 'end']),
    ],
]


class WeekPlanEvent(object):

    def __init__(self, id, plan, title, start, end):
        self.id = id
        self.plan = plan
        self.title = title
        self.start = start
        self.end = end

    def serialized(self, env, context):
        return {
            'id': self.id,
            'title': self.title, 
            'title_html': format_to_html(env, context, self.title),
            'start': self.start.date().isoformat(),
            'end': self.end.date().isoformat(),
            'plan': self.plan, # Custom field
        }

    @classmethod
    def add(cls, env, event):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
            INSERT INTO weekplan
                        (plan, title, start, %s)
                 VALUES (%%s, %%s, %%s, %%s)
            """ % db.quote('end'), (event.plan, event.title, to_utimestamp(event.start), to_utimestamp(event.end)))
            event.id = db.get_last_id(cursor, 'weekplan')

    @classmethod
    def update(cls, env, event):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                UPDATE weekplan
                SET plan=%%s, title=%%s, start=%%s, %s=%%s
                WHERE id=%%s
            """ % db.quote('end'), (event.plan, event.title, to_utimestamp(event.start), to_utimestamp(event.end), event.id))

    @classmethod
    def delete_by_id(cls, env, event_id):
        with env.db_transaction as db:
            db("""
                DELETE FROM weekplan
                WHERE id=%s
            """, (event_id,))

    @classmethod
    def select_by_plan(cls, env, plan):
        with env.db_query as db:
            rows = db("""
                    SELECT id, plan, title, start, %s
                    FROM weekplan
                    WHERE plan=%%s
                    """ % db.quote('end'), (plan,))
            return [WeekPlanEvent(id, plan, title, from_utimestamp(start), from_utimestamp(end)) for id, plan, title, start, end in rows]

    @classmethod
    def select_by_plans_and_time(cls, env, plans, start, end):
        if not plans:
            return []
        with env.db_query as db:
            plan_holder = ','.join(['%s'] * len(plans))
            rows = db("""
                    SELECT id, plan, title, start, %s
                    FROM weekplan
                    WHERE plan IN (%s) AND start < %%s AND %s > %%s
                    """ % (db.quote('end'), plan_holder, db.quote('end')),
                    list(plans) + [to_utimestamp(end), to_utimestamp(start)])
            return [WeekPlanEvent(id, plan, title, from_utimestamp(start), from_utimestamp(end)) for id, plan, title, start, end in rows]
