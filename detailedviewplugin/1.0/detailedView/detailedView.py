# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Jay Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re

from genshi.builder import tag
from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider

from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, ITemplateProvider, Chrome
from genshi.filters.transform import Transformer
from trac.ticket.model import Ticket
from trac.ticket.api import TicketSystem
from util import *

class DetailedView(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, ITemplateStreamFilter)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'detailedView'

    def get_navigation_items(self, req):
        if 'TICKET_VIEW' in req.perm:
            yield ('mainnav', 'detailedView',
            tag.a('Detailed View', href=req.href.detailedView()))

    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/detailedView(?:_trac)?(?:/.*)?$', req.path_info)

    def process_request(self, req):

        tickets = req.args.get('ids', 'view')
        ticketIDs = tickets.split(',')
        del ticketIDs[-1]
        detailed = []
        cloneTable = []
        changes = []
        comment = []
        tkt = None

        for id in ticketIDs:
            try:
                tkt = Ticket(self.env,id)
            except:
                tkt = None
            if tkt:
                detailed.append(tkt)
                cloneList = []
                cloneList = findClones(self,id,id,[],[])
                if cloneList:
                    cloneTable = cloneTable + cloneList
                for result in self.env.db_query("SELECT * FROM ticket_change WHERE ticket = %s " % (id)):
                    if result[3] == 'description':
                        comment.append([result[0], result[1], result[2], result[3],'modified',''])
                    elif result[3] != 'comment':
                        comment.append([result[0], result[1], result[2], result[3], result[4], result[5]])
                    else:
                        comment.insert(0,[result[0], result[1], result[2], result[3], result[4], result[5]])
                        changes.append(comment)
                        comment = []

#            changes.sort(key=lambda x: x[1])

        if len(cloneTable) > 1:
            cloneTable.sort(key=lambda x: x[1])

        data = {}
        data['changes'] = changes
        data['sortedFields'],data['textAreas'] = sortFields(TicketSystem(self.env).get_ticket_fields())
        data['detailed'] = detailed
        data['cloneTable'] = cloneTable
        data['tkt'] = tkt

        return 'detailedView.html', data, None

    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "query.html":
            chrome = Chrome(self.env)

            # insert detailedView page into the stream
            filter = Transformer('//div[@id="content"]')
            stream = stream | filter.after(chrome.render_template(req, 'detailedButton.html', data, fragment=True))
        return stream

