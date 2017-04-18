# Copyright 2010-2011, 2014 Stefan Goebel - <tracsecdl -at- subtype -dot- de>
#
# This file is part of TracSecDl.
#
# TracSecDl is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# TracSecDl is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# TracSecDl. If not, see <http://www.gnu.org/licenses/>.

from trac.core      import Component
from trac.util.text import to_unicode

class SecDlModel (Component):

    """Abstract base class providing some basic database methods."""

    # The table prefix, you also need to change this in the database upgrade
    # scripts if you change the value defined here:
    _prefix = 'sdl_'

    # The _field member will contain the actual table name used by the
    # individual models. It has to be overridden in the inheriting classes:
    _field  = None

    def _cursor (self):
        """Return a database handle and a cursor.

        The database handle and the cursor will be returned as (handle, cursor)
        tuple.
        """
        db = self.env.get_db_cnx ()
        cs = db.cursor ()
        return (db, cs)

    def _name (self, name):
        """Convert and check a property name.

        The name is always required and may not be empty. This method will
        convert the name (specified as first parameter) to unicode and check
        it, if it is False in boolean context an error will be raised, else the
        unicode name will be returned.
        """
        name = to_unicode (name).strip ()
        if not name:
            raise ValueError ('Empty names are not allowed.')
        return name

    def _string_or_none (self, string):
        """Returns a unicode string or None.

        This method converts the string specified as first parameter to
        unicode, if the result is False in boolean context None will be
        returned, else the unicode string. If the parameter is None already, it
        will simply be returned.
        """
        if not string:
            return None
        string = to_unicode (string).strip ()
        if string:
            return string
        else:
            return None

    def _int_or_none (self, integer):
        """Returns an integer or None.

        Basically the same as _string_or_none(), only for integer values. None
        will be returned if the value of the first parameter is not greater
        than zero.
        """
        if not integer:
            return None
        integer = int (integer)
        if integer > 0:
            return integer
        else:
            return None

    def _table (self, name = None):
        """Return the table name for the current model.

        This method returns the table name for the model, that is the prefix
        and the field name concatenated.
        """
        if name is None:
            if not self._field:
                raise NotImplementedError
            return self._prefix + self._field
        return self._prefix + name

    def assert_id (self, id):
        """Makes sure an ID does exist.

        This method checks the ID specified as first parameter for existence.
        If it does not exist, an error will be raised. If the value of the
        parameter is False in boolean context, None will be returned. If it
        does exist the parameter explicitely converted to an integer value will
        be returned.
        """
        if not id:
            return None
        (db, cs) = self._cursor ()
        sql = 'SELECT id FROM %s WHERE id=%%s' % self._table ()
        try:
            cs.execute (sql, [int (id)])
            for row in cs:
                return int (id)
        except:
            raise
        return None

    def delete (self, id):
        """Delete an entry from the database.

        The first parameter must be the ID of the entry to delete. The method
        will return True if there was no error during the operation (ie. even
        if there is no entry with the given ID True will be returned if the
        query itself succeeds). Only in case of an error an exception will be
        raised.
        """
        (db, cs) = self._cursor ()
        sql = 'DELETE FROM %s WHERE id=%%s' % self._table ()
        try:
            cs.execute (sql, [int (id)])
            db.commit ()
        except:
            db.rollback ()
            raise
        return True

    def delete_all (self):
        """Deletes all entries of the current model.

        This method will delete all entries unconditionally. It will always
        return True if there was no error, regardless of how many (if any)
        properties were deleted. In case of an error an exception will be
        raised.
        """
        (db, cs) = self._cursor ()
        sql = 'DELETE FROM %s' % self._table ()
        try:
            cs.execute (sql)
            db.commit ()
        except:
            db.rollback ()
            raise
        return True

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: