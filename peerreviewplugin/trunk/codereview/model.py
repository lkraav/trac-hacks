# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#
import copy
from time import time
from trac.core import Component, implements, TracError
from trac.db import Table, Column, Index,  DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.resource import ResourceNotFound
from trac.util.text import _
from trac.util.translation import N_
from trac.util import format_date
from tracgenericclass.model import IConcreteClassProvider, AbstractVariableFieldsObject, \
    need_db_create_for_realm, create_db_for_realm, need_db_upgrade_for_realm, upgrade_db_for_realm
from tracgenericclass.util import get_timestamp_db_type
from peerReviewInit import db_name, db_name_old, db_version


__author__ = 'Cinc'


class PeerReviewModel(AbstractVariableFieldsObject):
    # Fields that have no default, and must not be modified directly by the user
    protected_fields = ('review_id', 'res_realm', 'state')

    def __init__(self, env, id_=None, res_realm=None, state='new', db=None):
        self.values = {}

        self.values['review_id'] = id_
        self.values['res_realm'] = 'peerreview'
        self.values['state'] = state
        self.values['status'] = state

        key = self.build_key_object()
        AbstractVariableFieldsObject.__init__(self, env, 'peerreview', key, db)

    def get_key_prop_names(self):
        # Set the key used as ID when getting an object from the database
        # If provided several ones they will all be used in the query:
        #     SELECT foo FROM bar WHERE key1 = .. AND key2 = .. AND ...
        return ['review_id']

    def create_instance(self, key):
        return PeerReviewModel(self.env, key, 'peerreview')

class PeerReviewerModel(AbstractVariableFieldsObject):
    # Fields that have no default, and must not be modified directly by the user
    protected_fields = ('reviewer_id', 'res_realm', 'state')

    def __init__(self, env, id=None, res_realm=None, state='new', db=None):
        self.values = {}

        self.values['reviewer_id'] = id
        self.values['res_realm'] = res_realm
        self.values['state'] = state
        self.values['status'] = state

        key = self.build_key_object()
        AbstractVariableFieldsObject.__init__(self, env, 'peerreviewer', key, db)

    def get_key_prop_names(self):
        return ['reviewer_id']

    def create_instance(self, key):
        return PeerReviewModel(self.env, 'id', 'peerreviewer')

