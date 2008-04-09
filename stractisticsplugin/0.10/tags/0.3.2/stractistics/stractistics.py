# -*- coding: utf-8 -*-
#
# Stractistics
# Copyright (C) 2008 GMV SGI Team <http://www.gmv-sgi.es>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public
# License as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# $Id: stractistics.py 383 2008-04-09 11:02:15Z mjrs $
#

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
        add_stylesheet, add_script
from trac.config import Option
from trac.web.api import IRequestHandler
from trac.util import escape
from trac.util.html import html, Markup
from trac.perm import IPermissionRequestor
import OpenFlashChart


class StractisticsModule(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
                IPermissionRequestor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'stractistics'

    def get_navigation_items(self, req):
        if req.perm.has_permission('STRACTISTICS_VIEW'):
            yield 'mainnav', 'stractistics', html.A("Stractistics", href=req.href.stractistics())
        
    #IPermissionRequestor methods
    def get_permission_actions(self):
        return ['STRACTISTICS_VIEW']
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return a list of directories containing the provided ClearSilver
        templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]


    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/stractistics'

    def process_request(self, req):
        req.perm.assert_permission('STRACTISTICS_VIEW')
        add_stylesheet(req, 'hw/css/stractistics.css')
        
        self._read_config_options()
        self.start_date, self.end_date, self.weeks_back = self._parse_time_gap(req)
                                           
        #First , repository activity 
        query_response = self._repository_activity(req.args)
        req.hdf = query_response.dump_info_to_hdf(req.hdf)
        
        #Second, ticket activity.
        ticket_activity_query_response = self._ticket_activity(req.args)
        req.hdf = ticket_activity_query_response.dump_info_to_hdf(req.hdf)
                
        #Third, wiki activity.
        wiki_activity_query_response = self._wiki_activity()
        req.hdf = wiki_activity_query_response.dump_info_to_hdf(req.hdf)
        
        self.env.log.debug("hdf : %s" % req.hdf)
        return 'stractistics.cs', None
    
    
    def _read_config_options(self):
        """
        Reads available configurations options from trac.ini 
        """
        self.repository_authors_limit = self.env.config.getint('stractistics', 'repository_authors_limit', 5)
        self.repository_ignored_authors = [str(elem) for elem in self.env.config.getlist(\
                                                'stractistics',
                                                'ignored_repository_authors',
                                                default=[])]
        
        self.wiki_authors_limit = self.env.config.getint('stractistics', 'wiki_authors_limit', 5)
        self.wiki_ignored_authors = [str(elem) for elem in self.env.config.getlist(\
                                                'stractistics',
                                                'ignored_wiki_authors',
                                                default=[])]
        
        self.max_author_characters = self.env.config.getint('stractistics', 'max_author_characters', None)
        
    
    def _parse_time_gap(self, req):
        """
        Parse 'end_date' and 'weeks_back' from url.
        In case of error, end_date defaults to current date
         and weeks_back defaults to 12.
        """
        
        weeks_back = 12
        if req.args.has_key('weeks_back'):
            try:
                tmp = int(req.args['weeks_back'])
                if tmp > 0:
                    weeks_back = tmp
            except ValueError:
                pass
        req.hdf['timeframe.weeks_back'] = weeks_back
        
        import datetime
        end_date = datetime.datetime.today()
        date_format = "%m/%d/%y"
        if req.args.has_key('end_date'):
            aux = req.args['end_date']
            try:
                aux = datetime.datetime.strptime(aux, date_format)
                end_date = aux
            except Exception:
                end_date = datetime.datetime.today()
        req.hdf['timeframe.end_date'] = datetime.datetime.strftime(end_date, date_format)
        start_date = end_date - datetime.timedelta(days = weeks_back * 7)
        return start_date, end_date, weeks_back
    
    def _quote_authors(self, ignored_authors):
        def quote(author):
            return "'%s'" % author
        return ", ".join([quote(author) for author in ignored_authors])
        
    
    def _repository_activity(self, args):
        """
        Displays commits per week of the AUTHORS_LIMIT most active authors in the last WEEKS_NUMBER weeks.
        """
        WEEKS_NUMBER = self.weeks_back
        AUTHORS_LIMIT = self.repository_authors_limit
        ignored_authors = self._quote_authors(self.repository_ignored_authors)
        
        end_date = self.end_date
        start_date = self.start_date
        
        #We retrieve the most active authors during the time frame
        authors = self._most_active_repository_authors( AUTHORS_LIMIT, ignored_authors, start_date, end_date)
        #Now we retrieve all the revisions commited in the time frame
        revisions = self._retrieve_revisions(authors, start_date, end_date)        
        #Last, for every author we determine how many commits per week he's done. 
        weeks_list, authors_data = self._authors_commit_data(authors, revisions, start_date, end_date)
        
        #We must build a QueryResponse from weeks_labels, and authors_data
        query_response = QueryResponse("repository_activity")
        query_response.set_title("Commits per week (%s weeks)" % WEEKS_NUMBER)
        
        columns, rows = self._adapt_to_table(weeks_list, authors_data)
        query_response.set_columns(columns)
        query_response.set_results(rows)   
        
        chart = query_response.chart_info
        chart.type = 'Line'
        chart.x_legend = 'Weeks'
        chart.y_legend = 'Commits'
        chart.x_labels = weeks_list
        chart.data = self._restructure_data(authors_data) 
        chart.set_tool_tip("#key#<br>week:#x_label#<br>commits:#val#")
             
        return query_response
        
    def _most_active_repository_authors(self, AUTHORS_LIMIT, ignored_authors, start_date, end_date):
        """
        Retrieves the AUTHORS_LIMIT  most active repository authors between stard_date and end_date.
        Returns a list with their names.
        """
        
        authors = []
        sql_statement = """
        SELECT r.author AS author, COUNT( r.author ) AS commits 
         FROM revision r 
         WHERE r.time > %s AND r.time < %s AND r.author NOT IN (%s)
         GROUP BY r.author 
         ORDER BY commits DESC 
         LIMIT %s
        """
        
        sql_statement = sql_statement % ( self._datetime_to_secs(start_date),
                                          self._datetime_to_secs(end_date),
                                          ignored_authors,
                                          AUTHORS_LIMIT)
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()        
        cursor.execute(sql_statement)
        #Only interested in the name 
        authors = [row[0] for row in cursor] 
        return authors 
    
    
    def _retrieve_revisions(self, authors, start_date, end_date):
        """
        Retrieves every revision commited by any author in authors between start_date and end_date
        Returs a list of author and date pairs.
        """
        revisions = []
        sql_statement = """
        SELECT r.author AS author, r.time AS date 
        FROM revision r 
        WHERE r.time > %s AND r.time < %s AND r.author IN %s 
        """   
        def valuesList(authors): 
            return "( %s )" % ','.join( map(lambda x:"'%s'" % x,authors) )
        sql_params = {'start_date':self._datetime_to_secs(start_date),
                      'end_date':self._datetime_to_secs(end_date),
                      'authors':valuesList(authors)}
        
        sql_statement = sql_statement % (self._datetime_to_secs(start_date),
                                         self._datetime_to_secs(end_date),
                                         valuesList(authors))
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(sql_statement)

        import datetime
        revisions = [[row[0],datetime.datetime.fromtimestamp(row[1])] for row in cursor]
        return revisions
        
    def _authors_commit_data(self, authors, revisions, start_date, end_date):
        """
        First, we obtain the list of weeks between start_date and end_date.
        Then for each author we compute how many commits he's done each week.
        """
        weeks = self._weeks_elapsed(start_date,end_date)
        authors_data = {}
        for aut in authors:
            authors_data[aut] = weeks.copy()
        for rev in revisions:
            author = rev[0]
            week = self._week_format(rev[1])
            authors_data[author][week] = authors_data[author][week] + 1
        
        weeks_labels = [k for k in weeks.iterkeys()]
        weeks_labels.sort()
        weeks_labels = [self._rearrangeWeekYear(x) for x in weeks_labels]
        
        aux_dic = {}
        for author in authors_data.iterkeys():
            aux_dic[author] = self._values_sorted_by_key(authors_data[author])
        authors_data = aux_dic
        
        return (weeks_labels, authors_data)
     
    def _ticket_activity(self,args):
        """
        Shows ticket activity in the last NUM_DAYS days, only those tickets 
        created or modified during that time frame are considered. 
        """
        NUM_DAYS = 30
        
        sql_statement = """
        SELECT t.status AS status, COUNT(DISTINCT t.id) AS tickets
        FROM ticket t 
        WHERE t.changetime > %s
        GROUP BY t.status;
        """
        
        import datetime, calendar
        start_date = self.end_date - datetime.timedelta(days = NUM_DAYS)
        start_date = calendar.timegm(start_date.timetuple())
        
        sql_statement = sql_statement % start_date
        self.env.log.debug("ticket_activity sql : %s" % sql_statement)
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(sql_statement)
       
        results = list(cursor)

        query_response = QueryResponse("ticket_activity")
        query_response.set_title("Ticket activity (%s days until %s)" % (NUM_DAYS, self.end_date.date()))
        query_response.set_columns(('ticket status','tickets'))
        query_response.set_results(results)
        chart = query_response.chart_info
        chart.type = "Pie"
        chart.set_width(480)
        chart.set_height(300)
        chart.set_tool_tip("status:#x_label#<br>tickets:#val#")
        chart.set_line_color("#000000")
        chart.x_labels = [row[0] for row in results]
        chart.data = [row[1] for row in results]
        
        return query_response
    
    def _wiki_activity(self):
        """
        Displays wiki editions per week of each of the AUTHORS_LIMIT most 
        active authors in the last WEEKS_NUMBER weeks.
        """
        WEEKS_NUMBER = self.weeks_back
        AUTHORS_LIMIT = self.wiki_authors_limit
        ignored_authors = self._quote_authors(self.wiki_ignored_authors)
        
        import datetime
        end_date = self.end_date
        start_date = self.start_date
        
        authors_list = self._retrieve_most_active_wiki_authors(AUTHORS_LIMIT,\
                                                                ignored_authors,
                                                                start_date,
                                                                end_date)
        
        wiki_pages_list = self._retrieve_wiki_pages(start_date, end_date)        
        
        weeks_list, authors_data = self._wiki_authors_data(authors_list, 
                                                           wiki_pages_list, 
                                                           start_date, 
                                                           end_date)
        
        
        query_response = QueryResponse("wiki_activity")
        query_response.set_title("Wiki activity (%s weeks)" % WEEKS_NUMBER)
        
        columns, rows = self._adapt_to_table(weeks_list, authors_data)
        query_response.set_columns(columns)
        query_response.set_results(rows)
        
        chart = query_response.chart_info
        chart.type = 'Line'
        chart.x_labels = weeks_list
        chart.x_legend = 'Weeks'
        chart.y_legend = 'Wiki modifications'
        chart.data = self._restructure_data(authors_data)
        chart.set_tool_tip("#key#<br>week:#x_label#<br>wiki modifications:#val#")
        
        return query_response
    
    
    def _wiki_authors_data(self, authors_list, wiki_pages_list, start_date, end_date):
        weeks_dic = {}
        weeks_dic = self._weeks_elapsed(start_date, end_date)
        
        authors_data = {}
        for author in authors_list:
            authors_data[author] = weeks_dic.copy()
        
        for page in wiki_pages_list:
            week = self._week_format(page[1])
            author = page[0]
            if author in authors_list:
                authors_data[author][week] = authors_data[author][week ] + 1
        
        #Sorting time!
        weeks_list = [key for key in weeks_dic.iterkeys()]
        weeks_list.sort()
        weeks_list = [self._rearrangeWeekYear(week) for week in weeks_list]
        
        data_aux = {}
        for author in authors_data:
            data_aux[author] = self._values_sorted_by_key(authors_data[author])
        authors_data = data_aux
        return (weeks_list, authors_data)
                
        
    def _retrieve_most_active_wiki_authors(self, AUTHORS_LIMIT, ignored_authors, start_date, end_date):
        """
        Retrieves the AUTHORS_LIMIT most active wiki authors between start_date and end_date
        """
        sql_statement = """
        SELECT w.author AS author, COUNT(distinct w.version) AS modifications 
        FROM wiki w
        WHERE w.time > %s AND w.time < %s AND w.author NOT IN (%s)
        GROUP BY author
        ORDER BY modifications DESC
        LIMIT %s  
        """
        import datetime
        sql_statement = sql_statement % (self._datetime_to_secs(start_date),
                                         self._datetime_to_secs(end_date),
                                         ignored_authors,
                                         AUTHORS_LIMIT)
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(sql_statement)
        
        authors_list = [row[0] for row in cursor]
        return authors_list
    
    def _retrieve_wiki_pages(self, start_date, end_date):
        sql_statement = """
        SELECT w.author AS author, w.time  AS time
        FROM wiki w
        WHERE time > %s AND time < %s
        """
        sql_statement = sql_statement % (self._datetime_to_secs(start_date),
                                         self._datetime_to_secs(end_date))
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(sql_statement)
        
        import datetime
        wiki_pages_list = [[row[0],datetime.datetime.fromtimestamp(row[1])] for row in cursor]
        return wiki_pages_list
    
    
    
    def _datetime_to_secs(self,datetime_date):
            """ 
            From datetime to seconds since epoch. 
            """
            import calendar 
            return calendar.timegm(datetime_date.timetuple())
    
    def _weeks_elapsed(self, start_date, end_date):
        """
        Returns a dic whose keys are all the weeks between start_date and end_date.
        """
        import datetime
        #Sometimes the 53th week of the year is just one day long. If we skip that week but data has been generated in 
        #that week, the plugin will crash because of a KeyError.
        diff = datetime.timedelta(days=1)
        weeks = {}
        myDate = start_date
        while myDate < end_date:
            weeks[self._week_format(myDate)] = 0
            myDate = myDate + diff
        weeks[self._week_format(end_date)] = 0
        return weeks
        
    def _week_format(self, datetime):
        """
        Picks a datetime and formats it into a "Year/Week" string.
        """
        format = "%y/%W"
        return datetime.strftime(format)
    
    def _values_sorted_by_key(self, dic):
        """
        Returns a list of the values in dic sorted by key.
        """
        keys = dic.keys()
        keys.sort()
        return map(dic.get, keys)
    
    def _rearrangeWeekYear(self, x):
        """
        From "Year-Week" to "Week-Year".It just swaps places.
        "Year-Week" format is much easier to sort but for displaying purposes, "Week/Year" is preferable.
        """
        aux = x.split('/')
        return "%s/%s" % (aux[1], aux[0])
    
    
    def _restructure_data(self, authors_data):
        """
        We need this function to avoid employing names with dots as HDF nodes.
        """
        new_data = []
        for author in authors_data.keys():
            dic = {}
            dic['author'] = author
            dic['info'] = authors_data[author]
            new_data.append(dic)
        return new_data
        
    
    def _adapt_to_table(self, weeks_list, authors_data):
        """
        This function rearranges our data in order to be displayed easier 
        in the html table.
        """
        
        #First, we reverse the order of the weeks.
        reversed_weeks_list = list(weeks_list)
        reversed_weeks_list.reverse()
        
        """Now, we must reverse the order of the results to match the new 
        order of weeks.""" 
        results = {}
        for author in authors_data.iterkeys():
            results[author] = list(authors_data[author])
            results[author].reverse()
        
        """
        Every row in rows is a 2-tuple, the first element of the tuple is the week 
        and the second element of the
        tuple is an array of the wiki modifications per author for that week.
        """
        authors = results.keys()
        rows = []
        index = 0
        for week in reversed_weeks_list:
            week_N_values = []
            for author in authors:
                week_N_values.append(results[author][index])
            index += 1
            rows.append((week, week_N_values))
        
        #Name mangling goes here
        def mangle_name(name, characters_cap):
            if characters_cap is not None:
                name = name[0:characters_cap]
            return name
        columns = [mangle_name(name,self.max_author_characters) for name in authors]
        return (columns, rows)
        
    
