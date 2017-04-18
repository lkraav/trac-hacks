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

from genshi.builder      import tag
from trac.core           import Component, implements
from trac.timeline       import ITimelineEventProvider
from trac.web.chrome     import add_stylesheet
from trac.wiki.formatter import format_to_oneliner
from trac.util.datefmt   import to_datetime
from trac.util.text      import pretty_size
from tracsecdl.config    import SecDlConfig
from tracsecdl.model     import SecDlDownload

class SecDlTimeline (Component):

    """Include creation of downloads in Trac's timeline."""

    implements (ITimelineEventProvider)

    def get_timeline_filters (self, req):
        """Return a list of filters for the timeline.

        The filters must be (internal_name, label) tuples. (An optional third
        element - checked - may be provided, if it is omitted the filter is
        enabled by default.)
        """
        if 'SECDL_VIEW' in req.perm:
            yield 'secdl', 'New downloads'

    def get_timeline_events (self, req, start, stop, filters):
        """Return a list of timeline events for the specified period.

        'req' is a request instance, 'start' and 'stop' are 'datetime' objects
        specifying the requested period and 'filters' is a list of enabled
        timeline filters (containing the 'internal_name' returned by the
        get_timeline_filters() method.)

        Events are (kind, date, author, data) tuples, where 'kind' is a string
        used for categorizing the event (we use 'secdl' here), 'date' is a
        'datetime' object, 'author' is a user who created the download and
        'data' is the private data that the component will reuse when rendering
        the event (see render_timeline_event()).
        """
        if 'secdl' in filters and 'SECDL_VIEW' in req.perm:
            add_stylesheet (req, 'secdl/css/secdl.css')
            hid = 'SECDL_HIDDEN' in req.perm
            dls = self.env [SecDlDownload].get_timeline (start, stop, hid)
            for dl in dls:
                yield 'secdl', to_datetime (dl ['time']), dl ['author'], dl

    def render_timeline_event (self, context, field, event):

        """Render the specific timeline event.

        Parameters are the context, the field (either 'title', 'description' or
        'url') and the event tuple as returned by get_timeline_events().
        """

        dl = event [3]

        if field == 'url':
            return context.req.href (self.env [SecDlConfig] ['url'], dl ['id'])

        elif field == 'title':
            return tag ('New download ', tag.em (dl ['name']), ' created')

        elif field == 'description':
            data = []
            if dl ['url']:
                data.append ('[remote file]')
            else:
                data.append ('[local file]')
            if dl ['size']:
                data.append (' (%s) ' % pretty_size (dl ['size']))
            if dl ['description']:
                data.append (format_to_oneliner (
                        self.env, context, dl ['description']
                    ))
            return tag (data)

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: