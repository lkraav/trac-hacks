# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index
from trac.wiki.formatter import format_to_html

SCHEMA = [
    Table('cards', key='id')[
        Column('id', auto_increment=True),
        Column('stack'),
        Column('rank', type='int64'),
        Column('title'),
        Index(['stack', 'rank']),
    ],
]


class Card(object):

    def __init__(self, id, stack, rank, title):
        self.id = id
        self.stack = stack
        self.rank = rank
        self.title = title

    def serialized(self, env, context):
        return {
            'id': self.id,
            'stack': self.stack,
            'rank': self.rank,
            'title': self.title, 
            'title_html': format_to_html(env, context, self.title),
        }

    @classmethod
    def add(cls, env, card):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                SELECT COALESCE(MAX(rank) + 1, 0)
                FROM cards
                WHERE stack = %s
            """, (card.stack,))
            card.rank = cursor.fetchone()[0]
            cursor.execute("""
            INSERT INTO cards
                        (stack, rank, title)
                 VALUES (%s, %s, %s)
            """, (card.stack, card.rank, card.title))
            card.id = db.get_last_id(cursor, 'cards')

    @classmethod
    def update(cls, env, card):
        with env.db_transaction as db:
            cursor = db.cursor()

            cursor.execute("""
                SELECT stack, rank
                FROM cards
                WHERE id = %s
            """, (card.id,))
            old_stack, old_rank = cursor.fetchone()
            if card.stack == old_stack:
                if card.rank < old_rank:
                    cursor.execute("""
                        UPDATE cards
                        SET rank = rank + 1
                        WHERE stack=%s AND rank >= %s AND rank < %s
                    """, (card.stack, card.rank, old_rank))
                elif card.rank > old_rank:
                    cursor.execute("""
                        UPDATE cards
                        SET rank = rank - 1
                        WHERE stack=%s AND rank > %s AND rank <= %s
                    """, (card.stack, old_rank, card.rank))
            else:
                cursor.execute("""
                    UPDATE cards
                    SET rank = rank - 1
                    WHERE stack=%s AND rank > %s
                """, (old_stack, old_rank))
                cursor.execute("""
                    UPDATE cards
                    SET rank = rank + 1
                    WHERE stack=%s AND rank >= %s
                """, (card.stack, card.rank))

            cursor.execute("""
                UPDATE cards
                SET stack=%s, rank=%s, title=%s
                WHERE id=%s
            """, (card.stack, card.rank, card.title, card.id))

    @classmethod
    def delete_by_id(cls, env, card_id):
        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                SELECT stack, rank
                FROM cards
                WHERE id = %s
            """, (card_id,))
            stack, rank = cursor.fetchone()
            cursor.execute("""
                UPDATE cards
                SET rank = rank - 1
                WHERE stack=%s AND rank > %s
            """, (stack, rank))
            cursor.execute("""
                DELETE FROM cards
                WHERE id=%s
            """, (card_id,))

    @classmethod
    def select_by_stack(cls, env, stack):
        rows = env.db_query("""
                SELECT id, stack, rank, title
                FROM cards
                WHERE stack=%s
                ORDER BY rank
                """, (stack,))
        return [Card(id, stack, rank, title) for id, stack, rank, title in rows]

    @classmethod
    def select_by_stacks(cls, env, stacks):
        stack_sql = ','.join(["'%s'" % stack for stack in stacks])
        rows = env.db_query("""
                SELECT id, stack, rank, title
                FROM cards
                WHERE stack in (%s)
                ORDER BY stack, rank
                """ % stack_sql)
        return [Card(id, stack, rank, title) for id, stack, rank, title in rows]
