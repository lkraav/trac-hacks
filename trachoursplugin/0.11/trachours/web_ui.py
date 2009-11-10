"""
web handlers for TracHours
"""

import calendar
import datetime
import time

from api import hours_format # local import
from componentdependencies.interface import IRequireComponents
from genshi.builder import tag
from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from hours import TracHoursPlugin
from ticketsidebarprovider.interface import ITicketSidebarProvider
from ticketsidebarprovider.ticketsidebar import TicketSidebarProvider
from trac.core import *
from trac.ticket import Ticket
from trac.web.api import IRequestHandler
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_stylesheet
from trac.web.chrome import Chrome
from trac.web.chrome import ITemplateProvider
from tracsqlhelper import get_all_dict, get_column
from utils import get_date

class TracHoursRoadmapFilter(Component):
    
    implements(ITemplateStreamFilter, IRequireComponents)

    ### method for IRequireComponents
    def requires(self):
        return [TracHoursPlugin]

    ### method for ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        """
        filter the stream for the roadmap (/roadmap)
        and milestones /milestone/<milestone>
        """

        if filename in ('roadmap.html', 'milestone_view.html'):
            trachours = TracHoursPlugin(self.env)

            hours = {}

            milestones = data.get('milestones')
            this_milestone = None

            if milestones is None:
                # /milestone view : only one milestone
                milestones = [ data['milestone'] ]
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
                cursor.execute("select id from ticket where milestone='%s'" % milestone.name)
                tickets = [i[0] for i in cursor.fetchall()]

                if tickets:
                    hours[milestone.name]['date'] = Ticket(self.env, tickets[0]).time_created
                for ticket in tickets:
                    ticket = Ticket(self.env, ticket)

                    # estimated hours for the ticket
                    try:
                        estimatedhours = float(ticket['estimatedhours'])
                    except (ValueError, TypeError):
                        estimatedhours = 0.
                    hours[milestone.name]['estimatedhours'] += estimatedhours

                    # total hours for the ticket
                    totalhours = trachours.get_total_hours(ticket.id)
                    hours[milestone.name]['totalhours'] += totalhours
                
                    # update date for oldest ticket
                    if ticket.time_created < hours[milestone.name]['date']:
                        hours[milestone.name]['date'] = ticket.time_created
                    # seconds -> hours
                    hours[milestone.name]['totalhours'] /= 3600.


                b = StreamBuffer()
                stream |= Transformer(find_xpath).copy(b).end().select(xpath).append(self.MilestoneMarkup(b, hours, req.href, this_milestone))

        return stream

    class MilestoneMarkup(object):
        """iterator for Transformer markup injection"""
        def __init__(self, buffer, hours, href, this_milestone):
            self.buffer = buffer
            self.hours = hours
            self.href = href
            self.this_milestone = this_milestone
            
        def __iter__(self):
            if self.this_milestone is not None: # for /milestone/xxx
                milestone = self.this_milestone
            else:
                milestone = self.buffer.events[3][1]
            hours = self.hours[milestone]
            estimatedhours = hours['estimatedhours']
            totalhours = hours['totalhours']
            if not (estimatedhours or totalhours):
                return iter([])
            items = []
            if estimatedhours:
                items.append(tag.dt("Estimated Hours:"))
                items.append(tag.dd(str(estimatedhours)))
            date = hours['date']
            link = self.href("hours", milestone=milestone, 
                             from_year=date.year,
                             from_month=date.month,
                             from_day=date.day)
            items.append(tag.dt(tag.a("Total Hours:", href=link)))
            items.append(tag.dd(tag.a(hours_format % totalhours, href=link)))
            return iter(tag.dl(*items))



class TracHoursSidebarProvider(Component):

    implements(ITicketSidebarProvider, IRequireComponents)

    ### method for IRequireComponents
    def requires(self):
        return [TracHoursPlugin, TicketSidebarProvider]


    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        if ticket.id and req.authname and 'TICKET_ADD_HOURS' in req.perm:
            return True
        return False

    def content(self, req, ticket):
        data = { 'worker': req.authname,
                 'action': req.href('hours', ticket.id) }
        return Chrome(self.env).load_template('hours_sidebar.html').generate(**data)


    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


class TracUserHours(Component):
    
    implements(IRequireComponents, ITemplateProvider, IRequestHandler)

    ### method for IRequireComponents
    def requires(self):
        return [TracHoursPlugin]


    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return req.path_info.rstrip('/') == '/hours/user'

    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """
        trachours = TracHoursPlugin(self.env)
        now = datetime.datetime.now()
        data = {}
        add_stylesheet(req, 'common/css/report.css')

        # data for the date
        data['days'] = range(1, 32)
        data['months'] = [ (i, calendar.month_name[i]) for i in range(1,13) ]        
        data['years'] = range(now.year, now.year - 10, -1)
        if 'from_year' in req.args:
            from_date = get_date(req.args['from_year'], 
                                 req.args.get('from_month'),
                                 req.args.get('from_day'))

        else:
            from_date = datetime.datetime(now.year, now.month, now.day)
            from_date = from_date - datetime.timedelta(days=7) # 1 week ago, by default
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

        ### get the hours
        tickets = trachours.tickets_with_hours()
        hours = get_all_dict(self.env, 
                             "SELECT * FROM ticket_time WHERE time_started >= %s AND time_started < %s",
                             *[int(time.mktime(i.timetuple()))
                               for i in (from_date, to_date)])
        worker_hours = {}
        for entry in hours:
            worker = entry['worker']
            if  worker not in worker_hours:
                worker_hours[worker] = 0
            worker_hours[worker] += entry['seconds_worked']

        worker_hours = [(worker, seconds/3600.)
                        for worker, seconds in 
                        sorted(worker_hours.items())]
        data['worker_hours'] = worker_hours
        data['hours_format'] = hours_format

        return 'hours_users.html', data, "text/html"
