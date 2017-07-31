# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index
from trac.wiki.formatter import format_to_html

SCHEMA = [
    Table('cards', key='id')[
        Column('id', auto_increment=True),
        Column('stack'),
        Column('rank', type='int64'),
        Column('title'),
        Column('color'),
        Index(['stack', 'rank']),
    ],
    Table('cards_stacks', key='name')[
        Column('name'),
        Column('version', type='int64'),
    ],
]


class Card(object):

    def __init__(self, id, stack, rank, title, color):
        self.id = id
        self.stack = stack
        self.rank = rank
        self.title = title
        self.color = color

    def serialized(self, env, context):
        return {
            'id': self.id,
            'stack': self.stack,
            'rank': self.rank,
            'title': self.title, 
            'title_html': format_to_html(env, context, self.title),
            'color': self.color,
        }

    @classmethod
    def add(cls, env, card, client_stack):
        with env.db_transaction as db:
            cursor = db.cursor()
            if not CardStack.check_and_bump_versions(env, [client_stack]):
                return False
            cursor.execute("""
                SELECT COALESCE(MAX(rank) + 1, 0)
                FROM cards
                WHERE stack = %s
            """, (card.stack,))
            card.rank = cursor.fetchone()[0]
            cursor.execute("""
            INSERT INTO cards
                        (stack, rank, title, color)
                 VALUES (%s, %s, %s, %s)
            """, (card.stack, card.rank, card.title, card.color))
            card.id = db.get_last_id(cursor, 'cards')
            return True

    @classmethod
    def update(cls, env, card, new_client_stack, old_client_stack):
        with env.db_transaction as db:
            cursor = db.cursor()

            cursor.execute("""
                SELECT stack, rank
                FROM cards
                WHERE id = %s
            """, (card.id,))
            old_stack, old_rank = cursor.fetchone()
            if card.stack == old_stack:
                if not CardStack.check_and_bump_versions(env, [new_client_stack]):
                    return False
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
                if old_stack != old_client_stack.name or not CardStack.check_and_bump_versions(env, [new_client_stack, old_client_stack]):
                    return False
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
                SET stack=%s, rank=%s, title=%s, color=%s
                WHERE id=%s
            """, (card.stack, card.rank, card.title, card.color, card.id))
            return True

    @classmethod
    def delete_by_id(cls, env, card_id, client_stack):
        with env.db_transaction as db:
            cursor = db.cursor()
            if not CardStack.check_and_bump_versions(env, [client_stack]):
                return False
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
            return True

    @classmethod
    def select_by_stack(cls, env, stack):
        rows = env.db_query("""
                SELECT id, stack, rank, title, color
                FROM cards
                WHERE stack=%s
                ORDER BY rank
                """, (stack,))
        return [Card(id, stack, rank, title, color) for id, stack, rank, title, color in rows]

    @classmethod
    def select_by_stacks(cls, env, stacks):
        if not stacks:
            return []
        stack_holder = ','.join(['%s'] * len(stacks))
        rows = env.db_query("""
                SELECT id, stack, rank, title, color
                FROM cards
                WHERE stack in (%s)
                ORDER BY stack, rank
                """ % stack_holder, list(stacks))
        return [Card(id, stack, rank, title, color) for id, stack, rank, title, color in rows]


class CardStack(object):

    def __init__(self, name, version):
        self.name = name
        self.version = version

    def serialized(self):
        return {
            'name': self.name,
            'version': self.version,
        }

    @classmethod
    def check_and_bump_versions(cls, env, stacks):
        with env.db_transaction as db:
            cursor = db.cursor()
            existing = cls.select_by_names(env, [s.name for s in stacks])
            current_version_by_name = dict((stack.name, stack.version) for stack in existing)

            # Check
            for stack in stacks:
                current_version = current_version_by_name.get(stack.name, 0)
                if stack.version != current_version:
                    return False

            # bump:
            for stack in stacks:
                if stack.name in current_version_by_name:
                    cursor.execute("""
                        UPDATE cards_stacks
                        SET version = version + 1
                        WHERE name=%s
                        """, (stack.name,))
                else:
                    cursor.execute("""
                        INSERT INTO cards_stacks (name, version)
                        VALUES (%s, %s)
                        """, (stack.name, 1))

            return True

    @classmethod
    def select_by_names(cls, env, names):
        if not names:
            return []
        names_holder = ','.join(['%s'] * len(names))
        rows = env.db_query("""
                SELECT name, version
                FROM cards_stacks
                WHERE name in (%s)
                ORDER BY name
                """ % names_holder, list(names))
        return [CardStack(name, version) for name, version in rows]