class PeerReviewModelProvider(Component):
    """
    This class provides the data model for the generic workflow plugin.

    The actual data model on the db is created starting from the
    SCHEMA declaration below.
    For each table, we specify whether to create also a '_custom' and
    a '_change' table.

    This class also provides the specification of the available fields
    for each class, being them standard fields and the custom fields
    specified in the trac.ini file.
    The custom field specification follows the same syntax as for
    Tickets.
    Currently, only 'text' type of custom fields are supported.
    """

    implements(IConcreteClassProvider, IEnvironmentSetupParticipant)

    current_db_version = 0

    SCHEMA = {
                'peerreview':
                    {'table':
                        Table('peerreview', key = ('review_id'))[
                              Column('review_id', auto_increment=True, type='int'),
                              Column('owner'),
                              Column('status'),
                              Column('created', type='int'),
                              Column('name'),
                              Column('notes'),
                              Column('parent_id', type='int'),
                              Column('project'),
                              Column('keywords')],
                     'has_custom': True,
                     'has_change': True,
                     'version': 3},
                'peerreviewfile':
                    {'table':
                        Table('peerreviewfile', key='file_id')[
                              Column('file_id', auto_increment=True, type='int'),
                              Column('review_id', type='int'),
                              Column('path'),
                              Column('line_start', type='int'),
                              Column('line_end', type='int'),
                              Column('repo'),
                              Column('revision'),
                              Column('changerevision'),
                              Column('hash'),
                              Column('status')],
                     'has_custom': True,
                     'has_change': True,
                     'version': 3},
                'peerreviewcomment':
                    {'table':
                        Table('peerreviewcomment', key='comment_id')[
                              Column('comment_id', auto_increment=True, type='int'),
                              Column('file_id', type='int'),
                              Column('parent_id', type='int'),
                              Column('line_num', type='int'),
                              Column('author'),
                              Column('comment'),
                              Column('attachment_path'),
                              Column('created', type='int'),
                              Column('refs'),
                              Column('type'),
                              Column('status')],
                     'has_custom': True,
                     'has_change': True,
                     'version': 3},
                'peerreviewer':
                    {'table':
                        Table('peerreviewer', key=('reviewer_id', 'reviewer'))[
                              Column('reviewer_id', auto_increment=True, type='int'),
                              Column('review_id', type='int'),
                              Column('reviewer'),
                              Column('status'),
                              Column('vote', type='int')],
                     'has_custom': True,
                     'has_change': True,
                     'version': 3},
            }

    FIELDS = {
                'peerreview': [
                    {'name': 'review_id', 'type': 'int', 'label': N_('Review ID')},
                    {'name': 'owner', 'type': 'text', 'label': N_('Review owner')},
                    {'name': 'status', 'type': 'text', 'label': N_('Review status')},
                    {'name': 'created', 'type': 'int', 'label': N_('Review creation date')},
                    {'name': 'name', 'type': 'text', 'label': N_('Review name')},
                    {'name': 'notes', 'type': 'text', 'label': N_('Review notes')},
                    {'name': 'parent_id', 'type': 'int', 'label': N_('Review parent. 0 if not a followup review')},
                    {'name': 'project', 'type': 'text', 'label': N_('Project')},
                    {'name': 'keywords', 'type': 'text', 'label': N_('Review keywords')}
                ],
                'peerreviewfile': [
                    {'name': 'file_id', 'type': 'int', 'label': N_('File ID')},
                    {'name': 'review_id', 'type': 'int', 'label': N_('Review ID')},
                    {'name': 'path', 'type': 'text', 'label': N_('File path')},
                    {'name': 'line_start', 'type': 'int', 'label': N_('First line to review')},
                    {'name': 'line_end', 'type': 'int', 'label': N_('Last line to review')},
                    {'name': 'repo', 'type': 'text', 'label': N_('Repository')},
                    {'name': 'revision', 'type': 'text', 'label': N_('Revision')},
                    {'name': 'changerevision', 'type': 'text', 'label': N_('Revision of last change')},
                    {'name': 'hash', 'type': 'text', 'label': N_('Hash of file content')},
                    {'name': 'status', 'type': 'text', 'label': N_('File status')}
                ],
                'peerreviewcomment': [
                    {'name': 'comment_id', 'type': 'int', 'label': N_('Comment ID')},
                    {'name': 'file_id', 'type': 'int', 'label': N_('File ID')},
                    {'name': 'parent_id', 'type': 'int', 'label': N_('Parent comment')},
                    {'name': 'line_num', 'type': 'int', 'label': N_('Line')},
                    {'name': 'author', 'type': 'text', 'label': N_('Author')},
                    {'name': 'comment', 'type': 'text', 'label': N_('Comment')},
                    {'name': 'attachment_path', 'type': 'text', 'label': N_('Attachment')},
                    {'name': 'created', 'type': 'int', 'label': N_('Comment creation date')},
                    {'name': 'status', 'type': 'text', 'label': N_('Comment status')}
                ],
                'peerreviewer': [
                    {'name': 'reviewer_id', 'type': 'int', 'label': N_('ID')},
                    {'name': 'review_id', 'type': 'int', 'label': N_('Review ID')},
                    {'name': 'reviewer', 'type': 'text', 'label': N_('Reviewer')},
                    {'name': 'status', 'type': 'text', 'label': N_('Review status')},
                    {'name': 'vote', 'type': 'int', 'label': N_('Vote')},
                ]
            }

    METADATA = {
                'peerreview': {
                        'label': "Review",
                        'searchable': True,
                        'has_custom': True,
                        'has_change': True
                    },
                'peerreviewfile': {
                        'label': "ReviewFile",
                        'searchable': False,
                        'has_custom': True,
                        'has_change': True
                    },
                'peerreviewcomment': {
                    'label': "ReviewComment",
                    'searchable': True,
                    'has_custom': True,
                    'has_change': True
                },
                'peerreviewer': {
                    'label': "Reviewer",
                    'searchable': False,
                    'has_custom': True,
                    'has_change': True
                },
    }


    # IConcreteClassProvider methods
    def get_realms(self):
            yield 'peerreview'
            yield 'peerreviewer'

    def get_data_models(self):
        return self.SCHEMA

    def get_fields(self):
        return self.FIELDS

    def get_metadata(self):
        return self.METADATA

    def create_instance(self, realm, key=None):
        obj = None

        if realm == 'peerreview':
            if key is not None:
                obj = PeerReviewModel(self.env, key, realm)
            else:
                obj = PeerReviewModel(self.env)
        elif realm == 'peerreviewer':
            if key is not None:
                obj = PeerReviewerModel(self.env, key, realm)
            else:
                obj = PeerReviewerModel(self.env)
        return obj

    def check_permission(self, req, realm, key_str=None, operation='set', name=None, value=None):
        pass

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.current_db_version = 0
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        self.current_db_version = self._get_version(db.cursor())

        if self.current_db_version < db_version:
            self.log.info("PeerReview plugin database schema version is %d, should be %d",
                          self.current_db_version, db_version)
            return True
        #if self.current_db_version > db_version:
        #    raise TracError(_("Database newer than PeerReview plugin version"))

        for realm in self.SCHEMA:
            realm_metadata = self.SCHEMA[realm]
            if need_db_create_for_realm(self.env, realm, realm_metadata, db) or \
                need_db_upgrade_for_realm(self.env, realm, realm_metadata, db):
                return True

        return False

    def upgrade_environment(self, db=None):
        # Create or update db

        @self.env.with_transaction(db)
        def do_upgrade(db):
            cursor = db.cursor()
            for i in range(self.current_db_version + 1, db_version + 1):
                name = 'db%i' % i
                print "PeerReview: running upgrade ", name
                try:
                    upgrades = __import__('upgrades', globals(), locals(), [name])
                    script = getattr(upgrades, name)
                except AttributeError:
                    raise TracError(_("No PeerReview upgrade module %(num)i "
                                      "(%(version)s.py)", num=i, version=name))
                script.do_upgrade(self.env, i, cursor)

                self._set_version(cursor, i)
                db.commit()


        # At this point at least all legacy tables are installed with db version 2.
        # Make sure we have a db version set for tables other than 'peerreview'
        @self.env.with_transaction(db)
        def add_tables(db):
            db_names = [u'peerreviewfile_version', u'peerreviewcomment_version',
                        u'peerreviewer_version']
            cursor = db.cursor()
            for name in db_names:
                print "checking ", name
                cursor.execute("SELECT name FROM system")
                if name not in [row[0] for row in cursor]:
                    cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",
                                  (name, db_version))

        # Add change and custom tables
        @self.env.with_transaction(db)
        def do_change_custom(db):
            if self.current_db_version == 2:
                for realm in self.SCHEMA:
                    realm_metadata = self.SCHEMA[realm]

                    self._create_custom_change_db_for_realm(realm, realm_metadata, db)

        @self.env.with_transaction(db)
        def do_upgrade_environment(db):
            for realm in self.SCHEMA:
                realm_metadata = self.SCHEMA[realm]

                if need_db_create_for_realm(self.env, realm, realm_metadata, db):
                    create_db_for_realm(self.env, realm, realm_metadata, db)

                elif need_db_upgrade_for_realm(self.env, realm, realm_metadata, db):
                    upgrade_db_for_realm(self.env, 'codereview.upgrades', realm, realm_metadata, db)

    def _create_custom_change_db_for_realm(self, realm, realm_schema, db=None):

        """
        Call this method from inside your Component IEnvironmentSetupParticipant's
        upgrade_environment() function to create the database tables corresponding to
        your Component's generic classes.

        :param realm_schema: The db schema definition, as returned by
                       the get_data_models() function in the IConcreteClassProvider
                       interface.
        """

        env = self.env
        @env.with_transaction(db)
        def do_create_db_for_realm(db):
            cursor = db.cursor()

            db_backend, _ = DatabaseManager(env).get_connector()

            env.log.info("Creating DB for class '%s'.", realm)

            # Create the required tables
            table_metadata = realm_schema['table']
            version = realm_schema['version']
            tablename = table_metadata.name

            key_names = [k for k in table_metadata.key]

            # Create custom fields table if required
            if realm_schema['has_custom']:
                cols = []
                for k in key_names:
                    # Determine type of column k
                    type = 'text'
                    for c in table_metadata.columns:
                        if c.name == k:
                            type = c.type

                    cols.append(Column(k, type=type))

                cols.append(Column('name'))
                cols.append(Column('value'))

                custom_key = copy.deepcopy(key_names)
                custom_key.append('name')

                table_custom = Table(tablename+'_custom', key = custom_key)[cols]
                env.log.info("Creating custom properties table %s...", table_custom.name)
                for stmt in db_backend.to_sql(table_custom):
                    env.log.debug(stmt)
                    cursor.execute(stmt)

            # Create change history table if required
            if realm_schema['has_change']:
                cols = []
                for k in key_names:
                    # Determine type of column k
                    type = 'text'
                    for c in table_metadata.columns:
                        if c.name == k:
                            type = c.type

                    cols.append(Column(k, type=type))

                cols.append(Column('time', type=get_timestamp_db_type()))
                cols.append(Column('author'))
                cols.append(Column('field'))
                cols.append(Column('oldvalue'))
                cols.append(Column('newvalue'))
                cols.append(Index(key_names))

                change_key = copy.deepcopy(key_names)
                change_key.append('time')
                change_key.append('field')

                table_change = Table(tablename+'_change', key = change_key)[cols]
                env.log.info("Creating change history table %s...", table_change.name)
                for stmt in db_backend.to_sql(table_change):
                    env.log.debug(stmt)
                    cursor.execute(stmt)



    def _get_version(self, cursor):
        cursor.execute("SELECT value FROM system WHERE name = %s", (db_name_old,))
        value = cursor.fetchone()
        val = int(value[0]) if value else 0
        if not val:
            # Database version > 1 or no datavase yet
            cursor.execute("SELECT value FROM system WHERE name = %s", (db_name,))
            value = cursor.fetchone()
            val = int(value[0]) if value else 0
        return val

    def _set_version(self, cursor, cur_ver):
        db_names = [u'peerreview_version', u'peerreviewfile_version', u'peerreviewcomment_version']
        if not self.current_db_version:
            for name in db_names:
                cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",
                               (name, cur_ver))
        else:
            for name in db_names:
                cursor.execute("UPDATE system SET value = %s WHERE name = %s",
                               (db_version, name))
                if cursor.rowcount == 0:
                    cursor.execute("INSERT INTO system (name,value) VALUES (%s,%s)",
                                   (name, db_version))
        self.current_db_version = cur_ver


