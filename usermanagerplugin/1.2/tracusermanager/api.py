# -*- coding: iso-8859-1 -*-
#
# Copyright 2008 Optaros, Inc.
#
try:
    import threading
except ImportError:
    import dummy_threading as threading

import time

from trac.core import Component, ExtensionPoint, Interface, TracError, \
                      implements
from trac.config import ExtensionOption
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider


class IUserAttributeChangeListener(Interface):
    def user_attribute_changed(username, attribute, old_value, new_value):
        """
        Called when a user attribute changes.
        """


class User(object):
    """Object representing a user"""

    def __init__(self, username=None, user_manager=None, **attr):
        self.username = username
        self.user_manager = user_manager
        self.default_attributes = attr
        self.changes = {}
        self.deleted = {}

    def exists(self):
        if self.store:
            return len(self.user_manager.search_users(self.username)) > 0
        return False

    def __getitem__(self, attribute):
        if attribute in self.changes:
            return self.changes[attribute]
        if self.user_manager:
            value = self.user_manager.get_user_attribute(self.username,
                                                         attribute)
            if value:
                return value
            elif attribute == 'username':
                return self.username
        if attribute in self.default_attributes:
            return self.default_attributes[attribute]

        return None

    def __setitem__(self, attribute, value):
        self.changes[attribute] = value

    def __delitem__(self, attribute):
        self.deleted[attribute] = 1

    def save(self):
        return self.user_manager.save_user(self)


class IUserStore(Interface):

    def get_supported_user_operations(username):
        """Returns supported operations
        in form of [operation, ].
        """

    def execute_user_operation(operation, user, operation_arguments):
        """Executes user operation.
        """

    def create_user(username):
        """Creates an user.
        Returns True if succeeded.
        """

    def search_users(user_pattern):
        """Returns a list of user names that matches user_pattern.
        """

    def delete_user(username):
        """Deletes an user.
        Returns True if the delete operation succeded.
        """


class IAttributeProvider(Interface):
    def get_user_attribute(username, attribute):
        """Returns user's attributes.

        @param username: str
        @param attribute: str"""

    def set_user_attribute(username, attribute, value):
        """Sets user's attribute value.

        @param username: str
        @param attribute: str
        @param value: str
        @return: bool
        """

    def delete_user_attribute(username, attribute):
        """Removes user attribute

        @param username: str
        @param attribute: str
        @return: bool
        """

    def get_usernames_with_attributes(attributes_dict):
        """Returns a list of usernames
        that have "user[attributes_dict.keys] like attributes_dict.values".

        @param attributes_dict: str
        @return: list"""


