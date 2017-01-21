# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.timeline import ITimelineEventProvider
from trac.util.datefmt import to_timestamp
from trac.util.html import html

from tracscreenshots.api import ScreenshotsApi
from tracscreenshots.core import _, tag_


class ScreenshotsTimeline(Component):
    """The timeline module implements timeline events when new
    screenshots are uploaded.
    """
    implements(ITimelineEventProvider)

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if 'SCREENSHOTS_VIEW' in req.perm:
            yield 'screenshots', _("Screenshots changes")

    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("start: %s, stop: %s, filters: %s",
                       start, stop, filters)
        if 'screenshots' in filters and 'SCREENSHOTS_VIEW' in req.perm:
            api = self.env[ScreenshotsApi]

            # Get message events
            for screenshot in api.get_new_screenshots(to_timestamp(start),
                                                      to_timestamp(stop)):
                yield ('newticket', screenshot['time'], screenshot['author'],
                       (screenshot['id'], screenshot['name'],
                        screenshot['description']))

    def render_timeline_event(self, context, field, event):
        id, name, description = event[3]
        if field == 'url':
            return context.href.screenshots(id)
        elif field == 'title':
            return tag_("New screenshot %(name)s created", name=html.em(name))
        elif field == 'description':
            return html(description)
