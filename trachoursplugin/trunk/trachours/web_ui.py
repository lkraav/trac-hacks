# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from genshi.builder import tag
from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from trac.core import *
from trac.ticket import Ticket
from trac.ticket.model import Milestone
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import (
    Chrome, ITemplateProvider, add_link, add_stylesheet
)

from componentdependencies.interface import IRequireComponents
from hours import TracHoursPlugin
from ticketsidebarprovider.interface import ITicketSidebarProvider
from ticketsidebarprovider.ticketsidebar import TicketSidebarProvider
from tracsqlhelper import get_all_dict, get_column
from utils import get_date, hours_format

from StringIO import StringIO
import calendar
import csv
import datetime
import time


class TracHoursRoadmapFilter(Component):
    
    implements(ITemplateStreamFilter, IRequireComponents)

    ### IRequireComponents methods

    def requires(self):
        return [TracHoursPlugin]

    ### ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        """
        filter the stream for the roadmap (/roadmap)
        and milestones /milestone/<milestone>
        """

        if filename in ('roadmap.html', 'milestone_view.html') and \
                'TICKET_VIEW_HOURS' in req.perm:
            trac_hours = TracHoursPlugin(self.env)

            hours = {}

            milestones = data.get('milestones')
            this_milestone = None

            if milestones is None:
                # /milestone view : only one milestone
                milestones = [data['milestone']]
                this_milestone = milestones[0].name
                find_xpath = "//div[@class='milestone']//h1"
                xpath = "//div[@class='milestone']//div[@class='info']"
            else:
                # /roadmap view
                find_xpath = "//li[@class='milestone']//h2/a"
                xpath = "//li[@class='milestone']//div[@class='info']"

            for milestone in milestones:
                hours[milestone.name] = dict(totalhours=0., 
                                             estimatedhours=0.,)
            
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute("select id from ticket where milestone=%s",
                               (milestone.name,))
                tickets = [i[0] for i in cursor.fetchall()]

                if tickets:
                    hours[milestone.name]['date'] = \
                        Ticket(self.env, tickets[0]).time_created
                for ticket in tickets:
                    ticket = Ticket(self.env, ticket)

                    # estimated hours for the ticket
                    try:
                        estimated_hours = float(ticket['estimatedhours'])
                    except (ValueError, TypeError):
                        estimated_hours = 0.
                    hours[milestone.name]['estimatedhours'] += estimated_hours

                    # total hours for the ticket (seconds -> hours)
                    total_hours = trac_hours.get_total_hours(ticket.id) / 3600.0
                    hours[milestone.name]['totalhours'] += total_hours
                
                    # update date for oldest ticket
                    if ticket.time_created < hours[milestone.name]['date']:
                        hours[milestone.name]['date'] = ticket.time_created

            b = StreamBuffer()
            stream |= Transformer(find_xpath).copy(b).end().select(xpath). \
                append(self.MilestoneMarkup(b, hours, req.href, this_milestone))

        return stream

    class MilestoneMarkup(object):
        """Iterator for Transformer markup injection"""
        def __init__(self, buffer, hours, href, this_milestone):
            self.buffer = buffer
            self.hours = hours
            self.href = href
            self.this_milestone = this_milestone
            
        def __iter__(self):
            if self.this_milestone is not None:  # for /milestone/xxx
                milestone = self.this_milestone
            else:
                milestone = self.buffer.events[3][1]
            if not milestone in self.hours.keys(): 
                return iter([]) 
            hours = self.hours[milestone]
            estimated_hours = hours['estimatedhours']
            total_hours = hours['totalhours']
            if not (estimated_hours or total_hours):
                return iter([])
            items = []
            if estimated_hours:
                items.append(tag.dt("Estimated Hours:"))
                items.append(tag.dd(str(estimated_hours)))
            date = hours['date']
            link = self.href("hours", milestone=milestone, 
                             from_year=date.year,
                             from_month=date.month,
                             from_day=date.day)
            items.append(tag.dt(tag.a("Total Hours:", href=link)))
            items.append(tag.dd(tag.a(hours_format % total_hours, href=link)))
            return iter(tag.dl(*items))


class TracHoursSidebarProvider(Component):

    implements(ITicketSidebarProvider, IRequireComponents)

    ### IRequireComponents methods

    def requires(self):
        return [TracHoursPlugin, TicketSidebarProvider]

    ### ITicketSidebarProvider methods

    def enabled(self, req, ticket):
        if ticket.id and req.authname and 'TICKET_ADD_HOURS' in req.perm:
            return True
        return False

    def content(self, req, ticket):
        data = {'worker': req.authname,
                'action': req.href('hours', ticket.id)}
        return Chrome(self.env). \
            load_template('hours_sidebar.html').generate(**data)

    ### ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


class TracUserHours(Component):

    implements(IRequireComponents, ITemplateProvider, IRequestHandler)

    ### IRequireComponents methods

    def requires(self):
        return [TracHoursPlugin]

    ### ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    ### IRequestHandler methods

    def match_request(self, req):req.perm.require('TICKET_VIEW_HOURS')
        """Return whether the handler wants to process the given request."""
        return req.path_info == '/hours/user' or \
               req.path_info.startswith('/hours/user/')

    def process_request(self, req):
        req.perm.require('TICKET_VIEW_HOURS')
        if req.path_info.rstrip('/') == '/hours/user':
            return self.users(req)
        user = req.path_info.split('/hours/user/', 1)[-1]

        add_stylesheet(req, 'common/css/report.css')
        add_link(req, 'alternate', req.href(req.path_info, format='csv'),
                 'CSV', 'text/csv', 'csv')
        
        return self.user(req, user)

    ### Internal methods

    def date_data(self, req, data):
        """data for the date"""
        now = datetime.datetime.now()
        data['days'] = range(1, 32)
        data['months'] = list(enumerate(calendar.month_name))
        data['years'] = range(now.year, now.year - 10, -1)
        if 'from_year' in req.args:
            from_date = get_date(req.args['from_year'], 
                                 req.args.get('from_month'),
                                 req.args.get('from_day'))

        else:
            from_date = datetime.datetime(now.year, now.month, now.day)
            from_date = from_date - datetime.timedelta(days=7)
        if 'to_year' in req.args:
            to_date = get_date(req.args['to_year'], 
                               req.args.get('to_month'),
                               req.args.get('to_day'),
                               end_of_day=True)
        else:
            to_date = now
        
        data['from_date'] = from_date
        data['to_date'] = to_date
        data['prev_week'] = from_date - datetime.timedelta(days=7)
        args = dict(req.args)
        args['from_year'] = data['prev_week'].year
        args['from_month'] = data['prev_week'].month
        args['from_day'] = data['prev_week'].day
        args['to_year'] = from_date.year
        args['to_month'] = from_date.month
        args['to_day'] = from_date.day

        data['prev_url'] = req.href('/hours/user', **args)

    def users(self, req):
        """hours for all users"""

        data = {'hours_format':  hours_format}

        ### date data
        self.date_data(req, data)

        ### milestone data
        milestone = req.args.get('milestone')
        milestones = Milestone.select(self.env)
        data['milestones'] = milestones

        ### get the hours
        #trachours = TracHoursPlugin(self.env)
        #tickets = trachours.tickets_with_hours()
        hours = get_all_dict(self.env, """
            SELECT * FROM ticket_time
            WHERE time_started >= %s AND time_started < %s
            """, *[int(time.mktime(i.timetuple()))
                   for i in (data['from_date'], data['to_date'])])
        worker_hours = {}
        for entry in hours:
            worker = entry['worker']
            if worker not in worker_hours:
                worker_hours[worker] = 0

            if milestone and milestone != \
                    Ticket(self.env, entry['ticket']).values.get('milestone'):
                continue

            worker_hours[worker] += entry['seconds_worked']

        worker_hours = [(worker, seconds/3600.)
                        for worker, seconds in 
                        sorted(worker_hours.items())]
        data['worker_hours'] = worker_hours

        if req.args.get('format') == 'csv':
            req.send(self.export_csv(req, data))

        #add_link(req, 'prev', self.get_href(query, args, context.href),
        #         _('Prev Week'))
        #add_link(req, 'next', self.get_href(query, args, context.href),
        #         _('Next Week'))
        #prevnext_nav(req, _('Prev Week'), _('Next Week'))

        return 'hours_users.html', data, "text/html"

    def user(self, req, user):
        """hours page for a single user"""
        data = {'hours_format':  hours_format,
                'worker': user}
        self.date_data(req, data)
        args = [user]
        args += [int(time.mktime(i.timetuple()))
                 for i in (data['from_date'], data['to_date'])]
        hours = get_all_dict(self.env, """
            SELECT * FROM ticket_time
            WHERE worker=%s AND time_started >= %s AND time_started < %s
            """, *args)
        worker_hours = {}
        for entry in hours:
            ticket = entry['ticket']
            if ticket not in worker_hours:
                worker_hours[ticket] = 0
            worker_hours[ticket] += entry['seconds_worked']
        
        data['tickets'] = dict([(i, Ticket(self.env, i))
                                for i in worker_hours.keys()])

        # sort by ticket number and convert to hours
        worker_hours = [(ticket_id, seconds/3600.)
                        for ticket_id, seconds in
                        sorted(worker_hours.items())]

        data['worker_hours'] = worker_hours
        data['total_hours'] = sum([hours[1] for hours in worker_hours])

        if req.args.get('format') == 'csv':
            buffer = StringIO()
            writer = csv.writer(buffer)
            format = '%B %d, %Y'
            title = "Hours for %s" % user
            writer.writerow([title, req.abs_href()])
            writer.writerow([])
            writer.writerow(['From', 'To'])
            writer.writerow([data[i].strftime(format) 
                             for i in 'from_date', 'to_date'])
            writer.writerow([])
            writer.writerow(['Ticket', 'Hours'])
            for ticket, hours in worker_hours:
                writer.writerow([ticket, hours])
            
            req.send(buffer.getvalue(), 'text/csv')

        return 'hours_user.html', data, 'text/html'

    def export_csv(self, req, data, sep=',', mimetype='text/csv'):
        content = StringIO()
        content.write('\xef\xbb\xbf')  # BOM
        writer = csv.writer(content, delimiter=sep, quoting=csv.QUOTE_MINIMAL)

        title = "Hours for %s" % self.env.project_name
        writer.writerow([title, req.abs_href()])
        writer.writerow([])
        writer.writerow(['From', 'To'])
        writer.writerow([data[i].strftime('%B %d, %Y')
                         for i in 'from_date', 'to_date'])
        if data['milestone']:
            writer.writerow(['Milestone', data['milestone']])
        writer.writerow([])
        writer.writerow(['Worker', 'Hours'])
        for worker, hours in data['worker_hours']:
            writer.writerow([worker, hours])

        return content.getvalue(), '%s;text/csv' % mimetype
