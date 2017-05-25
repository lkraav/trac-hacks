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
from collections import defaultdict
from datetime import datetime
from time import time
from trac.core import Component, implements, TracError
from trac.db import Table, Column, Index,  DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.resource import ResourceNotFound
from trac.util.datefmt import to_utimestamp, utc
from trac.util.translation import N_, _
from trac.util import format_date
from tracgenericclass.model import IConcreteClassProvider, AbstractVariableFieldsObject, \
    need_db_create_for_realm, create_db_for_realm, need_db_upgrade_for_realm, upgrade_db_for_realm
from tracgenericclass.util import get_timestamp_db_type

__author__ = 'Cinc'

db_name_old = 'codereview_version'  # for database version 1
db_name = 'peerreview_version'
db_version = 2  # Don't change this one!

datetime_now = datetime.now

class PeerReviewModel(AbstractVariableFieldsObject):
    # Fields that have no default, and must not be modified directly by the user
    protected_fields = ('review_id', 'res_realm', 'state')

    def __init__(self, env, id_=None, res_realm=None, state='new', db=None):
        self.values = {}
        self.env = env

        self.values['review_id'] = id_
        self.values['res_realm'] = 'peerreview'
        # Set defaults
        self.values['state'] = state
        self.values['status'] = state
        self.values['created'] = to_utimestamp(datetime_now(utc))
        self.values['parent_id'] = 0

        key = self.build_key_object()
        AbstractVariableFieldsObject.__init__(self, env, 'peerreview', key, db)

    def get_key_prop_names(self):
        # Set the key used as ID when getting an object from the database
        # If provided several ones they will all be used in the query:
        #     SELECT foo FROM bar WHERE key1 = .. AND key2 = .. AND ...
        return ['review_id']

    def clear_props(self):
        for key in self.values:
            if key not in ['review_id', 'res_realm']:
                self.values[key] = None

    def create_instance(self, key):
        return PeerReviewModel(self.env, key['review_id'], 'peerreview')

    def change_status(self, new_status, author=None):
        """Called from the change object listener to change state of review and connencted files."""
        self['status'] = new_status
        self.save_changes(author=author)

        # Change the status of files attached to this review

        r_tmpl = ReviewFileModel(self.env)
        r_tmpl.clear_props()
        r_tmpl['review_id'] = self['review_id']
        all_files = r_tmpl.list_matching_objects()  # This is a generator
        # We only mark files for terminal states
        finish_states = self.env.config.getlist("peerreview", "terminal_review_states")
        if new_status in finish_states:
            status = new_status
            self.env.log.debug("ReviewModel: changing status of attached files for review '#%s'to '%s'" %
                               (self['review_id'], new_status))
        else:
            status = 'new'
            self.env.log.debug("ReviewModel: changing status of attached files for review '#%s'to '%s'" %
                               (self['review_id'], status))
        for f in all_files:
            f['status'] = status
            f.save_changes(author, "Status of review '#%s' changed." % self['review_id'])

    @classmethod
    def reviews_by_period(cls, env, start_timestamp, end_timestamp):
        """Used for getting timeline reviews."""

        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT review_id FROM peerreview WHERE created >= %s AND created <= %s ORDER BY created",
                       (start_timestamp, end_timestamp))
        reviews = []
        for row in cursor:
            review = cls(env, row[0])
            reviews.append(review)
        return reviews


class PeerReviewerModel(AbstractVariableFieldsObject):
    # Fields that have no default, and must not be modified directly by the user
    protected_fields = ('reviewer_id', 'res_realm', 'state')

    def __init__(self, env, id_=None, res_realm=None, state='new', db=None):
        self.values = {}

        self.values['reviewer_id'] = id_
        self.values['res_realm'] = res_realm
        self.values['state'] = state
        self.values['status'] = state

        key = self.build_key_object()
        AbstractVariableFieldsObject.__init__(self, env, 'peerreviewer', key, db)

    def get_key_prop_names(self):
        return ['reviewer_id']

    def clear_props(self):
        for key in self.values:
            if key not in ['reviewer_id', 'res_realm']:
                self.values[key] = None

    def create_instance(self, key):
        return PeerReviewerModel(self.env, key['reviewer_id'], 'peerreviewer')

    @classmethod
    def select_by_review_id(cls, env, review_id):
        rm = PeerReviewerModel(env)
        rm.clear_props()
        rm['review_id'] = review_id
        return rm.list_matching_objects()


