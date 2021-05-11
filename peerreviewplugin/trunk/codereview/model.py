# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#

from collections import defaultdict, namedtuple
from datetime import datetime
from trac.core import Component, implements, TracError
from trac.db import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant
from trac.search.api import shorten_result
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc
from trac.util.translation import N_, _
from .compat import itervalues
from .tracgenericclass.model import IConcreteClassProvider, AbstractVariableFieldsObject, \
    need_db_create_for_realm, create_db_for_realm, need_db_upgrade_for_realm, upgrade_db_for_realm

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
        """Create an instance which is identified by the values in dict 'key'

        @param key: dict with key: identifier 'review_id', val: actual value from the database.

        Note: while it's technically possible to have several identifiers uniquely describing an
        object here, this class only use a single one.
        """
        return PeerReviewModel(self.env, key['review_id'], 'peerreview')

    def change_status(self, new_status, author=None):
        """Called from the change object listener to change state of review and connected files.

        Note that files are only set to closed when the new status is one of

        [peerreview]
        terminal_review_states = ...

        as set in trac.ini. For any other status the file status is set to 'new'.

        @param new_status: new status for this review
        @param author: user causing this change
        @return:
        """
        finish_states = self.env.config.getlist("peerreview", "terminal_review_states")
        if new_status in finish_states:
            self['closed'] = to_utimestamp(datetime_now(utc))
        else:
            self['closed'] = None
        self['status'] = new_status
        self.save_changes(author=author)

        # Handle changeset reviews

        dm = ReviewDataModel(self.env)
        dm['type'] = 'changeset'
        dm['review_id'] = self['review_id']
        rev_data = list(dm.list_matching_objects())
        if rev_data:
            changeset = rev_data[-1]
            if self['status'] == 'closed':
                # Mark changeset review as closed. 'data' will be something like: reponame:xxxxx:closed
                changeset['data'] += u':closed'
            else:
                # User reopened the review
                if changeset['data'].endswith(u':closed'):
                    changeset['data'] = changeset['data'][:-7]
            changeset.save_changes(author)

        # Change the status of files attached to this review

        r_tmpl = ReviewFileModel(self.env)
        r_tmpl.clear_props()
        r_tmpl['review_id'] = self['review_id']
        all_files = r_tmpl.list_matching_objects()  # This is a generator
        # We only mark files for terminal states
        if new_status in finish_states:
            status = new_status
            self.env.log.debug("PeerReviewModel: changing status of attached files for review '#%s'to '%s'" %
                               (self['review_id'], new_status))
        else:
            status = 'new'
            self.env.log.debug("PeerReviewModel: changing status of attached files for review '#%s'to '%s'" %
                               (self['review_id'], status))
        for f in all_files:
            f['status'] = status
            f.save_changes(author, "Status of review '#%s' changed." % self['review_id'])

    @classmethod
    def reviews_by_period(cls, env, start_timestamp, end_timestamp):
        """Used for getting timeline reviews.

        Times are compared using '>=' and '<='.

        @param env: Trac Environment object
        @param start_timestamp: start time as a utimestamp
        @param end_timestamp: end time as a utimestamp
        @return: list of PeerReviewModels matching the times ordered by field 'created'
        """
        reviews = []
        with env.db_query as db:
            for row in db("SELECT review_id FROM peerreview WHERE created >= %s AND created <= %s ORDER BY created",
                          (start_timestamp, end_timestamp)):
                reviews.append(cls(env, row[0]))
        return reviews

    @classmethod
    def select_all_reviews(cls, env):
        with env.db_query as db:
            for row in db("SELECT review_id FROM peerreview"):
                yield cls(env, row[0])

    def get_search_results(self, req, terms, filters):
        results = {}
        set_lst = []
        review = PeerReviewModel(self.env)
        if "peerreview:all" in terms:
            # list all codereviews if no search term is given. This is the behaviour of the old
            # codereview search page.
            self.env.log.info("SEARCH terms: %s 2", terms)

            for rev in PeerReviewModel.select_all_reviews(self.env):
                title = u"Review #%s - %s: %s" % (rev['review_id'], rev['status'], rev['name'])
                yield (req.href.peerreviewview(rev['review_id']),
                       title,
                       from_utimestamp(rev['created']),
                       rev['owner'],
                       shorten_result(rev['notes']))
            return

        for term in terms:
            seen_reviews = []
            for field in ('name', 'notes', 'owner', 'status'):
                review.clear_props()
                review[field] = "%" + term + "%"
                res = review.list_matching_objects(exact_match=False)
                for rev in res:
                    seen_reviews.append(rev['review_id'])
                    if rev['review_id'] not in results:
                        results[rev['review_id']] = rev
            set_lst.append(set(seen_reviews))

        if results:
            # Calculate common review_ids over all sets
            res_set = set_lst[0]
            for item in set_lst[1:]:
                res_set &= item

            for rev_id in res_set:
                rev = results[rev_id]
                title = u"Review #%s - %s: %s" % (rev['review_id'], rev['status'], rev['name'])
                yield (req.href.peerreviewview(rev['review_id']),
                       title,
                       from_utimestamp(rev['created']),
                       rev['owner'],
                       shorten_result(rev['notes']))


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

    @staticmethod
    def select_by_review_id(env, review_id):
        """Get all reviewers associated with the review with the given id

        @param env: Trac Environment object
        @param review_id: review id as int
        @return: a generator returning PeerReviewerModels
        """
        rm = PeerReviewerModel(env)
        rm.clear_props()
        rm['review_id'] = review_id
        return rm.list_matching_objects()

    @classmethod
    def delete_by_review_id_and_name(cls, env, review_id, name):
        """Delete the reviewer 'name' from the review eith id 'review_id'.


        @param env: Trac Environment object
        @param review_id: id of the review as an int
        @param name: name of the reviewer.
        @return: None
        """
        reviewer = cls(env)
        reviewer['review_id'] = 1
        reviewer['reviewer'] = name
        res = list(reviewer.list_matching_objects())
        if len(res) > 1:
            raise ValueError("Found two reviewers with name '%s' for review '%s'." % (name, review_id))
        res[0].delete()


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
    def file_dict_by_review(cls, env):
        """Return a dict with review_id as key (int) and a file list as value.

        @return dict: key: review id as int, val: list of ReviewFileModels

        Note that files with review_id == 0 are omitted here. These are files
        which are members of file lists belonging to projects.
        """
        files_dict = defaultdict(list)
        with env.db_query as db:
            for row in db("SELECT file_id, review_id FROM peerreviewfile WHERE review_id != 0 ORDER BY review_id"):
                file_ = cls(env, row[0])
                files_dict[row[1]].append(file_)
        return files_dict

    @staticmethod
    def delete_files_by_project_name(env, proj_name):
        """Delete all file information belonging to project proj_name.

        @param env: Trac environment object
        @param proj_name: name of project. Used to filter by 'project' column
        @return: None

        It's possible to have a list of all files belonging to a project. Using this
        list one may check which files are not yet reviewed.
        These files are those in the table which have data in the 'project' column.
        The review_id is set to 0.
        """
        with env.db_transaction as db:
            db("DELETE FROM peerreviewfile WHERE project=%s", (proj_name,))

    @staticmethod
    def select_by_review(env, review_id):
        """Get all file objects for a given review_id.
        @param env: Trac Environment object
        @param review_id: id of a review as int
        @return: Returns a generator.

        Note that review_id 0 is allowed here to query files belonging to
        project file lists.
        """
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

        with env.db_query as db:
            cursor = db.cursor()
            cursor.execute("SELECT comment_id, type, data FROM peerreviewdata "
                           "WHERE file_id = %s AND owner = %s",
                           (file_id, owner))
            return cursor.fetchall()

    @classmethod
    def comments_for_owner(cls, env, owner):
        """Return a list of comment data for owner.
        """
        with env.db_query as db:
            cursor = db.cursor()
            cursor.execute("SELECT comment_id, review_id, type, data FROM peerreviewdata "
                           "WHERE owner = %s", (owner,))
            return cursor.fetchall()

    @classmethod
    def all_file_project_data(cls, env):
        """Return a dict with project name as key and a dict with project information as value."""
        fileprojectname, datatype, data = range(3)
        sql = """SELECT n.data AS name , r.type, r.data FROM peerreviewdata AS n
                 JOIN peerreviewdata AS r ON r.data_key = n.data
                 WHERE n.type = 'fileproject'"""
        with env.db_query as db:
            cursor = db.cursor()
            cursor.execute(sql)
            files_dict = defaultdict(dict)
            for row in cursor:
                files_dict[row[fileprojectname]][row[datatype]] = row[data]
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
        self.children = {}

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

    @staticmethod
    def comment_ids_by_file_id(env):
        """Return a dict with file_id as key and a comment id list as value.

        @param env: Trac Environment object
        @return dict with key: file id as int, val: list of comment ids for that file as int
        """
        the_dict = defaultdict(list)
        for row in env.db_query("SELECT comment_id, file_id FROM peerreviewcomment"):
            the_dict[row[1]].append(row[0])
        return the_dict

    @staticmethod
    def select_by_file_id(env, file_id):
        """Return all comments for the file specified by 'file_id'.

        :param env: Trac Environment object
        :param file_id: file id as int. All comments for this file are returned
        :return: generator for ReviewCommentModels
        """
        rcm = ReviewCommentModel(env)
        rcm.clear_props()
        rcm['file_id'] = file_id
        return rcm.list_matching_objects()

    @staticmethod
    def create_comment_tree(env, fileid, line):
        """Create a comment tree for the given file and line number.

        :param env: Trac environment object
        :param fileid: id of a peerreviewfile
        :param line: line number we wnat to get comments for
        :return dict with key: comment id, val: comment data as a namedtuple
                each comments 'children' dict is properly populated thus for each
                comment we have a (sub)tree. Comments with parent_id = -1 are root
                comments.
        """
        Comment = namedtuple('Comment', "children, comment_id, file_id, parent_id, line, author, comment, created")
        tree = {}
        for row in env.db_query("SELECT comment_id, file_id, parent_id, line_num, author, comment, created"
                                " FROM peerreviewcomment WHERE file_id = %s"
                                " AND line_num = %s"
                                " ORDER by created", (fileid, line)):
            comment = Comment({}, *row)
            tree[comment.comment_id] = comment
        for comment in itervalues(tree):
            if comment.parent_id != -1 and comment.parent_id in tree:
                tree[comment.parent_id].children[comment.comment_id] = comment
        return tree


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

    def environment_needs_upgrade(self, db_=None):
        with self.env.db_query as db:
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
        with self.env.db_transaction as db:
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
                   ['change_owner', '* -> *'],
                   ['change_owner.name', 'Change Owner to'],
                   ['change_owner.operations', 'set_review_owner'],
                   ['change_owner.permissions', 'CODE_REVIEW_MGR'],
                   ['change_owner.default', '-1'],
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
    users = []
    with env.db_query as db:
        cursor = db.cursor()
        cursor.execute("""SELECT DISTINCT p1.username FROM permission AS p1
                          LEFT JOIN permission AS p2 ON p1.action = p2.username
                          WHERE p2.action IN ('CODE_REVIEW_DEV', 'CODE_REVIEW_MGR')
                          OR p1.action IN ('CODE_REVIEW_DEV', 'CODE_REVIEW_MGR', 'TRAC_ADMIN')
                          """)
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


# Deprecated use ReviewCommentModel instead
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

    @classmethod
    def select_by_file_id(cls, env, file_id):
        with env.db_query as db:
            cursor = db.cursor()
            cursor.execute("SELECT comment_id, file_id, parent_id, line_num, author, comment, attachment_path, created FROM "
                           "peerreviewcomment WHERE file_id=%s ORDER BY line_num", (file_id,))
            comments = []
            for row in cursor:
                c = cls(env)
                c._init_from_row(row)
                comments.append(c)
        return comments
