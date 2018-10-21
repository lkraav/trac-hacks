# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index
from trac.util.datefmt import from_utimestamp, to_utimestamp


SCHEMA = [
    Table('packagerepository_files', key='id')[
        Column('id', auto_increment=True),
        Column('repository'),
        Column('package'),
        Column('version'),
        Column('filename'),
        Column('comment'),
        Index(['repository', 'package']),
    ],
]


class PackageRepositoryFile(object):

    def __init__(self, id, repository, package, version, filename, comment):
        self.id = id
        self.repository = repository
        self.package = package
        self.version = version
        self.filename = filename
        self.comment = comment

    @classmethod
    def add(cls, env, file):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
            INSERT INTO packagerepository_files
                        (repository, package, version, filename, comment)
                 VALUES (%s, %s, %s, %s, %s)
            """, (file.repository, file.package, file.version, file.filename, file.comment))
            file.id = db.get_last_id(cursor, 'packagerepository_files')

    @classmethod
    def delete_by_ids(cls, env, ids):
        if not ids:
            return
        id_holder = ','.join(['%s'] * len(ids))
        with env.db_transaction as db:
            db("""
                DELETE FROM packagerepository_files
                WHERE id in (%s)
            """ % id_holder, list(ids))

    @classmethod
    def update(cls, env, file):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                UPDATE packagerepository_files
                SET repository=%s, package=%s, version=%s, filename=%s, comment=%s
                WHERE id=%s
            """, (file.repository, file.package, file.version, file.filename, file.comment, file.id))

    @classmethod
    def select_by_id(cls, env, id):
        rows = env.db_query("""
                SELECT id, repository, package, version, filename, comment
                FROM packagerepository_files
                WHERE id=%s
                """, (id,))
        if not rows:
            return None
        id, repository, package, version, filename, comment = rows[0]
        return PackageRepositoryFile(id, repository, package, version, filename, comment)

    @classmethod
    def select_by_repository(cls, env, repository):
        rows = env.db_query("""
                SELECT id, repository, package, version, filename, comment
                FROM packagerepository_files
                WHERE repository=%s
                ORDER BY repository, package, version, filename
                """, (repository,))
        return [PackageRepositoryFile(id, repository, package, version, filename, comment)
                for id, repository, package, version, filename, comment in rows]

    @classmethod
    def select_paginated(cls, env, page, max_per_page):
        rows = env.db_query("""
                SELECT id, repository, package, version, filename, comment
                FROM packagerepository_files
                ORDER BY repository, package, version, filename
                LIMIT %s OFFSET %s
                """, (max_per_page, max_per_page * (page - 1)))
        return [PackageRepositoryFile(id, repository, package, version, filename, comment)
                for id, repository, package, version, filename, comment in rows]

    @classmethod
    def total_count(cls, env):
        with env.db_query as db:
            return db("""
                    SELECT COUNT(*)
                    FROM packagerepository_files
                    """)[0][0]