def get_threshold(env):
    return env.config.getint('peer-review', 'vote_threshold', 100)

def set_threshold(env, val):
    env.config.set('peer-review', 'vote_threshold', val)
    env.config.save()


def get_users(env):
    db = env.get_read_db()
    cursor = db.cursor()
    cursor.execute("""SELECT DISTINCT p1.username FROM permission AS p1
                      LEFT JOIN permission AS p2 ON p1.action = p2.username
                      WHERE p2.action = 'CODE_REVIEW_DEV'
                      OR p1.action = 'CODE_REVIEW_DEV'
                      OR p1.action = 'TRAC_ADMIN'
                      """)
    users = []
    for row in cursor:
        users.append(row[0])
    if users:
        # Filter groups from the results. We should probably do this using the group provider component
        cursor.execute("""Select DISTINCT p3.action FROM permission AS p3
                          JOIN permission p4 ON p3.action = p4.username""")
        groups = []
        for row in cursor:
            groups.append(row[0])
        groups.append('authenticated')
        users = list(set(users)-set(groups))
    return sorted(users)


class Vote(object):

    def __init__(self, env, review_id):
        if not review_id:
            raise ValueError("No review id given during creation of Vote object.")
        self._votes = {'yes': 0, 'no': 0, 'pending': 0}
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT vote FROM peerreviewer WHERE review_id = %s", (review_id,))
        for row in cursor:
            if row[0] == -1:
                self._votes['pending'] += 1
            elif row[0] == 1:
                self._votes['yes'] += 1
            elif row[0] == 0:
                self._votes['no'] += 1

    @property
    def yes(self):
        return self._votes['yes']

    @property
    def no(self):
        return self._votes['no']

    @property
    def pending(self):
        return self._votes['pending']

    @property
    def votes(self):
        return self._votes


