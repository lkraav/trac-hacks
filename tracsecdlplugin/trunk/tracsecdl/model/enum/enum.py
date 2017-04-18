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

from tracsecdl.model.base import SecDlModel

class SecDlEnum (SecDlModel):

    """Abstract base class for some download properties."""

    abstract = True
    _field   = None

    def add (self, name, descr = None):

        """Add a new property to the database.

        The first parameter must be the name of the property, this is required
        and names must be unique. The second optional parameter is a
        description for the new property, it defaults to None, empty strings
        are automatically replaced by None. This method returns the ID of the
        new property if the operation was successful. All other cases are
        fatal errors and an exception will be raised.
        """

        (db, cs) = self._cursor ()

        nam = self._name (name)
        des = self._string_or_none (descr)
        tbl = self._table ()
        sql = 'INSERT INTO %s (name, description) VALUES (%%s, %%s)' % tbl

        try:
            cs.execute (sql, (nam, des))
            db.commit ()
            return db.get_last_id (cs, tbl, 'id')
        except:
            db.rollback ()
            raise

    def delete (self, id):

        """Deletes a property entry.

        The first parameter must be the ID of the property to delete. Note that
        this method will remove all foreign key references in the main download
        table. For return values see SecDlModel.delete(). If something goes
        wrong an exception is raised.
        """

        (db, cs) = self._cursor ()

        tbl = self._prefix + 'download'
        sql = 'UPDATE %s SET %s=NULL WHERE %s=%%s' % (
                tbl, self._field, self._field
            )

        try:
            cs.execute (sql, [id])
            db.commit ()
        except:
            db.rollback ()
            raise

        super (SecDlEnum, self).delete (id)

    def edit (self, id, name, descr = None):

        """Change the name and/or description of a property.

        This function will alter the stored data of the property, specified by
        its ID as first parameter. The second (and required) parameter is the
        new name of the property, names must be unique. The third parameter is
        the new description, it is optional and defaults to None. Empty strings
        are replaced by None. This method will return True if the database
        could be updated successfully (this does not necessarily mean that data
        has been changed), in case of an error an exception will be raised.
        """

        (db, cs) = self._cursor ()

        nam = self._name (name)
        des = self._string_or_none (descr)
        tbl = self._table ()
        sql = 'UPDATE %s SET name=%%s, description=%%s WHERE id=%%s' % tbl

        try:
            cs.execute (sql, (nam, des, int (id)))
            db.commit ()
        except:
            db.rollback ()
            raise

        return True

    def get (self, id):

        """Get the data for a single property.

        This method will return the name and description of the property
        specified by its ID as first parameter. Data will be returned in a
        dictionary with 'id', 'name' and 'description' keys. In case of an
        error an exception will be raised, if no property with the specified ID
        exists None will be returned.
        """

        (db, cs) = self._cursor ()

        tbl = self._table ()
        sql = 'SELECT name, description FROM %s WHERE id=%%s' % tbl

        try:
            cs.execute (sql, [int (id)])
            for name, descr in cs:
                return {'id': int (id), 'name': name, 'description': descr}
        except:
            raise

        return None

    def get_all (self, descr = False):

        """Return a list containing all properties.

        This method will return a list with all properties, the list elements
        being dictionaries with 'name' and 'id' keys. If the optional parameter
        'descr' is True, the dictionaries will also contain the description of
        the properties (the key will be 'description'). The list will be empty
        if no properties are defined, in case of an error an exception will be
        raised.
        """

        (db, cs) = self._cursor ()

        tbl = self._table ()
        if descr:
            cls = 'id, name, description'
        else:
            cls = 'id, name'
        sql = 'SELECT %s FROM %s ORDER BY name' % (cls, tbl)

        res = []
        try:
            cs.execute (sql)
            for row in cs:
                res.append ({'id': int (row [0]), 'name': row [1]})
                if descr:
                    res [-1] ['description'] = row [2]
        except:
            raise

        return res

# The following classes need to override the _field member of the base class.
# Table names will be constructed from this, everything else is the same for
# all properties.

class SecDlArch (SecDlEnum):
    """Architecture property of the downloads, eg.: 'i386' or 'amd64'."""
    _field = 'architecture'

class SecDlPlatform (SecDlEnum):
    """Platform property of the downloads, eg. 'windows' or 'linux'."""
    _field = 'platform'

class SecDlType (SecDlEnum):
    """Type property of the downloads, eg. 'source' or 'binary'."""
    _field = 'type'

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: