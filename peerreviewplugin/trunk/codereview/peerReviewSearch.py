#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

import datetime
import itertools
import time

from trac.core import *
from trac.util import format_date
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_stylesheet
from trac.web.main import IRequestHandler

from dbBackend import *
from CodeReviewStruct import *


class UserbaseModule(Component):
    implements(IRequestHandler, ITemplateProvider, INavigationContributor)

    # IRequestHandler methods
    def match_request(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            return req.path_info == '/peerReviewSearch'

    # INavigationContributor methods
    def get_active_navigation_item(self, req):

        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return []

    def process_request(self, req):
        req.perm.require('CODE_REVIEW_DEV')
        data = {}

        #check permissions
        if 'CODE_REVIEW_MGR' in req.perm:
            data['manager'] = 1
        else:
            data['manager'] = 0

        #if the doSearch parameter is 'yes', perform the search
        #this parameter is set when someone searches
        if req.args.get('doSearch') == 'yes':
            results = self.performSearch(req, data)
            #if there are no results - fill the return array
            #with blank data.
            if len(results) == 0:
                noValResult = []
                noValResult.append("No results match query.")
                noValResult.append("")
                noValResult.append("")
                noValResult.append("")
                noValResult.append("")
                results.append(noValResult)
            data['results'] = results
            data['doSearch'] = 'yes'

        #for the top-right nav links
        data['main'] = "no"
        data['create'] = "no"
        data['search'] = "yes"
        data['options'] = "no"

        #get the database
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        users = dbBack.getPossibleUsers()
        #sets the possible users for the user combo-box
        data['users'] = users
        #creates a year array containing the last 10
        #years - for the year combo-box
        now = datetime.datetime.now()
        year = now.year
        years = []
        for i in range(0, 11):
            years.append(year - i)

        data['years'] = years
        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        return 'peerReviewSearch.html', data, None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]

    #Performs the search
    def performSearch(self, req, data):
        #create a code review struct to hold the search parameters
        crStruct = CodeReviewStruct(None)
        #get the search parameters from POST
        author = req.args.get('Author')
        name = req.args.get('CodeReviewName')
        status = req.args.get('Status')
        month = req.args.get('DateMonth')
        day = req.args.get('DateDay')
        year = req.args.get('DateYear')

        #check for entered date values, if none are set
        #default to 0
        if month is None:
            month = '0'
        if day is None:
            day = '0'
        if year is None:
            year = '0'

        #store date values for ClearSilver - used to reset values to
        #search parameters after a search is performed
        data['searchValues_month'] = month
        data['searchValues_day'] = day
        data['searchValues_year'] = year
        data['searchValues_status'] = status
        data['searchValues_author'] = author
        data['searchValues_name'] = name

        #dates are ints in TRAC - convert search date to int
        fromdate = "-1"

        if (month != '0') and (day != '0') and (year != '0'):
            t = time.strptime(month + '/' + day + '/' + year[2] + year[3], '%x')
            #I have no idea what this is doing - obtained from TRAC source
            fromdate = time.mktime((t[0], t[1], t[2], 23, 59, 59, t[6], t[7], t[8]))
            #convert to string for database lookup
            fromdate = `fromdate`

        selectString = 'Select...'
        data['dateSelected'] = fromdate
        #if user has not selected parameter - leave
        #value in struct NULL
        if author != selectString:
            crStruct.Author = author

        if name != selectString:
            crStruct.Name = name

        if status != selectString:
            crStruct.Status = status

        crStruct.DateCreate = fromdate
        #get the database
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)

        #perform search
        results = dbBack.searchCodeReviews(crStruct)
        returnArray = []
        tempArray = []

        if results is None:
            return returnArray
        #fill ClearSilver friendly array with
        #search results
        for struct in results:
            tempArray.append(struct.IDReview)
            tempArray.append(struct.Author)
            tempArray.append(struct.Status)
            tempArray.append(format_date(struct.DateCreate))
            tempArray.append(struct.Name)
            returnArray.append(tempArray)
            tempArray = []

        return returnArray
