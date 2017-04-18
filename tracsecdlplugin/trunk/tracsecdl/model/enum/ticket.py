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

from trac.core            import TracError
from trac.ticket          import model
from tracsecdl.model.base import SecDlModel

class SecDlTicket (SecDlModel):

    """Abstract base class to access some ticket properties.

    The ticket stuff tables are a bit different from ours, this class provides
    some wrapper methods to access these properties in the same way the
    additional download properties are accessed. Only the necessary stuff is
    implemented here, the proper classes should be used for everything else.
    """

    abstract = True
    _model   = None

    def assert_id (self, id):

        """Make sure a property exists.

        This method will check the ID specified as first parameter for
        existence. If an ID is specified and it does not exists in the
        database, an exception will be raised. If no ID is specified (either
        None or an empty string), None will be returned.
        """

        id = self._string_or_none (id)

        if id:
            try:
                self._model (self.env, id)
            except:
                raise TracError ('Enum %s not found.' % id)

        return id

    def get_all (self, descr = False):

        """Returns a list with all properties.

        This method will return a list containing all defined properties. The
        list will contain dictionaries, with the keys 'id' and 'name' (note
        that for these properties both will be the same). The optional
        parameter 'descr' will be ignored and is provided for compatibilty with
        the SecDlEnum classes only. If no properties are defined the list
        returned will be empty.
        """

        sel = self._model.select (self.env)
        all = []
        for s in sel:
            all.append ({'id': s.name, 'name': s.name})
        return all

# The following classes need to override the _model member of the base class,
# it has to be set to the class object that implements the ticket property
# model.

class SecDlComponent (SecDlTicket):
    """Provides access to the ticket component property."""
    _model = model.Component

class SecDlMilestone (SecDlTicket):
    """Provides access to the ticket milestone property."""
    _model = model.Milestone

class SecDlVersion (SecDlTicket):
    """Provides access to the ticket version property."""
    _model = model.Version

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: