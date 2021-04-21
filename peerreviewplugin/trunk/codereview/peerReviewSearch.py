#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016-2021 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

import datetime
import itertools

from codereview.model import PeerReviewModel
from trac.core import *
from trac.util.datefmt import format_date, to_datetime, to_utimestamp, user_time, utc
from trac.web.chrome import add_stylesheet, add_script, add_script_data, Chrome, INavigationContributor
from trac.web.main import IRequestHandler

from .peerReviewMain import add_ctxt_nav_items
from .model import get_users


class PeerReviewSearch(Component):
    implements(IRequestHandler, INavigationContributor)

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/peerReviewSearch'

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return []

    def process_request(self, req):
        req.perm.require('CODE_REVIEW_DEV')
        data = {}

        # if the doSearch parameter is 'yes', perform the search
        # this parameter is set when someone searches
        if req.args.get('doSearch') == 'yes' or True:  # always start with the full list for now
            results = self.performSearch(req, data)
            if len(results) == 0:
                noValResult = ["No results match query.", "", "", "", "", ""]
                results.append(noValResult)
            data['results'] = results
            data['doSearch'] = 'yes'

        users = get_users(self.env)
        # sets the possible users for the user combo-box
        data['users'] = users
        # creates a year array containing the last 10
        # years - for the year combo-box
        now = datetime.datetime.now()
        year = now.year
        years = []
        for i in range(0, 11):
            years.append(year - i)

        data['years'] = years
        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_script(req, 'hw/js/peerReviewSearch.js')
        if req.args.get('doSearch'):
            add_script_data(req, {'dateIndexSelected': '01',
                                  'monthSelected': data['searchValues_month'],
                                  'daySelected': data['searchValues_day'],
                                  'yearSelected': data['searchValues_year'],
                                  'statusSelected': data['searchValues_status'],
                                  'authorSelected': data['searchValues_author'],
                                  'nameSelected': data['searchValues_name']})
        else:
            add_script_data(req, {'dateIndexSelected': '',
                                  'monthSelected': '',
                                  'daySelected': '',
                                  'yearSelected': '',
                                  'statusSelected': '',
                                  'authorSelected': '',
                                  'nameSelected': ''})
        add_ctxt_nav_items(req)
        if hasattr(Chrome, 'jenv'):
            return 'peerreview_search_jinja.html', data
        else:
            return 'peerreview_search.html', data, None

    # Performs the search

    def performSearch(self, req, data):
        # get the search parameters from POST
        author = req.args.get('Author', '')
        name = req.args.get('CodeReviewName', '')
        status = req.args.get('Status', '')
        month = req.args.get('DateMonth', '0')
        day = req.args.get('DateDay', '0')
        year = req.args.get('DateYear', '0')

        # store date values for JavaScript
        data['searchValues_month'] = month
        data['searchValues_day'] = day
        data['searchValues_year'] = year
        data['searchValues_status'] = status
        data['searchValues_author'] = author
        data['searchValues_name'] = name

        # dates are utimes for reviews
        fromdate = None
        date = None
        if (month != '0') and (day != '0') and (year != '0'):
            # implicitely converts to suitable timezone
            date = to_datetime(datetime.datetime(int(year), int(month), int(day)))
            fromdate = to_utimestamp(date)

        selectString = 'Select...'

        returnArray = []

        rev_model = PeerReviewModel(self.env)
        rev_model.clear_props()
        if status and status != selectString:
            rev_model['status'] = status
        if name:
            rev_model['name'] = "%" + name + "%"
        if author and author != selectString:
            rev_model['owner'] = author

        for rev in rev_model.list_matching_objects(exact_match=False):
            tempArray = [rev['review_id'], rev['owner'], rev['status'],
                         user_time(req, format_date, to_datetime(rev['created'])), rev['name']]
            if rev['closed']:
                tempArray.append(user_time(req, format_date, to_datetime(rev['closed'])))
            else:
                tempArray.append('')
            if date:
                if rev['created'] > fromdate:
                    returnArray.append(tempArray)
            else:
                returnArray.append(tempArray)

        return returnArray
