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

import datetime
import socket
import struct
import re

from trac.util.datefmt    import to_timestamp, utc
from trac.util.text       import to_unicode
from tracsecdl.model.base import SecDlModel
from tracsecdl.model.enum import SecDlArch, SecDlPlatform, SecDlType, \
                                 SecDlComponent, SecDlMilestone, SecDlVersion

class SecDlDownload (SecDlModel):

    """Main class providing access to the download database.

    Note that this class really only handles the database, any file in the file
    system is unknown to it, files just happen to have some name and path based
    on some data in the download database.
    """

    # Table name without the prefix:
    _field   = 'download'

    # All table columns that are actually foreign keys (note: this does NOT
    # include the ticket properties 'component', 'milestone' and 'version'):
    _foreign = ['architecture', 'platform', 'type']

    # All table columns (including the foreign keys):
    _columns = [
            'id',
            'name',
            'url',
            'description',
            'size',
            'time',
            'last_request',
            'count',
            'author',
            'ip',
            'component',
            'milestone',
            'version',
            'architecture',
            'platform',
            'type',
            'hidden',
            'checksum_md5',
            'checksum_sha'
        ]

    def _ip_to_integer (self, ip):
        """Convert a dotted quad IP address to an integer."""
        return struct.unpack ('!L', socket.inet_aton (ip)) [0]

    def _integer_to_ip (self, integer):
        """Convert an integer IP address to dotted quad format."""
        return socket.inet_ntoa (struct.pack ('!L', integer))

    def _ip_or_none (self, ip):

        """Return an IP in integer format or None.

        This method will check the IP specified as first parameter and return
        either None (if it is False in boolean context) or the IP converted to
        integer format. If an IP address is specified it may be dotted quad or
        integer format (in the latter case it is returned as is if it passes a
        range check, if this check fails a ValueError is raised).
        """

        if not ip:
            return None
        try:
            integer = int (ip)
        except:
            return self._ip_to_integer (ip)
        else:
            if not 0 <= integer <= 4294967295:
                raise ValueError ('Invalid IP: %s' % integer)
            return integer

    def _checksum_or_none (self, string, length):

        """Checks a checksum string and returns the string or None.

        The first parameter specifies a checksum as hex string, the second
        parameter the required length of the string. If the checksum is False
        in boolean context, None is returned without any further checks. Else
        the string will be converted to unicode and lowercase characters, and
        it is checked if it is a valid hexadecimal string (ie. containing only
        a-f and 0-9) and if its length equals the specified one. If the checks
        succeed, the converted string will be returned, else an exception will
        be raised (ValueError).
        """

        if not string:
            return None
        string = to_unicode (string).strip ().lower ()
        if not string:
            return None
        elif not re.match (r'^[a-f0-9]{%i}$' % length, string):
            raise ValueError ('Invalid checksum: %s' % string)
        return string

    def columns (self):
        """Return a list containing all column names of the download table."""
        return self._columns

    def local_file_exists (self, name):

        """Checks if a file specified by name exists as local download.

        The first parameter must be the file name to check, the method returns
        True if an entry in the database exists for the specified file and it
        is a local download (ie. the URL field is NULL). If a file exists the
        download's ID will be returned, else False. In case of an error an
        exception is raised.
        """

        (db, cs) = self._cursor ()
        tbl = self._table ()
        sql = 'SELECT id FROM %s WHERE name=%%s AND url IS NULL' % tbl
        try:
            cs.execute (sql, [name])
            for row in cs:
                return int (row [0])
        except:
            raise
        return False

    def checksum (self, id, typ):

        """Returns the specified checksum for the specified download.

        The first parameter must be the download ID, the second one the
        checksum to return (either 'md5' or 'sha'). The method returns a
        dictionary containing the file name of the download, the checksum and
        the hidden value (the keys are 'name', 'checksum' and 'hidden'), unless
        no file is found for the given ID, the return value will be None in
        that case. An exception will be raised in case of an error.
        """

        if not typ in ('md5', 'sha'):
            raise ValueError ('Invalid checksum type: %s.' % typ)
        (db, cs) = self._cursor ()
        tbl = self._table ()
        sql = 'SELECT name, checksum_%s, hidden FROM %s WHERE id=%%s' % (
                typ, tbl
            )
        try:
            cs.execute (sql, [id])
            for name, checksum, hidden in cs:
                if hidden:
                    hidden = True
                else:
                    hidden = False
                return {'name': name, 'checksum': checksum, 'hidden': hidden}
        except:
            raise
        return None

    def redirect_data (self, id):

        """Returns redirect data for a specified download.

        This method returns the data necessary to send a redirect to the actual
        download URL. The return value will be a dictionary: 'name' will be the
        file name, 'url' the URL, 'hidden' the value of the 'hidden' property
        of the download. All these keys are guaranteed to exist, but the value
        may be empty (in case of the URL for local downloads). The 'hidden'
        value will be either True or False. If a download with the specified ID
        does not exist None will be returned. In case of an error an exception
        will be raised.
        """

        (db, cs) = self._cursor ()
        sql = 'SELECT name, url, hidden FROM %s WHERE id=%%s' % self._table ()
        try:
            cs.execute (sql, [id])
            for name, url, hidden in cs:
                if hidden:
                    hidden = True
                else:
                    hidden = False
                return {'name': name, 'url': url, 'hidden': hidden}
        except:
            raise
        return None

    def get_description (self):

        """Returns the description for the download index page.

        This method returns the description to be shown on the download index
        page. It may be None if there is no description in the database or if
        it is not set. In case of an error an exception will be raised.
        """

        (db, cs) = self._cursor ()
        sql = 'SELECT value FROM system WHERE name=%s'
        try:
            cs.execute (sql, ['secdl_description'])
            for row in cs:
                return row [0]
        except:
            raise
        return None

    def edit_description (self, descr):

        """Updates the description of the download index page.

        This method will modify the description for the download index page,
        the first and only parameter must be the new description. Empty strings
        will be converted to None automatically, the actual value used for the
        update will be returned. An exception is raised in case of an error.
        """

        descr = self._string_or_none (descr)
        (db, cs) = self._cursor ()
        sql = 'UPDATE system SET value=%s WHERE name=%s'
        try:
            cs.execute (sql, (descr, 'secdl_description'))
            db.commit ()
        except:
            db.rollback ()
            raise
        return descr

    def count (self, id):

        """Increase counter and set last request time of a download.

        This method will increase the download counter of the download
        specified by its ID as first parameter by one and set the last request
        time to the current time. This method always returns True, in case of
        an error an exception is raised.
        """

        (db, cs) = self._cursor ()
        tbl = self._table ()
        now = to_timestamp (datetime.datetime.now (utc))
        sql = 'UPDATE %s SET count=count+1,last_request=%%s WHERE id=%%s' % tbl
        try:
            cs.execute (sql, (now, int (id)))
            db.commit ()
        except:
            db.rollback ()
            raise
        return True

    def get_local_size (self):

        """Return the total size in bytes of all local downloads.

        This method will return the total file size in bytes used by local
        downloads. It will be returned as an integer, if there are no local
        downloads it will be 0. In case of an error an exception will be
        raised.
        """

        (db, cs) = self._cursor ()
        sql = 'SELECT SUM(size) FROM %s WHERE url IS NULL' % self._table ()
        try:
            cs.execute (sql)
            for row in cs:
                return int (row [0] or 0)
        except:
            raise

    def get_local_number (self):

        """Return the number of local downloads.

        This method will return the number of locally available downloads (as
        an integer). In case of an error an exception will be raised.
        """

        (db, cs) = self._cursor ()
        sql = 'SELECT COUNT(*) FROM %s WHERE url IS NULL' % self._table ()
        try:
            cs.execute (sql)
            for row in cs:
                return int (row [0])
        except:
            raise

    def get_local_file (self, id):

        """Returns the file name for a given ID.

        The first parameter is the download ID, the method will return the file
        name that belongs to this download. If there is no download with the
        specified ID, or the download is not local, None will be returned. In
        case of an error an exception will be raised.
        """

        (db, cs) = self._cursor ()
        tbl = self._table ()
        sql = 'SELECT name FROM %s WHERE id=%%s AND url IS NULL' % tbl
        try:
            cs.execute (sql, [id])
            for row in cs:
                return row [0]
        except:
            raise
        return None

    def get_local_files (self):

        """Returns a list of all local files, including ID and file name.

        This method will return a list of all local downloads, the list will
        contain (id, file_name) tuples in no specific order, and may be empty
        if no local downloads exist. If an error occurs an exception will be
        raised.
        """

        (db, cs) = self._cursor ()
        sql   = 'SELECT id, name FROM %s' % self._table ()
        files = []
        try:
            cs.execute (sql)
            for id, name in cs:
                files.append ((id, name))
        except:
            raise
        return files

    def get_timeline (self, start, stop, hidden = False):

        """Return a list of downloads for the timeline.

        The parameters are the start and stop time for the requested period (as
        'datetime' objects), and a flag to indicate if hidden downloads should
        be included (defaults to False). The list returned (which may be empty)
        contains dictionaries with the following keys: 'id', 'name', 'time',
        'size', 'author', 'url' and 'description'. If an error occurs an
        exception will be raised.
        """

        (db, cs) = self._cursor ()
        if hidden:
            hid = ''
        else:
            hid = ' AND hidden=0'
        cls = ['id', 'name', 'time', 'size', 'author', 'url', 'description']
        sql = 'SELECT %s FROM %s WHERE time>=%%s AND time<=%%s %s' % (
                ', '.join (cls), self._table (), hid
            )
        dls = []
        try:
            cs.execute (sql, (to_timestamp (start), to_timestamp (stop)))
            for row in cs:
                dls.append (dict (zip (cls, row)))
        except:
            raise
        return dls

    def get (self, id):

        """Returns a single download, including all data.

        The first parameter is the ID of the download. This method will return
        all data of it in a dictionary, the keys being the names of the columns
        in the download table. No joins are done, ie. only the data directly
        available in the download table will be returned. If the download does
        not exist for the given ID, None will be returned. In case of an error
        an exception will be raised.
        """

        (db, cs) = self._cursor ()
        cls = ', '.join (self._columns)
        sql = 'SELECT %s FROM %s WHERE id=%%s' % (cls, self._table ())
        try:
            cs.execute (sql, [id])
            for row in cs:
                res = dict (zip (self._columns, row))
                res ['ip'] = self._integer_to_ip (res ['ip'])
                return res
        except:
            raise
        return None

    def get_all (self, fields = [], order = [], hidden = False):

        """Returns a list of all downloads.

        This method will return a list of all downloads. There are three
        parameters: 'fields', 'order' and 'hidden'. The 'fields' parameter is
        required and must be set to a list containing the column names to
        return, see the source for a complete list. The 'order' parameter is
        optional, it defaults to an empty list. It may contain a list of
        columns to sort the results. The default sort order for any column is
        ascending, to sort by a column in descending order prepend a '!' to the
        column name. The order of the 'order' list is important. If the
        'fields' list or the 'order' list contain invalid column names, an
        exception is raised. The 'hidden' parameter is optional, if it is True,
        hidden downloads will be included in the list, if it is False (the
        default), they will be left out. The list returned may be empty if
        there are no downloads, else it will contain dictionaries for the
        downloads, the keys will be the same as the column names. If the IP is
        included, it will be returned in dotted quad format. If foreign keys
        are included (eg. 'platform'), there will be three keys added to the
        dictionary: '<field>_id', '<field>_name' and '<field>_description',
        containing the three values from the joined table. In case of an error
        an exception will be raised.
        """

        if not fields:
            raise ValueError ('No columns specified.')

        # Construct the column part of the query and the joins if required:
        columns    = []
        joins      = ''
        all_fields = []
        for field in fields:
            if not field in self._columns:
                raise ValueError ('Invalid field specified: %s.' % field)
            if field in self._foreign:
                tbl = self._prefix + field
                joins += 'LEFT JOIN %s ON %s.%s=%s.id ' % (
                        tbl, self._table (), field, tbl
                    )
                for col in ('id', 'name', 'description'):
                    all_fields.append (field + '_' + col)
                    columns.append (tbl + '.' + col)
            else:
                all_fields.append (field)
                columns.append (self._table () + '.' + field)
        columns = ', '.join (columns)

        # Construct the order part of the query:
        ord = ''
        for field in order:
            if field [0] == '!':
                f = field [1:]
            else:
                f = field
            if not f in self._columns:
                raise ValueError ('Invalid field for sorting: %s.' % f)
            if ord:
                ord += ', '
            if f in self._foreign:
                ord += '%s%s.name ' % (self._prefix, f)
            else:
                ord += '%s.%s ' % (self._table (), f)
            if field [0] == '!':
                ord += 'DESC'
            else:
                ord += 'ASC'
        if ord:
            ord = 'ORDER BY ' + ord

        # In case hidden downloads should be excluded:
        if not hidden:
            hidden = ' WHERE %s.hidden=0 ' % self._table ()
        else:
            hidden = ''

        # And put it all together:
        sql = 'SELECT %s FROM %s %s %s %s' % (
                columns, self._table (), joins, hidden, ord
            )

        (db, cs) = self._cursor ()

        try:
            cs.execute (sql)
            rows = []
            for row in cs:
                rows.append (dict (zip (all_fields, row)))
                if 'ip' in all_fields:
                    rows [-1] ['ip'] = self._integer_to_ip (rows [-1] ['ip'])
        except:
            raise

        return rows

    def add (self, **d):

        """Add a new download entry to the database.

        This method will add a new download to the database. An arbitrary
        number of named parameters may be specified, with the names being
        column names in the download table (see source code for a complete
        list). The only required parameter is 'name', specifying the file name
        of the download. Invalid column names will cause an exception to be
        raised, and the column names 'time', 'last_request', 'count' and 'id'
        will be ignored. Every other column than 'name' can be omitted, but if
        it is specified it must be a valid value for the appropriate column,
        and in case of foreign keys the value in the other table must exist. If
        an IP address is specified it must be valid dotted quad format or the
        integer representation. If the data could be added to the database the
        ID of the new download entry will be returned, in all other cases
        something went wrong and an exception will be raised.
        """

        for key in d.keys ():
            if key not in self._columns or key == 'id':
                raise ValueError ('Invalid key: %s.' % key)

        (db, cs) = self._cursor ()

        # Basic stuff to construct the SQL query:
        col = ', '.join (self._columns [1:])
        val = ', '.join (['%s'] * len (self._columns [1:]))
        tbl = self._table ()
        sql = 'INSERT INTO %s (%s) VALUES (%s)' % (tbl, col, val)

        # Check some values, if something's wrong an exception is raised:
        na = self._name           (d.get ('name'       ))
        ur = self._string_or_none (d.get ('url'        ))
        de = self._string_or_none (d.get ('description'))
        au = self._string_or_none (d.get ('author'     ))
        si = self._int_or_none    (d.get ('size'       ))
        ip = self._ip_or_none     (d.get ('ip'         ))

        # These are foreign keys, check existence (that sucks):
        cp = self.env [SecDlComponent].assert_id (d.get ('component'   ))
        ms = self.env [SecDlMilestone].assert_id (d.get ('milestone'   ))
        vs = self.env [SecDlVersion  ].assert_id (d.get ('version'     ))
        ar = self.env [SecDlArch     ].assert_id (d.get ('architecture'))
        pf = self.env [SecDlPlatform ].assert_id (d.get ('platform'    ))
        tp = self.env [SecDlType     ].assert_id (d.get ('type'        ))

        # Check for valid checksums:
        md = self._checksum_or_none (d.get ('checksum_md5'),  32)
        sh = self._checksum_or_none (d.get ('checksum_sha'), 128)

        # hidden is an integer:
        if d.get ('hidden', False):
            hd = 1
        else:
            hd = 0

        # These are not to be set by arguments:
        tm = to_timestamp (datetime.datetime.now (utc))
        lr = None
        cn = 0

        try:
            # CAREFUL NOW! DOWN WI^W^W The values must be in the same order as
            # the fields in the self._columns list (without the ID)!
            cs.execute (
                    sql,
                    (na,ur,de,si,tm,lr,cn,au,ip,cp,ms,vs,ar,pf,tp,hd,md,sh)
                )
            db.commit ()
            return db.get_last_id (cs, tbl, 'id')
        except:
            db.rollback ()
            raise

    def edit (self, id, **d):

        """Modify the data of a download.

        The first parameter must be the download ID, remaining parameters are
        named parameters of the form <column> = <new value>. All specified
        columns will be updated to contain the new data. If an invalid column
        is specified, or the column 'id' is specified, an exception will be
        raised, this is also the case if another error occurs. If everything
        went fine the method will return True (note that a True return value
        does not guarantee that data has actually been modified). (For more
        details on the format of the column values see the add() method.)
        """

        (db, cs) = self._cursor ()

        set = []
        val = []

        cslen = {'checksum_md5': 32, 'checksum_sha': 128}
        model = {
                'component'   : SecDlComponent,
                'milestone'   : SecDlMilestone,
                'version'     : SecDlVersion,
                'architecture': SecDlArch,
                'platform':     SecDlPlatform,
                'type':         SecDlType,
            }

        # check for validity of keys and values:
        for col in d.keys ():

            # Error if the column does not exist or is the 'id' column:
            if col not in self._columns or col == 'id':
                raise ValueError ('Invalid key: %s.' % col)

            # Column exists, append it to the list:
            set.append ('%s=%%s' % col)

            # Check the provided values according to their type:
            if col == 'name':
                val.append (self._name (d [col]))
            elif col == 'ip':
                val.append (self._ip_or_none (d [col]))
            elif col == 'hidden':
                if d [col]:
                    val.append (1)
                else:
                    val.append (0)
            elif col in ('size', 'time', 'last_request', 'count'):
                val.append (self._int_or_none (d [col]))
            elif col in ('checksum_md5', 'checksum_sha'):
                val.append (self._checksum_or_none (d [col], cslen [col]))
            elif col in model.keys ():
                val.append (self.env [model [col]].assert_id (d [col]))
            else:
                val.append (self._string_or_none (d [col]))

        val.append (int (id))

        # Construct the query:
        tbl = self._table ()
        sql = 'UPDATE %s SET %s WHERE id=%%s' % (tbl, ', '.join (set))

        # And execute it:
        try:
            cs.execute (sql, val)
            db.commit ()
        except:
            db.rollback ()
            raise

        return True

    def delete_remote (self):

        """Deletes all remote downloads from the database.

        This method will remove all downloads from the database that are remote
        downloads, ie. the 'url' field is not empty. In case of an error an
        exception will be raised, else the method will always return True.
        """

        (db, cs) = self._cursor ()
        sql = 'DELETE FROM %s WHERE url IS NOT NULL' % self._table ()
        try:
            cs.execute (sql)
            db.commit ()
        except:
            db.rollback ()
            raise
        return True

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: