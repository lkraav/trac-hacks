# -*- coding: utf8 -*-

#
# To start developing a new Trac Plugin I used those references (and copied some of their code, too):
#
#  http://trac.edgewall.org/wiki/TracDev
#  Trac DiscussionPlugin source code: http://trac-hacks.org/wiki/DiscussionPlugin (author: http://trac-hacks.org/wiki/Blackhex)
#  Trac TimingAndEstimation plugin source code: http://trac-hacks.org/wiki/TimingAndEstimationPlugin (author: http://trac-hacks.org/wiki/bobbysmith007)
#  Trac source code
#
# As long as I could understand their licences would permit me to do this. If someone think I infringed something, please tell me and I will correct it immediatly.
# Thank you! Trac rocks! Python rocks! OSS rocks!
#

import re
import data

from pkg_resources import resource_filename

from trac.core import *
from trac.mimeview import Context
from trac.config import Option
from trac.util.html import html

from trac.log import logger_factory

from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor

from tracdiscussion.api import *

class ReleaseCore(Component):
    """
        The core module implements a message board, including wiki links to
        discussions, topics and messages.
    """
    implements(INavigationContributor, IRequestHandler, IPermissionRequestor, ITemplateProvider)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['RELEASE_VIEW', 'RELEASE_ADMIN', 'RELEASE_CREATE']
        
        

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'release'

    def get_navigation_items(self, req):
        if req.perm.has_permission('RELEASE_VIEW', 'RELEASE_CREATE', 'RELEASE_ADMIN'):
            yield 'mainnav', 'release', html.a('Release', href = req.href.release())



    # IRequestHandler methods
    def match_request(self, req):
        if req.path_info == "/release":
            return True

        if req.path_info == "/release/add":
            req.args['action'] = 'add'
            return True

        match = re.match("/release/(\d+)$", req.path_info)
        if match:
            req.args['id'] = match.group(1)
            req.args['action'] = 'view'
            return True
        
        match = re.match("/release/([^/]+)/(\d+)$", req.path_info)
        if match and (match.group(1) in ['edit', 'view', 'install', 'sign', 'signed']):
            req.args['id'] = match.group(2)
            req.args['action'] = match.group(1)
            return True
        
        return False

    def process_request(self, req):
        templateData = {}
        templateData['baseURL'] = req.href.release()
        templateData['ticketURL'] = req.href.ticket()
        
        if 'id' in req.args:
            templateData['release'] = data.loadRelease(self, req.args['id'])

        
        if 'action' in req.args:
            if req.args['action'] == 'view':
                return 'release_view.html', templateData, None
            
            if req.args['action'] == 'edit':
                templateData['availableVersions'] = data.findAvailableVersions(self)
                return 'release_edit.html', templateData, None
        
            if req.args['action'] == 'add':
                if req.method == "POST":
                    ## releaseVersion contains the selected version
                    ## releaseName contains the release name
                    ## releaseDescription contains the release long description
                    ## releasePlannedDate contains the date when the release should be installed on Production Environment
                    ## releaseTickets contains a comma-separated list with all tickets included in the release
                    ## releaseTicketItems contains all ticket objects
                    ## releaseSignatures contains all the users who should approve this release
                    
                    self.log.debug("Adding: POST")
                    step = req.args.get("hiddenReleaseStep")
                    if not step:
                        step = "1"
                    
                    templateData['releaseVersion'] = req.args.get("selectReleaseVersion")
                    templateData['releaseName'] = req.args.get("txtReleaseName")
                    if not templateData['releaseName']:
                        ## default release name is the version name
                        templateData['releaseName'] = templateData['releaseVersion']
                        
                    templateData['releaseDescription'] = req.args.get("txtReleaseDescription")
                    templateData['releasePlannedDate'] = req.args.get("txtReleasePlannedDate")
                    templateData['releaseTickets'] = req.args.get("hiddenReleaseTickets")
                    templateData['releaseSignatures'] = req.args.get("hiddenReleaseSignatures")
                    
                    self.log.debug("releaseSignatures: [%s]" % templateData['releaseSignatures'])
                    self.log.debug("releaseTickets: [%s]" % templateData['releaseTickets'])
                    
                    if not templateData['releaseTickets']:
                        self.log.debug("No ticket has been selected up to now")
                        if templateData['releaseVersion']:
                            self.log.debug("Setting tickets according to the selected version")
                            templateData['releaseTickets'] = ""
                            templateData['releaseTicketItems'] = data.getVersionTickets(self, templateData['releaseVersion'])
                            for ticket in templateData['releaseTicketItems']:
                                templateData['releaseTickets'] = templateData['releaseTickets'] + str(ticket['id']) + ","
                            
                    else:
                        templateData['releaseTicketItems'] = []
                        for item in templateData['releaseTickets'].split(","):
                            self.log.debug("Loading Ticket [%s]" % item)
                            templateData['releaseTicketItems'].append(data.getTicket(self, item))
                    self.log.debug("releaseTicketItems: [" + str(templateData['releaseTicketItems']) + "]")
                    
                    if (step == "2"):
                        resp = data.createRelease(self, templateData['releaseName'], templateData['releaseDescription'],
                                                  req.authname, None, templateData['releaseTickets'], templateData['releaseSignatures'])
                        self.log.debug(resp)
                        
                    
                else:
                    self.log.debug("Adding: GET")
                    
                templateData['availableVersions'] = data.findAvailableVersions(self)
                self.log.debug(templateData)
                return 'release_add.html', templateData, None

            if req.args['action'] == 'install':
                return 'release_install.html', templateData, None
            
            if req.args['action'] == 'sign':
                return 'release_sign.html', templateData, None

            if req.args['action'] == 'signed':
                data.signRelease(self, req.args['id'], req.authname)
                req.redirect(req.href.release() + '/view/' + req.args['id'])
            
        # exibe listagem de releases existentes
        templateData['baseURL'] = req.href.release()
        templateData['releases'] = data.findAvailableReleases(self)
        return 'release.html', templateData, None



    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('Release', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        genshi templates.
        """
        rtn = [resource_filename(__name__, 'templates')]
        self.log.debug(rtn)
        return rtn
