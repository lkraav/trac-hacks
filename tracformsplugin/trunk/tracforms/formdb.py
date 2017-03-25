# -*- coding: utf-8 -*-

import re
import time
import urlparse

from trac.cache import cached
from trac.config import BoolOption, ListOption, Option
from trac.core import implements
from trac.db import Column, DatabaseManager, Index, Table
from trac.resource import Resource, resource_exists
from trac.search.api import search_to_sql
from trac.web.chrome import Chrome

from api import IFormDBObserver, _
from compat import json
from tracdb import DBComponent
from util import is_number, parse_history, resource_from_page, xml_unescape

__all__ = ['FormDBComponent', 'format_author']


class FormDBComponent(DBComponent):
    """Provides form update methods and schema components."""

    implements(IFormDBObserver)

    apply_schema = True

    parent_blacklist = Option(
        'forms', 'parent_blacklist', 'wiki:PageTemplates/*,/newticket',
        doc="""Deaktivate form submission from these (parent) resources.
            Resources are specified as comma-separated list of paths and/or
            <realm>:<resource_id> pairs, even with REGEXP pattern supported 
            for resource IDs in the latter specifier type.""")

    show_fullname = BoolOption(
        'forms', 'show_fullname', False,
        doc="Display full names instead of usernames if available.")

    show_fullname_pos = ListOption(
        'forms', 'show_fullname_position', 'macro',
        doc="""Comma-separated list containing one or more of the possible
            positional descriptors 'change', 'macro', 'value'.  Default is
            to show full names in 'macro' content only.
            """)

    def __init__(self):
        # Preprocess blacklist configuration option.
        listd = {}
        for elem in self.parent_blacklist.split(','):
            res = elem.split(':', 1)
            # Result is a Trac resource realm or a special context without
            #   resource ID, i.e. /newticket
            if [elem] == res:
                if listd.get('paths'):
                    listd['paths'].append(res[0])
                else:
                    listd['paths'] = res
            else:
                if listd.get(res[0]):
                    listd[res[0]].append(res[1])
                else:
                    listd[res[0]] = [res[1]]
        self.parent_blacklisted = listd

    # abstract TracForms update methods

    def get_tracform_ids(self, src):
        """Returns all child forms of resource specified by parent realm and
        parent id as a list of tuples (form_id and corresponding subcontext).
        """
        return [(int(form_id), subcontext)
                for form_id, subcontext in self.env.db_query("""
                    SELECT id, subcontext FROM forms
                    WHERE realm=%s AND resource_id=%s
                    """, (src[0], src[1]))]

    def get_tracform_meta(self, src):
        """
        Returns the meta information about a form based on a form id (int or
        long) or context (parent realm, parent id, TracForms subcontext).
        """
        sql = """
                SELECT id, realm, resource_id, subcontext, author, time,
                       keep_history, track_fields
                FROM forms %s
                """
        if not is_number(src):
            sql %= "WHERE realm=%s AND resource_id=%s AND subcontext=%s"
        else:
            sql %= "WHERE id=%s"
        form_id = None
        realm = None
        resource_id = None
        subcontext = None
        if not is_number(src):
            realm, resource_id, subcontext = src
        else:
            form_id = src
            src = tuple([src], )
        print(src, sql)
        for row in self.env.db_query(sql, src):
            return row
        return form_id, realm, resource_id, subcontext, None, None, None, None

    def get_tracform_state(self, src):
        sql = "SELECT state FROM forms "
        if not is_number(src):
            sql += "WHERE realm=%s AND resource_id=%s AND subcontext=%s"
        else:
            sql += "WHERE id=%s"
            src = tuple([src], )
        for state, in self.env.db_query(sql, src):
            return state

    def save_tracform_allowed(self, path_or_realm, resource_id):
        if not resource_id:
            if path_or_realm not in self.parent_blacklisted.get('paths', []):
                return True
        else:
            if path_or_realm not in self.parent_blacklisted.keys():
                return True
            else:
                for pattern in self.parent_blacklisted[path_or_realm]:
                    if re.match(pattern, resource_id):
                        return False
                return True
        return False

    def save_tracform(self, src, state, author,
                      base_version=None, keep_history=False,
                      track_fields=False):
        (form_id, realm, resource_id, subcontext, last_updater,
         last_updated_on, form_keep_history,
         form_track_fields) = self.get_tracform_meta(src)

        if form_keep_history is not None:
            keep_history = form_keep_history
        old_state = form_id and self.get_tracform_state(form_id) or '{}'
        if form_track_fields is not None:
            track_fields = form_track_fields

        if base_version is not None:
            base_version = int(base_version or 0)

        if ((base_version is None and last_updated_on is None) or
                (base_version == last_updated_on)):
            if state != old_state and \
                    self.save_tracform_allowed(realm, resource_id):
                updated_on = int(time.time())
                with self.env.db_transaction as db:
                    if form_id is None:
                        cursor = db.cursor()
                        cursor.execute("""
                            INSERT INTO forms (realm, resource_id, subcontext,
                                               state, author, time)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """, (realm, resource_id, subcontext, state,
                                  author, updated_on))
                        form_id = db.get_last_id(cursor, 'forms')
                    else:
                        db("""
                            UPDATE forms
                            SET state=%s, author=%s, time=%s
                            WHERE id=%s
                            """, (state, author, updated_on, form_id))
                        if keep_history:
                            db("""
                            INSERT INTO forms_history
                                    (id, time, author, old_state)
                                    VALUES (%s, %s, %s, %s)
                            """, (form_id, last_updated_on,
                                  last_updater, old_state))
                    if track_fields:
                        # Break down old version and new version.
                        old_fields = json.loads(old_state)
                        new_fields = json.loads(state or '{}')
                        updated_fields = []
                        for field, old_value in old_fields.iteritems():
                            if new_fields.get(field) != old_value:
                                updated_fields.append(field)
                        for field in new_fields:
                            if old_fields.get(field) is None:
                                updated_fields.append(field)
                        self.log.debug('UPDATED: ', updated_fields)
                        for field in updated_fields:
                            for count, in db("""
                                    SELECT COUNT(*)
                                    FROM forms_fields
                                    WHERE id=%s AND field=%s""", (form_id,
                                                                  field)):
                                if count:
                                    db("""
                                        UPDATE forms_fields
                                        SET author=%s, time=%s
                                        WHERE id=%s AND field=%s
                                        """, (author, updated_on,
                                              form_id, field))
                                else:
                                    db("""
                                        INSERT INTO forms_fields
                                         (id, field, author, time)
                                        VALUES (%s, %s, %s, %s)
                                        """, (form_id, field,
                                              author, updated_on))
            else:
                updated_on = last_updated_on
                author = last_updater
            return ((form_id, realm, resource_id, subcontext, state,
                     author, updated_on),
                    (form_id, realm, resource_id, subcontext, old_state,
                     last_updater, last_updated_on))
        else:
            raise ValueError(_("Conflict"))

    def get_tracform_history(self, src):
        form_id = src if is_number(src) else self.get_tracform_meta(src)[0]
        return self.env.db_query("""
                SELECT author, time, old_state FROM forms_history
                WHERE id=%s ORDER BY time DESC
                """, (form_id,))

    def get_tracform_fields(self, src):
        form_id = src if is_number(src) else self.get_tracform_meta(src)[0]
        return self.env.db_query("""
                    SELECT field, author, time FROM forms_fields WHERE id=%s
                    """, (form_id,))

    def get_tracform_fieldinfo(self, src, field):
        """Retrieve author and time of last change per field."""
        form_id = src if is_number(src) else self.get_tracform_meta(src)[0]
        for row in self.env.db_query("""
                    SELECT author, time FROM forms_fields
                    WHERE id=%s AND field=%s
                    """, (form_id, field)):
            return row
        return None, None

    def reset_tracform(self, src, field=None, author=None, step=0):
        """Delete method for all TracForms db tables.

        Note, that we only delete recorded values and history here, while
        the form definition (being part of forms parent resource) is retained.
        Reset of single fields is not implemented, because this would require
        cumbersome and error prown history rewriting - not worth the hassle.
        """
        form_ids = []
        # identify form_id(s) to reset
        if is_number(src):
            form_ids.append(src)
        elif isinstance(src, tuple) and len(src) == 3:
            if src[-1] is None:
                # no subcontext given, reset all forms of the parent resource
                for form_id in self.get_tracform_ids(src[0], src[1]):
                    form_ids.append(form_id)
            else:
                form_ids.append(self.get_tracform_meta(src)[0])
        # restore of old values for multiple forms is not meaningful
        if step == -1 and len(form_ids) == 1:
            form_id = form_ids[0]
            now = int(time.time())
            author, updated_on, old_state =\
                self.get_tracform_history(form_id)[0] or \
                (author, now, '{}')
            if updated_on == now:
                # no history recorded, so only form values can be reset
                step = 0
            else:
                with self.env.db_transaction as db:
                    # copy last old_state to current
                    db("""
                        UPDATE forms SET author=%s, time=%s, state=%s
                        WHERE id=%s
                        """, (author, updated_on, old_state, form_id))
                    history = []
                    records = self.get_tracform_history(form_id)
                    for history_author, history_time, old_state in records:
                        history.append({'author': history_author,
                                        'time': history_time,
                                        'old_state': old_state})
                    history = parse_history(history, fieldwise=True)
                    # delete restored history entry
                    db("""
                        DELETE FROM forms_history
                        WHERE id=%s AND time=%s
                        """, (form_id, updated_on))
                    # rollback field info changes
                    for field in history.keys():
                        changes = history[field]
                        if len(changes) > 0:
                            # restore last field info, unconditional by
                            # intention i.e. to not create entries, if track_
                            # fields is False
                            db("""
                                UPDATE forms_fields
                                SET author=%s, time=%s
                                WHERE id=%s AND field=%s
                                """, (changes[0]['author'],
                                      changes[0]['time'],
                                      form_id, field))
                        else:
                            # delete current field info
                            db("""
                                DELETE FROM forms_fields
                                WHERE id=%s AND field=%s
                                """, (form_id, field))
        if step == 0:
            with self.env.db_transaction as db:
                # reset all fields and delete full history
                for form_id in form_ids:
                    db("DELETE FROM forms_history WHERE id=%s", (form_id,))
                    db("DELETE FROM forms_fields WHERE id=%s", (form_id,))
                    # don't delete basic form reference but save the reset
                    # as a form change to prevent creation of a new form_id
                    # for further retention data
                    db("""
                        UPDATE forms SET author=%s, time=%s, state=%s
                        WHERE id=%s
                        """, (author, int(time.time()), '{}', form_id))

    def search_tracforms(self, terms):
        """Backend method for TracForms ISearchSource implementation."""
        with self.env.db_query as db:
            sql, args = search_to_sql(db, ['resource_id', 'subcontext',
                                           'author', 'state',
                                           db.cast('id', 'text')], terms)
            return self.env.db_query("""
                SELECT id,realm,resource_id,subcontext,state,author,time
                FROM forms WHERE %s
                """ % sql, args)

    def get_known_users(self):
        # A reference is enough, as long as we ensure strictly read-only
        # access and short lifetime of the reference. Change later, if needed.
        # users = copy.deepcopy(self.known_users)
        users = self.known_users
        return users

    @cached
    def known_users(self):
        """Cached version of trac.env.get_known_users() for TracForms."""
        return [(username, name, email)
                for username, name, email in self.env.db_query("""
                    SELECT DISTINCT s.sid, n.value, e.value
                    FROM session AS s
                     LEFT JOIN session_attribute AS n
                          ON (n.sid=s.sid
                              AND n.authenticated=1
                              AND n.name = 'name')
                     LEFT JOIN session_attribute AS e
                          ON (e.sid=s.sid
                              AND e.authenticated=1
                              AND e.name = 'email')
                    WHERE s.authenticated=1 ORDER BY s.sid
                    """)]

    # TracForms schemas
    # Hint: See older versions of this file for the original SQL statements.
    #   Most of them have been rewritten to imrove compatibility with Trac.

    # def dbschema_2008_06_14_0000(self, cursor):
    #    """This was a simple test for the schema base class."""

    def db00(self, env, cursor):
        """Create the major tables."""
        tables = [
            Table('tracform_forms', key='id')[
                Column('tracform_id', auto_increment=True),
                Column('context'),
                Column('state'),
                Column('updater'),
                Column('updated_on', type='int')],
            Table('tracform_history')[
                Column('tracform_id', type='int'),
                Column('updater'),
                Column('updated_on', type='int'),
                Column('old_states')]
        ]
        db_connector = DatabaseManager(env).get_connector()[0]
        for table in tables:
            for stmt in db_connector.to_sql(table):
                cursor.execute(stmt)

    def db01(self, env, cursor):
        """Create indices for tracform_forms table."""
        cursor.execute("""
            CREATE INDEX tracform_forms_context
                ON tracform_forms(context)
            """)
        cursor.execute("""
            CREATE INDEX tracform_forms_updater
                ON tracform_forms(updater)
            """)
        cursor.execute("""
            CREATE INDEX tracform_forms_updated_on
                ON tracform_forms(updated_on)
            """)

    def db02(self, env, cursor):
        """This was a modify table, but instead removed the data altogether.
        """

    def db03(self, env, cursor):
        """Create indices for tracform_history table."""
        cursor.execute("""
            CREATE INDEX tracform_history_tracform_id
                ON tracform_history(tracform_id)
            """)
        # 'DESC' order removed for compatibility with PostgreSQL
        cursor.execute("""
            CREATE INDEX tracform_history_updated_on
                ON tracform_history(updated_on)
            """)
        cursor.execute("""
            CREATE INDEX tracform_history_updater
                ON tracform_history(updater)
            """)

    def db04(self, env, cursor):
        """Recreating updated_on index for tracform_forms to be descending.
        """
        # Providing compatibility for PostgreSQL this is now obsolete,
        # removing misspelled index name creation SQL statement too.

    def db10(self, env, cursor):
        """Also maintain whether history should be maintained for form."""
        cursor.execute("""
            ALTER TABLE tracform_forms
                ADD keep_history INTEGER
            """)

    def db11(self, env, cursor):
        """Make the context a unique index."""
        if env.config.get('trac', 'database').startswith('mysql'):
            cursor.execute("""
                ALTER TABLE tracform_forms DROP INDEX tracform_forms_context
                """)
        else:
            cursor.execute("""
                DROP INDEX tracform_forms_context
                """)
        cursor.execute("""
            CREATE UNIQUE INDEX tracform_forms_context
                ON tracform_forms(context)
            """)

    def db12(self, env, cursor):
        """Track who changes individual fields."""
        cursor.execute("""
            ALTER TABLE tracform_forms
                ADD track_fields INTEGER
            """)
        table = Table('tracform_fields')[
            Column('tracform_id', type='int'),
            Column('field'),
            Column('updater'),
            Column('updated_on', type='int'),
            Index(['tracform_id', 'field'], unique=True)
        ]
        db_connector = DatabaseManager(env).get_connector()[0]
        for stmt in db_connector.to_sql(table):
            cursor.execute(stmt)

    def db13(self, env, cursor):
        """Convert state serialization type to be more readable.

        Migrate to slicker named major tables and associated indexes too.
        """
        table = Table('forms', key='id')[
            Column('id', auto_increment=True),
            Column('context'),
            Column('state'),
            Column('author'),
            Column('time', type='int'),
            Column('keep_history', type='int'),
            Column('track_fields', type='int'),
            Index(['context'], unique=True),
            Index(['author']),
            Index(['time'])
        ]
        db_connector = DatabaseManager(env).get_connector()[0]
        for stmt in db_connector.to_sql(table):
            cursor.execute(stmt)

        forms_columns = ('tracform_id', 'context', 'state', 'updater',
                         'updated_on', 'keep_history', 'track_fields')
        forms_columns_new = ('id', 'context', 'state', 'author',
                             'time', 'keep_history', 'track_fields')

        sql = 'SELECT ' + ', '.join(forms_columns) + ' FROM tracform_forms'
        cursor.execute(sql)
        forms = []
        for row in cursor:
            row = dict(zip(forms_columns_new, row))
            forms.append(row)

        # convert current states serialization
        for form in forms:
            state_new = _url_to_json(form.get('state'))
            if state_new == '{}':
                form['state'] = form.get('state')
            else:
                form['state'] = state_new

        for form in forms:
            fields = form.keys()
            values = form.values()
            sql = "INSERT INTO forms (" + ", ".join(fields) + \
                  ") VALUES (" + ", ".join(
                ["%s" for I in xrange(len(fields))]) \
                  + ")"
            cursor.execute(sql, values)

        cursor.execute("""
            DROP TABLE tracform_forms
            """)
        # migrate history table
        if env.config.get('trac', 'database').startswith('postgres'):
            cursor.execute("""
                CREATE TABLE forms_history
                    AS SELECT
                         tracform_id AS id, updated_on AS time,
                         updater AS author, old_states AS old_state
                    FROM tracform_history
                """)
        else:
            cursor.execute("""
                CREATE TABLE forms_history
                    AS SELECT
                         tracform_id 'id', updated_on 'time',
                         updater 'author', old_states 'old_state'
                    FROM tracform_history
                """)

        sql = 'SELECT id,time,old_state FROM forms_history'
        cursor.execute(sql)
        history = []
        for row in cursor:
            row = dict(zip(('id', 'time', 'old_state'), row))
            history.append(row)

        # convert historic states serialization
        for row in history:
            old_state_new = _url_to_json(row.get('old_state'))
            if old_state_new == '{}':
                row['old_state'] = row.get('old_state')
            else:
                row['old_state'] = old_state_new

        for row in history:
            sql = "UPDATE forms_history SET old_state=%s " + \
                  "WHERE id=%s AND time=%s"
            cursor.execute(sql, (row['old_state'], row['id'], row['time']))

        cursor.execute("""
            CREATE INDEX forms_history_id_idx
                ON forms_history(id)
            """)
        # 'DESC' order removed for compatibility with PostgreSQL
        cursor.execute("""
            CREATE INDEX forms_history_time_idx
                ON forms_history(time)
            """)
        cursor.execute("""
            CREATE INDEX forms_history_author_idx
                ON forms_history(author)
            """)
        cursor.execute("""
            DROP TABLE tracform_history
            """)
        # migrate fields table
        if env.config.get('trac', 'database').startswith('postgres'):
            cursor.execute("""
                CREATE TABLE forms_fields
                    AS SELECT
                         tracform_id AS id, field,
                         updater AS author, updated_on AS time
                    FROM tracform_fields
                """)
        else:
            cursor.execute("""
                CREATE TABLE forms_fields
                    AS SELECT
                         tracform_id 'id', field, 
                         updater 'author', updated_on 'time'
                    FROM tracform_fields
                """)
        cursor.execute("""
            CREATE UNIQUE INDEX forms_fields_id_field_idx
                ON forms_fields(id, field)
            """)
        cursor.execute("""
            DROP TABLE tracform_fields
            """)
        # remove old TracForms version entry
        cursor.execute("""
            DELETE FROM system WHERE name='TracFormDBComponent:version';
            """)

    def db14(self, env, cursor):
        """Split context into proper Trac resource descriptors."""
        cursor.execute("""
            CREATE TABLE forms_old
                AS SELECT *
                FROM forms
            """)
        cursor.execute("""
            DROP TABLE forms
            """)
        table = Table('forms', key='id')[
            Column('id', auto_increment=True),
            Column('realm'),
            Column('resource_id'),
            Column('subcontext'),
            Column('state'),
            Column('author'),
            Column('time', type='int'),
            Column('keep_history', type='int'),
            Column('track_fields', type='int'),
            Index(['realm', 'resource_id', 'subcontext'], unique=True),
            Index(['author']),
            Index(['time'])
        ]
        db_connector = DatabaseManager(env).get_connector()[0]
        for stmt in db_connector.to_sql(table):
            cursor.execute(stmt)

        forms_columns = ('id', 'context', 'state', 'author',
                         'time', 'keep_history', 'track_fields')

        sql = 'SELECT ' + ', '.join(forms_columns) + ' FROM forms_old'
        cursor.execute(sql)
        forms = []
        for row in cursor:
            row = dict(zip(forms_columns, row))
            # extract realm, resource_id and subcontext from context
            row['realm'], row['resource_id'], row['subcontext'] = \
                _context_to_resource(self.env, row.pop('context'))
            forms.append(row)

        for form in forms:
            fields = form.keys()
            values = form.values()
            sql = "INSERT INTO forms (" + ", ".join(fields) + \
                  ") VALUES (" + ", ".join(
                ["%s" for I in xrange(len(fields))]) \
                  + ")"
            cursor.execute(sql, values)

        cursor.execute("""
            DROP TABLE forms_old
            """)


