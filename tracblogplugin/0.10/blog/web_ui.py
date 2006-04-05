# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 John Hampton <pacopablo@asylumware.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at:
# http://trac-hacks.org/wiki/TracBlogPlugin
#
# Author: John Hampton <pacopablo@asylumware.com>

import time
import datetime
import inspect
import calendar
from pkg_resources import resource_filename
from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.web.chrome import INavigationContributor 
from trac.util import Markup, format_date, format_datetime
from trac.wiki.formatter import wiki_to_html, wiki_to_oneliner
from trac.wiki.model import WikiPage
from trac.wiki.api import IWikiMacroProvider
from tractags.api import TagEngine
from tractags.parseargs import parseargs

__all__ = ['TracBlogPlugin']

class TracBlogPlugin(Component):
    """Displays a blog based on tags
    
    The list of tags to be shown can be specified as arguments to the macro.
    An options keyword argument of union can be secified.  If specified, then
    the resulting blog will be a {{{union}}} of pages with the specified tags.
    If the {{{union}}} parameter is omitted, then an intersection of the
    specified tags is returned.

    If no tags are specified as parameters, then the default 'blog' tag is
    used.

    === Examples ===
    {{{
    [[BlogShow()]]
    [[BlogShow(blog,pacopablo)]]
    [[BlogShow(blog,pacopablo,union=True)]]
    }}}
    """

    implements(IRequestHandler, ITemplateProvider, INavigationContributor,
               IWikiMacroProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'blog'
                
    def get_navigation_items(self, req):
        req.hdf['trac.href.blog'] = self.env.href.blog()
        yield 'mainnav', 'blog', Markup('<a href="%s">Blog</a>',
                                         self.env.href.blog())

    # IWikiMacroProvider
    def get_macros(self):
        yield "BlogShow"

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, content):
        """ Display the blog in the wiki page """
        add_stylesheet(req, 'blog/css/blog.css')
        tags, kwargs = self._split_macro_args(content)
        if not tags:
            tstr = self.env.config.get('blog', 'default_tag', 'blog')
            tags = [t.strip() for t in tstr.split(',') if t]
        self._generate_blog(req, *tags, **kwargs)
        req.hdf['blog.macro'] = True
        return req.hdf.render('blog.cs')

    def _split_macro_args(self, argv):
        """Return a list of arguments and a dictionary of keyword arguements

        """
        args = []
        kwargs = {}
        if argv:
            args, kwargs = parseargs(argv)
        return args, kwargs

    def match_request(self, req):
        return req.path_info == '/blog'

    def process_request(self, req):
        add_stylesheet(req, 'blog/css/blog.css')
        add_stylesheet(req, 'common/css/wiki.css')
        tags = req.args.getlist('tag')
        kwargs = {}
        #for key,value in req.args.items():
        for key in req.args.keys():
            if key != 'tag':
                #kwargs[key] = value
                kwargs[key] = req.args[key]
            continue
        if not tags:
            tstr = self.env.config.get('blog', 'default_tag', 'blog')
            tags = [t.strip() for t in tstr.split(',') if t]
        self._generate_blog(req, *tags, **kwargs)
        return 'blog.cs', None

    def _generate_blog(self, req, *args, **kwargs):
        """Extract the blog pages and fill the HDF.

        *args is a list of tags to use to limit the blog scope
        **kwargs are any aditional keyword arguments that are needed
        """
        tallies = {}
        tags = TagEngine(self.env).tagspace.wiki
        try:
            union = kwargs['union']
        except KeyError:
            union = False
        # Formatting
        read_post = "[wiki:%s Read Post]"
        entries = {}
        if not len(args):
            tlist = [self.env.config.get('blog', 'default_tag', 'blog')]
        else:
            tlist = args
        if union:
            blog = tags.get_tagged_names(tlist, operation='union')
        else:
            blog = tags.get_tagged_names(tlist, operation='intersection')

        poststart, postend = self._get_time_range(req, **kwargs)
        for blog_entry in blog:
            page = WikiPage(self.env, version=1, name=blog_entry)
            version, post_time, author, comment, ipnr = page.get_history(
                                                        ).next()
            self._add_to_tallies(tallies, post_time, blog_entry)
            page = WikiPage(self.env, name=blog_entry)
            version, modified, author, comment, ipnr = page.get_history(
                                                       ).next()
            if poststart >= post_time >= postend:       
                time_format = self.env.config.get('blog', 'date_format') \
                              or '%x %X'
                timeStr = format_datetime(post_time, format=time_format) 
                text = self._trim_page(page.text, blog_entry)
                data = {
                        'wiki_link' : wiki_to_oneliner(read_post % 
                                                       blog_entry,
                                                       self.env),
                        'time'      : timeStr,
                        'author'    : author,
                        'wiki_text' : wiki_to_html(text, self.env, req),
                        'comment'   : wiki_to_oneliner(comment, self.env),
                       }
                if modified != post_time:
                    data['modified'] = 1
                    mod_str = format_datetime(post_time, format=time_format)
                    data['mod_time'] = mod_str
                entries[post_time] = data
            continue
        tlist = entries.keys()
        # Python 2.4ism
        # tlist.sort(reverse=True)
        tlist.sort()
        tlist.reverse()
        req.hdf['blog.entries'] = [entries[x] for x in tlist]
        bloglink = self.env.config.get('blog', 'new_blog_link', 'New Blog Post')
        req.hdf['blog.newblog'] = bloglink
        self._generate_calendar(req)
        pass

    def _generate_calendar(self, req):
        """Generate data necessary for the calendar

        """
        now = datetime.datetime.now()
        year = self._choose_value('year', req, None, convert=int) or \
               now.year
        month = self._choose_value('month', req, None, convert=int) or \
                now.month
        day = self._choose_value('day', req, None, convert=int) or \
              now.day 
        baseday = datetime.datetime(year, month, day)
        cal = calendar.monthcalendar(year, month)
        week = [week for week in xrange(0,len(cal)-1) if day in cal[week]][0]
        monthname = format_datetime(time.mktime(now.timetuple()), format="%b") 
        lastyear = abs(year - 1)
        nextyear = year + 1
        # for the prev/next navigation links
        lastmonth = month - 1
        lastmonth_year = year
        nextmonth = month + 1
        nextmonth_year = year
        # check for year change (KISS version)
        if lastmonth <= 0:
            lastmonth = 12
            lastmonth_year -= 1
        if nextmonth >= 13:
            nextmonth = 1
            nextmonth_year += 1

        hdfdate = {
                    'year' : year,
                    'month' : month, 
                    'day' : day,
                    'lastyear' : lastyear,
                    'nextyear' : nextyear,
                    'lastmonth' : {
                                    'year' : lastmonth_year,
                                    'month' : lastmonth,
                                  },
                    'nextmonth' : {
                                    'year' : nextmonth_year,
                                    'month' : nextmonth,
                                  },
                    'daynames' : calendar.weekheader(1).split(),
                    'week' : week,
                    'monthname' : monthname,
                  }
        req.hdf['blog.date'] = hdfdate
        req.hdf['blog.cal'] = cal
        req.hdf['blog.path_info'] = req.href(req.path_info)
        pass

    def _add_to_tallies(self, tallies,  post_time, page_name):
        """Create a running tally of blog page data

        """
        d = datetime.datetime.fromtimestamp(post_time)
        try:
            tallies['total'] += 1
        except KeyError:
            tallies['total'] = 1
        try:
            tallies[d.year]['total'] += 1
            tallies[d.year]['pages'].append(page_name)
        except (KeyError, AttributeError):
            tallies[d.year] = {'total' : 1,
                               'pages' : [page_name]}
        try:
            tallies[d.year][d.month]['total'] += 1
            tallies[d.year][d.month]['pages'].append(page_name)
        except (KeyError, AttributeError):
            tallies[d.year][d.month] = {'total' : 1,
                                        'pages' : [page_name]}
        try:
            tallies[d.year][d.month][d.day]['total'] += 1
            tallies[d.year][d.month][d.day]['pages'].append(page_name)
        except (KeyError, AttributeError):
            tallies[d.year][d.month][d.day] = {'total' : 1,
                                               'pages' : [page_name]}
        pass

    def _get_time_range(self, req, **kwargs):
        """Return a start and end date range

        Parameters can be passed in via the req object or via **kwargs.  
        The req object always overrides **kwargs.  In practice, this shouldn't
        matter much as the macro will use **kwargs and the nav item will use
        req.  Just documenting behavior.

        The range of days can be specified in multiple ways.
        * Specify date range with startdate and enddate.  Value should be 
          seconds since epoch
        * Specify startdate and delta. delta should be a number of seconds. If
          both enddate and delta are specified, enddate is preferred.
        * Specify any combination of year, month, day.  If any one of the
          values is specified, then it will use this method in place of 
          startdate, enddate and delta.  If a value is missing that is required
          such as a year if month is specified, then it deafults to the current
          value.  Otherwise it generates a range according to the values passed
          in.  For example, year=2006 and month=12 will return all posts for 
          December 2006.

        """
        DAY = 86400
        HISTORY = int(self.env.config.get('blog', 'history_days') or 30) * DAY

        startdate = self._choose_value('startdate', req, kwargs, convert=int)
        enddate = self._choose_value('enddate', req, kwargs, convert=int)
        delta = self._choose_value('delta', req, kwargs, convert=int)
        year = self._choose_value('year', req, kwargs, convert=int)
        month = self._choose_value('month', req, kwargs, convert=int)
        day = self._choose_value('day', req, kwargs, convert=int)
        now = datetime.datetime.now()
        oneday = datetime.timedelta(days=1)
        if year or month or day:
            if day:
                year = year or now.year
                month = month or now.month
            if month:
                year = year or now.year
            days_in_month = calendar.monthrange(year, month or 12)[1]
            start = datetime.datetime(year, month or 12, 
                                      day or days_in_month)
            start += oneday
            end = datetime.datetime(year, month or 1, day or 1)
            start = time.mktime(start.timetuple())
            end = time.mktime(end.timetuple())
        else:
            start = startdate or time.mktime(now.timetuple())
            if enddate:
                end = enddate
            elif delta:
                end = start - delta
            else:
                end = start - HISTORY
        return start, end

    def _choose_value(self, key, req, kwargs, convert=None):
        """Return the value for the specified key from either req or kwargs

        If the value is present in both, then the value from req is used.
        If the value doesn't exist in either, then None is returned.

        An optional conversion function can be passed.  If present, the value
        will be passed to the conversion function before returning.  If the
        conversion function raises an error, None will be returned

        """
        val = req.args.get(key, None)
        if not val:
            try:
                val = kwargs[key]
            except:
                val = None
        if convert:
            try:
                val = convert(val)
            except:
                val = None
        return val

    def _trim_page(self, text, page_name):
        """Trim the page text to the {{{post_size}} in trac.ini

        The timming isn't exact.  It trims to the first line that causes the
        page to exceed the value storing in {{{post_size}}}.  If the line is
        in the middle of a code block, it will close the block.

        """
        post_size = int(self.env.config.get('blog', 'post_size', 1024))
        tlines = []
        entry_size = 0
        line_count = 0
        in_code_block = False
        lines = text.split('\n')
        for line in lines:
            line_count += 1
            entry_size += len(line)
            tlines.append(line)
            if not in_code_block:
                in_code_block = line.strip() == '{{{'
            else:
                in_code_block = in_code_block and line.strip() != '}}}'
            if entry_size > post_size:
                if in_code_block:
                    tlines.append('}}}')
                break
            continue
        if line_count < len(lines):
            tlines.append("''[wiki:%s (...)]''" % page_name)
            
        return '\n'.join(tlines)

    # ITemplateProvider
    def get_templates_dirs(self):
        """ Return the absolute path of the directory containing the provided
            templates

        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """ Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.

        """
        return [('blog', resource_filename(__name__, 'htdocs'))]