class Reviewer(object):
    """Model for a reviewer working on a code review."""
    def __init__(self, env, review_id=None, name=None):
        self.env = env

        if name and review_id:
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT reviewer_id, review_id, reviewer, status, vote FROM peerreviewer WHERE reviewer=%s
                AND review_id=%s
                """, (name, review_id))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_("Reviewer '%(name)s' does not exist for review '#%(review)s'.",
                                         name=name, review=review_id), _('Peer Review Error'))
            self._init_from_row(row)
        else:
            self._init_from_row((None,)*5)

    def _init_from_row(self, row):
        id_, rev_id, reviewer, status, vote = row
        self.id = id_
        self.review_id = rev_id
        self.reviewer = reviewer
        self.status = status
        self.vote = vote

    def insert(self):
        if not self.review_id:
            raise ValueError("No review id given during creation of Reviewer entry.")
        @self.env.with_transaction()
        def do_insert(db):
            cursor = db.cursor()
            self.env.log.debug("Creating new reviewer entry for '%s'" % self.review_id)
            cursor.execute("""INSERT INTO peerreviewer (review_id, reviewer, status, vote)
                              VALUES (%s, %s, %s, %s)
                           """, (self.review_id, self.reviewer, self.status, self.vote))

    def update(self):
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            self.env.log.debug("Updating reviewer %s for review '%s'" % (self.reviewer, self.review_id))
            cursor.execute("""UPDATE peerreviewer
                        SET review_id=%s, reviewer=%s, status=%s, vote=%s
                        WHERE reviewer=%s AND review_id=%s
                        """, (self.review_id, self.reviewer, self.status, self.vote, self.reviewer, self.review_id))

    def delete(self):
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            cursor.execute("""DELETE FROM peerreviewer
                        WHERE review_id=%s AND reviewer=%s
                        """, (self.review_id, self.reviewer))

    @classmethod
    def select_by_review_id(cls, env, review_id, rev_name=None):
        db = env.get_read_db()
        cursor = db.cursor()
        if rev_name:
            sql = "SELECT reviewer_id, review_id, reviewer, status, vote FROM peerreviewer WHERE review_id = %s " \
                  "AND reviewer = %s"
            data = (review_id, rev_name)
            cursor.execute(sql, data)
            row = cursor.fetchone()
            if row:
                reviewer = cls(env)
                reviewer._init_from_row(row)
            else:
                reviewer = None
            return reviewer
        else:
            sql = "SELECT reviewer_id, review_id, reviewer, status, vote FROM peerreviewer WHERE review_id = %s"
            data = (review_id,)
        cursor.execute(sql, data)
        reviewers = []
        for row in cursor:
            reviewer = cls(env)
            reviewer._init_from_row(row)
            reviewers.append(reviewer)
        return reviewers


class Review(object):
    def __init__(self, env, review_id=None):
        self.env = env

        if review_id:
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT review_id, owner, status, created, name, notes, parent_id FROM peerreview WHERE review_id=%s
                """, (review_id,))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_('Review %(name)s does not exist.',
                                         name=review_id), _('Peer Review Error'))
            self._init_from_row(row)
        else:
            self._init_from_row((None,)*7)
            self.raw_date = int(time())
            self.parent_id = 0

    def _init_from_row(self, row):
        rev_id, author, status, creation_date, name, notes, parent_id = row
        self.name = self._old_name = name
        self.review_id = rev_id
        self.author = author
        self.status = status
        self.raw_date = creation_date
        self.creation_date = format_date(creation_date)
        self.notes = notes or ''
        self.parent_id = parent_id or 0

    exists = property(lambda self: self._old_name is not None)

    def insert(self):
        if not self.raw_date:
            self.raw_date = int(time())
        @self.env.with_transaction()
        def do_insert(db):
            cursor = db.cursor()
            self.env.log.debug("Creating new review '%s'" % self.review_id)
            cursor.execute("""INSERT INTO peerreview (owner, status, created, name, notes, parent_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """, (self.author, self.status, self.raw_date, self.name, self.notes, self.parent_id))
            self.review_id = db.get_last_id(cursor, 'peerreview', 'review_id')

    def update(self):
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            self.env.log.debug("Updating review '%s'" % self.review_id)
            cursor.execute("""UPDATE peerreview
                            SET owner=%s, status=%s, created=%s, name=%s, notes=%s, parent_id=%s
                            WHERE review_id=%s
                            """, (self.author, self.status, self.raw_date, self.name, self.notes, self.parent_id,
                                  self.review_id))

    @classmethod
    def select(cls, env):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT review_id, owner, status, created, name, notes, parent_id FROM peerreview "
                       "ORDER BY created")
        reviews = []
        for row in cursor:
            review = cls(env)
            review._init_from_row(row)
            reviews.append(review)
        return reviews

    @classmethod
    def select_by_reviewer(cls, env, reviewer):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT cr.review_id, cr.owner, cr.status, cr.created, cr.name, cr.notes, cr.parent_id  FROM "
                       "peerreview AS cr JOIN peerreviewer AS r ON cr.review_id = r.review_id "
                       "WHERE r.reviewer=%s"
                       "ORDER BY cr.created", (reviewer,))
        reviews = []
        for row in cursor:
            review = cls(env)
            review._init_from_row(row)
            reviews.append(review)
        return reviews