def format_author(env, req, author=None, position='macro'):
    """Return user properties.

    This is a private method optionally using CacheManager (since Trac 0.12)
    to reduce costly access to env.get_known_users() .
    """
    formdb = FormDBComponent(env)
    if formdb.show_fullname is True and position in formdb.show_fullname_pos:
        for username, name, email in formdb.get_known_users():
            if author == username and name:
                author = name
    return Chrome(env).format_author(req, author)


def _url_to_json(state_url):
    """Convert urlencoded state serial to JSON state serial."""
    state = urlparse.parse_qs(state_url)
    for name, value in state.iteritems():
        if isinstance(value, (list, tuple)):
            for item in value:
                state[name] = xml_unescape(item)
        else:
            state[name] = xml_unescape(value)
    return json.dumps(state, separators=(',', ':'))


def _context_to_resource(env, context):
    """Find parent realm and resource_id and optional TracForms subcontext.

    Some guesswork is knowingly involved here to finally overcome previous
    potentially ambiguous contexts by distinct resource parameters.
    """
    realm, resource_path = resource_from_page(env, context)
    subcontext = None
    if resource_path is not None:
        # ambiguous: ':' could be part of resource_id or subcontext or
        # the start of subcontext
        segments = re.split(':', resource_path)
        id = ''
        resource_id = None
        while len(segments) > 0:
            id += segments.pop(0)
            # guess: shortest valid resource_id is parent,
            # the rest is a TracForms subcontext
            if resource_exists(env, Resource(realm, id)):
                resource_id = id
                subcontext = ':'.join(segments)
                break
            id += ':'
        # valid resource_id in context NOT FOUND
        if resource_id is None:
            resource_id = resource_path
    else:
        # realm in context NOT FOUND
        resource_id = context
        realm = ''
    return realm, resource_id, subcontext