class ReviewFileModel(AbstractVariableFieldsObject):
    # Fields that have no default, and must not be modified directly by the user
    protected_fields = ('file_id', 'res_realm', 'state')

    def __init__(self, env, id_=None, res_realm=None, state='new', db=None):
        self.values = {}

        if type(id_) is int:
            id_ = str(id_)
        self.values['file_id'] = id_
        self.values['res_realm'] = res_realm
        self.values['state'] = state
        self.values['status'] = state

        key = self.build_key_object()
        AbstractVariableFieldsObject.__init__(self, env, 'peerreviewfile', key, db)

    def clear_props(self):
        for key in self.values:
            if key not in ['file_id', 'res_realm']:
                self.values[key] = None

    def get_key_prop_names(self):
        return ['file_id']

    def create_instance(self, key):
        return ReviewFileModel(self.env, key['file_id'], 'peerreviewfile')

    @classmethod
    def file_dict_by_review(cls, env, include_closed=False):
        """Return a dict with review_id as key and a file list as value.

        :param include_closed: if True return closed files too.
        """

        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT file_id, review_id FROM peerreviewfile ORDER BY review_id")
        files_dict = defaultdict(list)
        for row in cursor:
            file_ = cls(env, row[0])
            files_dict[row[1]].append(file_)
        return files_dict

    @classmethod
    def delete_files_by_project_name(cls, env, proj_name):
        """Delete all file information belonging to project proj_name.

        @param env: Trac environment object
        @param proj_name: name of project. USed to filter by 'project' column
        @return: None
        """
        @env.with_transaction()
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute("DELETE FROM peerreviewfile WHERE project=%s", (proj_name,))

    @classmethod
    def select_by_review(cls, env, review_id):
        """Returns a generator."""
        rf = ReviewFileModel(env)
        rf.clear_props()
        rf['review_id'] = review_id
        return rf.list_matching_objects()


class ReviewDataModel(AbstractVariableFieldsObject):
    """Data model holding whatever you want to create relations for."""
    # Fields that have no default, and must not be modified directly by the user
    protected_fields = ('data_id', 'res_realm', 'state')

    def __init__(self, env, id_=None, res_realm=None, state='new', db=None):
        self.values = {}

        self.values['data_id'] = id_
        self.values['res_realm'] = res_realm
        self.values['state'] = state

        key = self.build_key_object()
        AbstractVariableFieldsObject.__init__(self, env, 'peerreviewdata', key, db)

    def get_key_prop_names(self):
        return ['data_id']

    def clear_props(self):
        for key in self.values:
            if key not in ['data_id', 'res_realm']:
                self.values[key] = None

    def create_instance(self, key):
        return ReviewDataModel(self.env, key['data_id'], 'peerreviewdata')

    @classmethod
    def comments_for_file_and_owner(cls, env, file_id, owner):
        """Return a list of data."""

        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT comment_id, type, data FROM peerreviewdata "
                       "WHERE file_id = %s AND owner = %s",
                       (file_id, owner))
        return cursor.fetchall()

    @classmethod
    def comments_for_owner(cls, env, owner):
        """Return a list of comment data for owner.
        """
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT comment_id, review_id, type, data FROM peerreviewdata "
                       "WHERE owner = %s", (owner,))
        return cursor.fetchall()

    @classmethod
    def all_file_project_data(cls, env):
        """Return a dict with project name as key and a dict with project information as value."""

        sql = """SELECT n.data AS name , r.type, r.data FROM peerreviewdata AS n
                 JOIN peerreviewdata AS r ON r.data_key = n.data
                 WHERE n.type = 'fileproject'"""
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute(sql)
        files_dict = defaultdict(dict)
        for row in cursor:
            files_dict[row[0]][row[1]] = row[2]
        return files_dict


class ReviewCommentModel(AbstractVariableFieldsObject):
    """Data model holding whatever you want to create relations for."""
    # Fields that have no default, and must not be modified directly by the user
    protected_fields = ('comment_id', 'res_realm', 'state')

    def __init__(self, env, id_=None, res_realm=None, state='new', db=None):
        self.values = {}

        self.values['comment_id'] = id_
        self.values['res_realm'] = res_realm
        self.values['state'] = state
        self.values['created'] = to_utimestamp(datetime_now(utc))

        key = self.build_key_object()
        AbstractVariableFieldsObject.__init__(self, env, 'peerreviewcomment', key, db)

    def get_key_prop_names(self):
        return ['comment_id']

    def clear_props(self):
        for key in self.values:
            if key not in ['comment_id', 'res_realm']:
                self.values[key] = None

    def create_instance(self, key):
        return ReviewCommentModel(self.env, key['comment_id'], 'peerreviewcomment')

    @classmethod
    def comments_by_file_id(cls, env):
        """Return a dict with file_id as key and a comment id list as value."""

        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT comment_id, file_id FROM peerreviewcomment")
        the_dict = defaultdict(list)
        for row in cursor:
            the_dict[row[1]].append(row[0])
        return the_dict