class QueryResponse:
    """
    Encapsulates the information retrieved by a query and additional data for correct display.
    """
    def __init__(self,name):
        self.title = None
        self.name = name
        self.columns = []
        self.results = []
        self.chart_info = ChartInfo(name)
        
    def set_name(self,name):
        self.name = name
        self.chart_info.name = "%s_chart" % self.name
    
    def set_title(self, title):
        self.title = title
        self.chart_info.title = title
        
    def set_columns(self, columns):
        self.columns = columns
        
    def set_results(self, results):
        self.results = results
        size = len( results )
        self.chart_info.data_size = size
    
    def dump_info_to_hdf(self, hdf):
        info = {
                'title':self.title,
                'columns':self.columns,
                'results':self.results,
                'chart_info': self.chart_info.get_data_members()
                }
        hdf.set_unescaped(self.name, info)        
        return hdf
    
        
class ChartInfo:
    """
    This data is meant to be fed to SWF objects.
    It lets us control chart presentation.
    """
    def __init__(self,name=''):
        #Default values
        self.width = 480
        self.height = 300
        self.x_font_size = 10
        self.x_font_color = "#000000"
        self.y_max = 0
        self.y_steps = 8
        self.data_size = 0
        self.x_orientation = 2
        self.x_steps = 1
        self.bg_color = '#FFFFFF'
        self.x_axis_color = '#000000'
        self.y_axis_color = '#000000'
        self.x_grid_color = '#F2F2EA'
        self.y_grid_color = '#F2F2EA'
        self.tool_tip = '#key#<br>#x_label#<br>#val#'
        self.type = "Bar"
        self.x_labels = None
        self.data = None
        self.colors = ["#f79910","#cbcc99","#6498c1","#cb1009","#64b832","#FF69B4","#000000","#8470FF"]
        self.title = ''
        self.name = "%s_chart" % name
        chartObject = OpenFlashChart.graph_object()
        self.embed_info = chartObject.render(self.width, self.height,'','chrome/hw/swf/',ofc_id = self.name) 
        
    
    #Only useful if you wish a custom tool_tip. 
    def set_tool_tip(self, tool_tip):
        self.tool_tip = tool_tip
    
    #Only useful for pie charts
    def set_line_color(self, color):
        self.line_color = color
               
    def set_width(self, width):
        self.width = width 
        chartObject = OpenFlashChart.graph_object()
        self.embed_info = chartObject.render(self.width, self.height,'','chrome/hw/swf/',ofc_id = self.name)
        
    def set_height(self, height):
        self.height = height
        chartObject = OpenFlashChart.graph_object()
        self.embed_info = chartObject.render(self.width, self.height,'','chrome/hw/swf/',ofc_id = self.name)
        
    def get_data_members(self):
        members_dic = {}
        for member in dir(self):
            if not callable(getattr(self,member)):
                members_dic[member] = getattr(self, member)
        return members_dic
            