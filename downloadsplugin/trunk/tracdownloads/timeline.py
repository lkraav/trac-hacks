# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.resource import Resource, get_resource_description, \
                          get_resource_name, get_resource_url
from trac.timeline import ITimelineEventProvider
from trac.util.datefmt import to_datetime, to_timestamp, utc
from trac.util.html import html

from tracdownloads.api import DownloadsApi


class DownloadsTimeline(Component):
    """
        The timeline module implements timeline events when new downloads are
        inserted.
    """
    implements(ITimelineEventProvider)

    # ITimelineEventProvider

    def get_timeline_filters(self, req):
        if 'DOWNLOADS_VIEW' in req.perm:
            yield ('downloads', 'Downloads changes')

    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("start: %s, stop: %s, filters: %s",
                       start, stop, filters)
        if ('downloads' in filters) and ('DOWNLOADS_VIEW' in req.perm):
            api = self.env[DownloadsApi]

            # Get message events
            for download in api.get_new_downloads(to_timestamp(start),
                                                  to_timestamp(stop)):
                yield ('newticket', to_datetime(download['time'], utc),
                       download['author'], download['id'])

    def render_timeline_event(self, context, field, event):
        # Decompose event data.
        id = event[3]

        # Return appropriate content.
        resource = Resource('downloads', id)
        if field == 'url':
            if 'DOWNLOADS_VIEW' in context.req.perm(resource):
                return get_resource_url(self.env, resource, context.req.href)
            else:
                return '#'
        elif field == 'title':
            return html('New download ',
                        html.em(get_resource_name(self.env, resource)),
                        ' created')
        elif field == 'description':
            return get_resource_description(self.env, resource, 'summary')