class UserManager(Component):
    implements(ITemplateProvider)

    user_store = ExtensionOption(
        'user_manager', 'user_store', IUserStore, 'SessionUserStore',
        """Name of the component implementing `IUserStore`, which is used
        for storing project's team""")

    attribute_provider = ExtensionOption(
        'user_manager', 'attribute_provider', IAttributeProvider,
        'SessionAttributeProvider',
        """Name of the component implementing `IAttributeProvider`, which is
        used for storing user attributes""")

    change_listeners = ExtensionPoint(IUserAttributeChangeListener)

    # Public methods

    def get_user(self, username):
        return User(username, self)

    def get_active_users(self):
        """Returns a list with the current users(team)
        in form of [tracusermanager.api.User, ]

        @return: list"""
        return self.search_users()

    def save_user(self, user):
        for attribute, value in user.changes.items():
            self.set_user_attribute(user.username, attribute, value)
        for attribute in user.deleted.keys():
            self.delete_user_attribute(user.username, attribute)
        return True

    # IUserStore methods
    def get_supported_user_operations(self, username):
        return self.user_store.get_supported_user_operations(username)

    def execute_user_operation(self, operation, user, operation_arguments):
        return self.user_store.execute_user_operation(operation, user,
                                                      operation_arguments)

    def create_user(self, user):
        if user.username is None:
            raise TracError(_("Username must be specified in order to "
                              "create it"))
        if self.user_store.create_user(user.username):
            user_attributes = user.default_attributes
            user_attributes.update(user.changes)
            for attribute, value in user_attributes.items():
                self.set_user_attribute(user.username, attribute, value)
            return True
        return False

    def search_users(self, user_templates=[]):
        """Returns a list of users matching
        user_templates."""
        search_result = {}

        if isinstance(user_templates, str):
            templates = [User(user_templates)]
        elif not isinstance(user_templates, list):
            templates = [user_templates]
        else:
            templates = user_templates

        if not templates:
            # no filters are passed so we'll return all users
            return [self.get_user(username)
                    for username in self.user_store.search_users()]

        # search
        for user_template in templates:
            # by username
            if user_template.username is not None:
                search_result.update([(username, self.get_user(username))
                                      for username in
                                      self.user_store.search_users(
                                          user_template.username)])
            else:
                search_attrs = user_template.default_attributes.copy()
                search_attrs.update(user_template.changes.copy())
                search_attrs.update(enabled='1')
                attrs = self.attribute_provider \
                    .get_usernames_with_attributes(search_attrs)
                search_result.update([(username, self.get_user(username))
                                      for username in attrs])

        return search_result.values()

    def delete_user(self, username):
        try:
            from acct_mgr.api import AccountManager
        except ImportError:
            self.log.error("Unable to delete user's authentication details")
        else:
            if AccountManager(self.env).has_user(username):
                AccountManager(self.env).delete_user(username)
        return self.user_store.delete_user(username)

    # IAttributeStore methods

    def get_user_attribute(self, username, attribute):
        return self.attribute_provider.get_user_attribute(username, attribute)

    def set_user_attribute(self, username, attribute, value):
        oldval = self.attribute_provider.get_user_attribute(username,
                                                            attribute)
        retval = self.attribute_provider.set_user_attribute(username,
                                                            attribute, value)
        for listener in self.change_listeners:
            listener.user_attribute_changed(username, attribute, oldval,
                                            value)
        return retval

    def delete_user_attribute(self, username, attribute):
        oldval = self.attribute_provider.get_user_attribute(username,
                                                            attribute)
        self.attribute_provider.delete_user_attribute(username, attribute)
        for listener in self.change_listeners:
            listener.user_attribute_changed(username, attribute, oldval, None)
        return self.attribute_provider.delete_user_attribute(username,
                                                             attribute)

    def get_usernames_with_attributes(self, attribute_dict):
        return self.attribute_provider.get_usernames_with_attributes(
            attribute_dict)

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracusermanager', 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracusermanager', resource_filename(__name__, 'htdocs'))]


class SessionUserStore(Component):
    implements(IUserStore)

    def get_supported_user_operations(self, username):
        return []

    def execute_user_operation(self, operation, user, operation_arguments):
        return True

    def create_user(self, username):
        with self.env.db_transaction as db:
            db("""
                INSERT INTO session (sid, last_visit, authenticated)
                VALUES(%s,%s,1)
                """, (username, int(time.time())))
            db("""
                DELETE FROM session_attribute
                WHERE sid=%s AND authenticated=1 AND name='enabled'
                """, (username,))
            db("""
                INSERT INTO session_attribute (sid,authenticated,name,value)
                VALUES(%s,1,'enabled','1')
                """, (username,))
            return True

    def search_users(self, username_pattern=None):
        if username_pattern is None:
            return [username for username, in self.env.db_query("""
                SELECT sid FROM session_attribute
                WHERE name='enabled' AND value='1'
                """)]
        else:
            return [username for username, in self.env.db_query("""
                SELECT sid FROM session_attribute
                WHERE sid LIKE %s AND name='enabled' AND value='1'
                """, (username_pattern,))]

    def delete_user(self, username):
        self.env.db_transaction("""
            DELETE FROM session_attribute
            WHERE sid=%s AND name='enabled'
            """, (username,))
        return True


class SessionAttributeProvider(Component):
    implements(IAttributeProvider)

    def get_user_attribute(self, username, attribute):
        for value, in self.env.db_query("""
                SELECT value FROM session_attribute
                WHERE sid=%s AND name=%s
                """, (username, attribute)):
            return value

    def set_user_attribute(self, username, attribute, value):
        """Sets user's attribute value.
        """
        with self.env.db_transaction as db:
            db("""
                DELETE FROM session_attribute WHERE sid=%s AND name=%s
                """, (username, attribute))
            db("""
                INSERT INTO session_attribute
                 (sid, authenticated, name, value)
                VALUES (%s, 1, %s, %s)
                """, (username, attribute, value))
            return True

    def delete_user_attribute(self, username, attribute):
        """Removes user attribute.
        """
        self.env.db_transaction("""
            DELETE FROM session_attribute WHERE sid=%s AND name=%s
            """, (username, attribute))
        return True

    def get_usernames_with_attributes(self, attributes_dict=None):
        """ Returns all usernames matching attributes_dict.

        Example: self.get_usernames_with_attributes(dict(name='John%',
                                                         email='%'))

        @param attributes_dict: dict
        @return: list
        """
        if attributes_dict is None:
            return [sid for sid, in self.env.db_query("""
                    SELECT sid FROM session_attribute WHERE name='enabled'
                    """)]
        else:
            # dict to list attr_dict = { k1:v1, k2:v2, ... } ->
            # [k1,v1,k2,v2..., len(attr_dict)]
            attributes_list = []
            for k, v in attributes_dict.items():
                attributes_list.append(
                    k.startswith('NOT_') and k[4:] or k)
                attributes_list.append(v)

            attributes_list.append(len(attributes_dict))

            with self.env.db_query as db:
                def _get_condition(k, v):
                    return "name=%s AND value " + \
                           (k.startswith('NOT_') and 'NOT' or '') + \
                           " %s" % db.like()

                return [id for id, in db("""
                        SELECT sid FROM session_attribute
                        WHERE %s GROUP BY sid HAVING count(*)=%%s
                        """ % ' OR '.join(_get_condition(k, v)
                                          for k, v in attributes_dict.items()),
                        attributes_list)]


class CachedSessionAttributeProvider(SessionAttributeProvider):
    CACHE_UPDATE_INTERVAL = 50

    def __init__(self):
        self._attribute_cache = {}
        self._attribute_cache_last_update = {}
        self._attribute_cache_lock = threading.RLock()

    def _update_cache(self, username, force=False):
        self._attribute_cache_lock.acquire()
        try:
            now = time.time()
            if now > self._attribute_cache_last_update.get(username, 0) + \
                    CachedSessionAttributeProvider.CACHE_UPDATE_INTERVAL \
                    or username not in self._attribute_cache \
                    or force:
                self._attribute_cache[username] = {}
                self._attribute_cache[username] = \
                    dict((name, value)
                         for name, value in self.env.db_query("""
                            SELECT name, value FROM session_attribute
                            WHERE sid=%s
                            """, (username,)))
                self._attribute_cache_last_update[username] = now
                self.log.debug("Updating SessionAttributeProvider attribute "
                               "cache for user <%s>", username)
        finally:
            self._attribute_cache_lock.release()

    def get_user_attribute(self, username, attribute):
        self._update_cache(username)
        if username in self._attribute_cache:
            return self._attribute_cache[username].get(attribute)
        return None

    def set_user_attribute(self, username, attribute, value):
        return_value = super(CachedSessionAttributeProvider,
                             self).set_user_attribute(username, attribute,
                                                      value)
        self._update_cache(username, force=True)
        return return_value

    def delete_user_attribute(self, username, attribute):
        return_value = super(CachedSessionAttributeProvider,
                             self).delete_user_attribute(username, attribute)
        self._update_cache(username, force=True)
        return return_value


class EnvironmentFixKnownUsers(Component):
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self):
        def inline_overwrite_get_known_users(as_dict=False):
            users = UserManager(self.env).get_active_users()
            if users:
                if as_dict:
                    return dict((user.username, (user['name'], user['email']))
                                for user in users)
                else:
                    return iter((user.username, user['name'], user['email'])
                                for user in users)
            else:
                return self.env.__class__.get_known_users(self.env)

        self.env.get_known_users = inline_overwrite_get_known_users

        return False

    def upgrade_environment(self):
        pass