class ReviewFile(object):
    def __init__(self, env, file_id=None):
        self.env = env

        if file_id:
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT file_id, review_id, path, line_start, line_end, revision FROM peerreviewfile WHERE file_id=%s
                """, (file_id,))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_('File %(name)s does not exist.',
                                         name=file_id), _('Peer Review Error'))
            self._init_from_row(row)
        else:
            self._init_from_row((None,)*6)

    def _init_from_row(self, row):
        file_id, rev_id, fpath, start, end, ver = row
        self.file_id = file_id
        self.review_id = rev_id
        self.path = fpath
        self.start = start
        self.end = end
        self.version = ver

    def insert(self):
        @self.env.with_transaction()
        def do_insert(db):
            cursor = db.cursor()
            self.env.log.debug("Creating new file for review '%s'" % self.review_id)
            cursor.execute("""INSERT INTO peerreviewfile (review_id, path, line_start,
                            line_end, revision)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (self.review_id, self.path, self.start, self.end, self.version))

    def delete(self):
        @self.env.with_transaction()
        def do_delete(db):
            cursor = db.cursor()
            self.env.log.debug("Deleting file '%s' for review '%s'" % (self.file_id, self.review_id))
            cursor.execute("""DELETE FROM peerreviewfile  WHERE file_id=%s""",
                           (self.file_id,))

    @classmethod
    def select_by_review(cls, env, review_id):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT f.file_id, f.review_id, f.path, f.line_start, f.line_end, f.revision FROM "
                       "peerreviewfile AS f WHERE f.review_id=%s"
                       "ORDER BY f.path", (review_id,))
        files = []
        for row in cursor:
            rev_file = cls(env)
            rev_file._init_from_row(row)
            files.append(rev_file)
        return files


class Comment(object):

    def __init__(self, env, file_id=None):
        self.env = env
        self._init_from_row((None,)*8)

    def _init_from_row(self, row):
        comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created = row
        self.comment_id = comment_id
        self.file_id = file_id
        self.parent_id = parent_id
        self.line_num = line_num
        self.author = author
        self.comment = comment
        self.attachment_path = attachment_path
        self.created = created

    def insert(self):
        @self.env.with_transaction()
        def do_insert(db):
            created = self.created
            if not created:
                created = int(time())
            cursor = db.cursor()
            self.env.log.debug("Creating new comment for file '%s'" % self.file_id)
            cursor.execute("""INSERT INTO peerreviewcomment (file_id, parent_id, line_num,
                            author, comment, attachment_path, created)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (self.file_id, self.parent_id, self.line_num, self.author, self.comment,
                                  self.attachment_path, created))

    @classmethod
    def select_by_file_id(cls, env, file_id):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created FROM "
                       "peerreviewcomment WHERE file_id=%s ORDER BY line_num", (file_id,))
        comments = []
        for row in cursor:
            c = cls(env)
            c._init_from_row(row)
            comments.append(c)
        return comments