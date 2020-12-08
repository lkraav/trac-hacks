# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#

from genshi.filters import Transformer
from trac.core import *
from trac.ticket.model import Ticket
from trac.util.html import html as tag
from trac.web.api import ITemplateStreamFilter, IRequestFilter

from simplemultiproject.model import *
from simplemultiproject.roadmap import create_proj_table
from simplemultiproject.smp_model import SmpProject
from simplemultiproject.session import get_project_filter_settings


class SmpTimelineProjectFilter(Component):
    """Allow filtering of timeline by projects."""

    implements(IRequestFilter, ITemplateStreamFilter)

    def __init__(self):
        self._SmpModel = SmpModel(self.env)
        self.smp_project = SmpProject(self.env)

    # IRequestFilter

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        path_elms = req.path_info.split('/')
        if data and len(path_elms) > 1 and path_elms[1] == 'timeline':
            # These are the defined events for the ticket subsystem
            ticket_kinds = ['newticket', 'closedticket', 'reopenedticket', 'editedticket', 'attachment']
            proj_filter = get_project_filter_settings(req, 'timeline', 'smp_projects', 'All')  # This returns a list of names
            filtered_events = []

            for event in data.get('events'):
                if event['kind'] in ticket_kinds:
                    resource = event['data'][0].parent if event['kind'] == 'attachment' else event['data'][0]
                    if event['kind'] in ticket_kinds and 'All' not in proj_filter and resource.realm == 'ticket':
                        # We have some ticket event, maybe attachment to ticket
                        tkt = Ticket(self.env, resource.id)
                        if tkt['project'] in proj_filter:
                            # New render function enhancing the title
                            event['render'] = self._lambda_render_func(tkt['project'], event['render'])
                            filtered_events.append(event)
                    else:
                        filtered_events.append(event)  # Show this event
                else:
                    filtered_events.append(event)  # Show this event

            data['events'] = filtered_events

        return template, data, content_type

    # ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        path_elms = req.path_info.split('/')
        if len(path_elms) > 1 and path_elms[1] == 'timeline':
            # Add project selection to the roadmap preferences
            xformer = Transformer('//form[@id="prefs"]')
            stream |= xformer.prepend(create_proj_table(self, self._SmpModel, req))

        return stream

    def _lambda_render_func(self, proj_name, old_render):
        """Lambda function which saves some parameters for our private
        render function.

        The timeline module calls render functions only with parameter field
        and context. In our private render function we need more information.
        So we replace the original render function stored in the event data
        with this one while storing the original pointer to the render
        function and the project name within this lambda. When the timeline
        module calls our own function field and context are forwarded together
        with our stored parameters.
        """
        return lambda field, context: self._render_ticket_event(field, context, proj_name, old_render)

    # Internal
    def _render_ticket_event(self, field, context, proj_name=None, old_render=None):
        """New render function which will render a ticket title with project name

        @param field: see render_timeline_event of ITimelineEventProvider
        @param context: see render_timeline_event of ITimelineEventProvider
        @param proj_name: Name of the project this event belongs too
        @param old_render: original render function associated with the timeline event
        """
        if old_render:
            tags = old_render(field, context)  # Let the ticket subsystem render the default
            if field == 'title':
                new_children = [tag.span(u"%s:" % proj_name), " "]  # prepend the project name to the title
                tags.children = new_children + tags.children
            return tags
        else:
            # We shouldn't end up here...
            self.env.log.error("Function for rendering timeline event is 'None'.")
            if field == 'title':
                return tag.em("Internal error in component %s" % self.__class__.__name__)
            else:
                return tag("")