class PeerReviewModelProvider(Component):
    """This class provides the data model for the generic workflow plugin.

    [[BR]]
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
                        Table('peerreview', key=('review_id'))[
                              Column('review_id', auto_increment=True, type='int'),
                              Column('owner'),
                              Column('status'),
                              Column('created', type='int'),
                              Column('closed', type='int'),
                              Column('name'),
                              Column('notes'),
                              Column('parent_id', type='int'),
                              Column('project'),
                              Column('keywords'),
                              Index(['owner']),
                              Index(['status'])],
                     'has_custom': True,
                     'has_change': True,
                     'version': 6},
                'peerreviewfile':
                    {'table':
                        Table('peerreviewfile', key=('file_id'))[
                              Column('file_id', auto_increment=True, type='int'),
                              Column('review_id', type='int'),
                              Column('path'),
                              Column('line_start', type='int'),
                              Column('line_end', type='int'),
                              Column('repo'),
                              Column('revision'),
                              Column('changerevision'),
                              Column('hash'),
                              Column('status'),
                              Column('project'),
                              Index(['hash']),
                              Index(['review_id']),
                              Index(['status']),
                              Index(['project'])
                        ],
                     'has_custom': True,
                     'has_change': True,
                     'version': 5},
                'peerreviewcomment':
                    {'table':
                        Table('peerreviewcomment', key=('comment_id'))[
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
                              Column('status'),
                              Index(['file_id']),
                              Index(['author'])
                        ],
                     'has_custom': True,
                     'has_change': True,
                     'version': 6},
                'peerreviewer':
                    {'table':
                        Table('peerreviewer', key=('reviewer_id'))[
                              Column('reviewer_id', auto_increment=True, type='int'),
                              Column('review_id', type='int'),
                              Column('reviewer'),
                              Column('status'),
                              Column('vote', type='int'),
                              Index(['reviewer']),
                              Index(['review_id'])
                        ],
                     'has_custom': True,
                     'has_change': True,
                     'version': 5},
                'peerreviewdata':
                    {'table':
                         Table('peerreviewdata', key=('data_id'))[
                             Column('data_id', type='int'),
                             Column('review_id', type='int'),
                             Column('comment_id', type='int'),
                             Column('file_id', type='int'),
                             Column('reviewer_id', type='int'),
                             Column('type'),
                             Column('data'),
                             Column('owner'),
                             Column('data_key'),
                             Index(['review_id']),
                             Index(['comment_id']),
                             Index(['file_id'])
                         ],
                     'has_custom': False,
                     'has_change': False,
                     'version': 3},
                    }

    FIELDS = {
                'peerreview': [
                    {'name': 'review_id', 'type': 'int', 'label': N_('Review ID')},
                    {'name': 'owner', 'type': 'text', 'label': N_('Review owner')},
                    {'name': 'status', 'type': 'text', 'label': N_('Review status')},
                    {'name': 'created', 'type': 'int', 'label': N_('Review creation date')},
                    {'name': 'closed', 'type': 'int', 'label': N_('Review closing date')},
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
                    {'name': 'status', 'type': 'text', 'label': N_('File status')},
                    {'name': 'project', 'type': 'text', 'label': N_('Project')},
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
                ],
                'peerreviewdata': [
                    {'name': 'data_id', 'type': 'int', 'label': N_('ID')},
                    {'name': 'review_id', 'type': 'int', 'label': N_('Review ID')},
                    {'name': 'comment_id', 'type': 'int', 'label': N_('Comment ID')},
                    {'name': 'file_id', 'type': 'int', 'label': N_('File ID')},
                    {'name': 'reviewer_id', 'type': 'int', 'label': N_('Reviewer ID')},
                    {'name': 'type', 'type': 'text', 'label': N_('Type')},
                    {'name': 'data', 'type': 'text', 'label': N_('Data')},
                    {'name': 'owner', 'type': 'text', 'label': N_('Owner')},
                    {'name': 'data_key', 'type': 'text', 'label': N_('Key for data')},
                ],
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
                'peerreviewdata': {
                    'label': "Data",
                    'searchable': True,
                    'has_custom': False,
                    'has_change': False
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

        if not db:
            db = self.env.get_read_db()
        self.current_db_version = self._get_version(db.cursor())

        if self.current_db_version < db_version:
            self.log.info("PeerReview plugin database schema version is %d, should be %d",
                          self.current_db_version, db_version)
            return True

        for realm in self.SCHEMA:
            realm_metadata = self.SCHEMA[realm]
            if need_db_create_for_realm(self.env, realm, realm_metadata, db) or \
                need_db_upgrade_for_realm(self.env, realm, realm_metadata, db):
                return True

        return False

    def upgrade_environment(self, db=None):
        # Create or update db. We are going step by step through all database versions.

        if self.current_db_version != 0 and self.current_db_version < 6:
            raise TracError("Upgrade for database version %s not supported. Raise a ticket for "
                            "PeerReviewPlugin for a fix."
                            % self.current_db_version)

        self.upgrade_tracgeneric()

    def upgrade_tracgeneric(self):
        """Upgrade for versions > 2 using the TracGenericClass mechanism."""
        @self.env.with_transaction()
        def do_upgrade_environment(db):
            for realm in self.SCHEMA:
                realm_metadata = self.SCHEMA[realm]

                if need_db_create_for_realm(self.env, realm, realm_metadata, db):
                    create_db_for_realm(self.env, realm, realm_metadata, db)
                    self.add_workflows()

                elif need_db_upgrade_for_realm(self.env, realm, realm_metadata, db):
                    upgrade_db_for_realm(self.env, 'codereview.upgrades', realm, realm_metadata, db)

    def add_workflows(self):

        env = self.env
        # Add default workflow for peerreview

        wf_data = [['approve', 'reviewed -> approved'],
                   ['approve.name', 'Approve the review'],
                   ['close', 'new, reviewed, in-review -> closed'],
                   ['close.name', 'Close review'],
                   ['disapprove', 'reviewed -> disapproved'],
                   ['disapprove.name', 'Deny this review'],
                   ['reopen', 'closed, reviewed, approved, disapproved -> new'],
                   ['reopen.permissions', 'CODE_REVIEW_MGR'],
                   ['review-done', 'in-review -> reviewed'],
                   ['review-done.name', 'Mark as reviewed'],
                   ['reviewing', 'new -> in-review'],
                   ['reviewing.default', '5'],
                   ['reviewing.name', 'Start review'],
                   ['change_owner','* -> *'],
                   ['change_owner.name','Change Owner to'],
                   ['change_owner.operations','set_review_owner'],
                   ['change_owner.permissions','CODE_REVIEW_MGR'],
                   ['change_owner.default','-1'],
                   ]
        wf_section = 'peerreview-resource_workflow'

        if wf_section not in env.config.sections():
            env.log.info("Adding default workflow for 'peerreview' to config.")
            for item in wf_data:
                env.config.set(wf_section, item[0], item[1])
            env.config.save()

        # Add default workflow for peerreviewer

        wf_data = [['reviewing', 'new -> in-review'],
                   ['reviewing.name', 'Start review'],
                   ['review_done', 'in-review -> reviewed'],
                   ['review_done.name', 'Mark review as done.'],
                   ['reopen', 'in-review, reviewed -> new'],
                   ['reopen.name', "Reset review state to 'new'"],
                   ]
        wf_section = 'peerreviewer-resource_workflow'

        if wf_section not in env.config.sections():
            env.log.info("Adding default workflow for 'peerreviewer' to config.")
            for item in wf_data:
                env.config.set(wf_section, item[0], item[1])
            env.config.save()

    def _get_version(self, cursor):
        cursor.execute("SELECT value FROM system WHERE name = %s", (db_name,))
        value = cursor.fetchone()
        val = int(value[0]) if value else 0
        return val

def get_users(env):
    db = env.get_read_db()
    cursor = db.cursor()
    cursor.execute("""SELECT DISTINCT p1.username FROM permission AS p1
                      LEFT JOIN permission AS p2 ON p1.action = p2.username
                      WHERE p2.action IN ('CODE_REVIEW_DEV', 'CODE_REVIEW_MGR')
                      OR p1.action IN ('CODE_REVIEW_DEV', 'CODE_REVIEW_MGR', 'TRAC_ADMIN')
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


# Obsolete use ReviewCommentModel instead
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
                created = to_utimestamp(datetime_now(utc))
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
