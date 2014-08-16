# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index
from trac.util.datefmt import from_utimestamp, to_utimestamp


SCHEMA = [
    Table('timetrackingtasks', key='id')[
        Column('id', auto_increment=True),
        Column('name'),
        Column('description'),
        Column('project'),
        Column('category'),
        Column('year', type='int'),
        Column('estimated_hours', type='int'),
        Index(['year', 'category', 'project']),
    ],
    Table('timetrackinglogs', key='id')[
        Column('id', auto_increment=True),
        Column('user'),
        Column('date', type='int64'),
        Column('location'),
        Column('spent_hours', type='int'),
        Column('task_id', type='int'),
        Column('comment'),
        Index(['task_id']),
        Index(['user', 'date']),
    ],
]


class Task(object):

    def __init__(self, id, name, description, project, category, year, estimated_hours):
        self.id = id
        self.name = name
        self.description = description
        self.project = project
        self.category = category
        self.year = year
        self.estimated_hours = int(estimated_hours) if estimated_hours is not None else None

    @classmethod
    def add(cls, env, task):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
            INSERT INTO timetrackingtasks
                        (name, description, project, category, year, estimated_hours)
                 VALUES (%s, %s, %s, %s, %s, %s)
            """, (task.name, task.description, task.project, task.category, task.year, task.estimated_hours))
            task.id = db.get_last_id(cursor, 'timetrackingtasks')

    @classmethod
    def delete_by_ids(cls, env, ids):
        ids_sql = ','.join(["'%s'" % id for id in ids])
        with env.db_transaction as db:
            db("""
                DELETE FROM timetrackingtasks
                WHERE id in (%s)
            """ % ids_sql)

    @classmethod
    def update(cls, env, task):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                UPDATE timetrackingtasks
                SET name=%s, description=%s, project=%s, category=%s, year=%s, estimated_hours=%s
                WHERE id=%s
            """, (task.name, task.description, task.project, task.category, task.year, task.estimated_hours, task.id))

    @classmethod
    def select_by_id(cls, env, id):
        rows = env.db_query("""
                SELECT id, name, description, project, category, year, estimated_hours
                FROM timetrackingtasks
                WHERE id=%s
                """, (id,))
        if not rows:
            return None
        id, name, description, project, category, year, estimated_hours = rows[0]
        return Task(id, name, description, project, category, year, estimated_hours)

    @classmethod
    def select_by_year(cls, env, year):
        rows = env.db_query("""
                SELECT id, name, description, project, category, estimated_hours
                FROM timetrackingtasks
                WHERE year=%s
                ORDER BY category ASC, project ASC, name ASC
                """, (year,))
        return [Task(id, name, description, project, category, year, estimated_hours)
                for id, name, description, project, category, estimated_hours in rows]

    @classmethod
    def get_known_years(cls, env):
        rows = env.db_query("""
                SELECT DISTINCT year
                FROM timetrackingtasks
                ORDER BY year
                """)
        return [int(year) for (year,) in rows]


class LogEntry(object):

    def __init__(self, id, user, date, location, spent_hours, task_id, comment):
        self.id = id
        self.user = user
        self.date = date
        self.location = location
        self.spent_hours = int(spent_hours) if spent_hours is not None else None
        self.task_id = int(task_id) if task_id is not None else None
        self.comment = comment

    @classmethod
    def add(cls, env, entry):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
            INSERT INTO timetrackinglogs
                        (user, date, location, spent_hours, task_id, comment)
                 VALUES (%s, %s, %s, %s, %s, %s)
            """, (entry.user, to_utimestamp(entry.date), entry.location, entry.spent_hours, entry.task_id, entry.comment))
            entry.id = db.get_last_id(cursor, 'timetrackinglogs')

    @classmethod
    def delete_by_ids(cls, env, ids):
        ids_sql = ','.join(["'%s'" % id for id in ids])
        with env.db_transaction as db:
            db("""
                DELETE FROM timetrackinglogs
                WHERE id in (%s)
            """ % ids_sql)

    @classmethod
    def update(cls, env, entry):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                UPDATE timetrackinglogs
                SET date=%s, location=%s, spent_hours=%s, task_id=%s, comment=%s
                WHERE id=%s
            """, (to_utimestamp(entry.date), entry.location, entry.spent_hours, entry.task_id, entry.comment, entry.id))

    @classmethod
    def select_by_id(cls, env, id):
        rows = env.db_query("""
                SELECT id, user, date, location, spent_hours, task_id, comment
                FROM timetrackinglogs
                WHERE id=%s
                """, (id,))
        if not rows:
            return None
        id, user, date, location, spent_hours, task_id, comment = rows[0]
        return LogEntry(id, user, from_utimestamp(date), location, spent_hours, task_id, comment)

    @classmethod
    def select_by_task_ids(cls, env, task_ids):
        task_ids_sql = ','.join(["'%s'" % id for id in task_ids])
        rows = env.db_query("""
                SELECT id, user, date, location, spent_hours, task_id, comment
                FROM timetrackinglogs
                WHERE task_id in (%s)
                """ % task_ids_sql)
        return [LogEntry(id, user, from_utimestamp(date), location, spent_hours, task_id, comment) for id, user, date, location, spent_hours, task_id, comment in rows]

    @classmethod
    def select_by_user(cls, env, user):
        rows = env.db_query("""
                SELECT id, user, date, location, spent_hours, task_id, comment
                FROM timetrackinglogs
                WHERE user=%s
                ORDER BY date DESC, id DESC
                """, (user,))
        return [LogEntry(id, user, from_utimestamp(date), location, spent_hours, task_id, comment) for id, user, date, location, spent_hours, task_id, comment in rows]

    @classmethod
    def select_by_user_paginated(cls, env, user, page, max_per_page):
        print page, type(page)
        print max_per_page, type(max_per_page)
        rows = env.db_query("""
                SELECT id, user, date, location, spent_hours, task_id, comment
                FROM timetrackinglogs
                WHERE user=%s
                ORDER BY date DESC, id DESC
                LIMIT %s OFFSET %s
                """, (user, max_per_page, max_per_page * (page - 1)))
        return [LogEntry(id, user, from_utimestamp(date), location, spent_hours, task_id, comment) for id, user, date, location, spent_hours, task_id, comment in rows]

    @classmethod
    def count_by_user(cls, env, user):
        with env.db_query as db:
            return db("""
                    SELECT COUNT(*)
                    FROM timetrackinglogs
                    WHERE user=%s
                    """, (user,))[0][0]

