# -*- coding: utf-8 -*-

import re
import trac

from pkg_resources import resource_exists, resource_filename

from trac.config import BoolOption, ListOption, ConfigSection
from trac.core import *
from trac.perm import PermissionSystem
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import Chrome, ITemplateProvider, add_script, add_script_data
from trac.util.translation import domain_functions

add_domain, _ = \
        domain_functions('cc_selector', ('add_domain', '_'))

class TicketWebUiAddon(Component):
    implements(IRequestFilter, ITemplateProvider, IRequestHandler)

    spam_section = ConfigSection('cc_selector',
        """This section is used to handle all configurations used by
        CcSelector plugin.""", doc_domain='cc_selector')

    show_fullname = BoolOption(
        'cc_selector', 'show_fullname', False,
        doc="Display full names instead of usernames if available.", doc_domain="cc_selector")

    username_blacklist = ListOption(
        'cc_selector', 'username_blacklist', '',
        doc="Usernames separated by comma, that should never get listed.", doc_domain="cc_selector")

    def __init__(self):
        # bind the 'cc_selector' catalog to the specified locale directory
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if re.search('ticket', req.path_info):
            add_script(req, 'cc_selector/cc_selector.js')
            add_script_data(req, {'ccb_label': _('Extended Cc selection')})
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('cc_selector', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'^/cc_selector', req.path_info)
        return False if match is None else True

    def process_request(self, req):
        add_script(req, 'cc_selector/cc_selector.js')
        add_script_data(req, {'ccb_label': _('Extended Cc selection')})

        blacklist = self.username_blacklist
        privileged_users = PermissionSystem(
            self.env).get_users_with_permission('TICKET_VIEW')
        all_users = self.env.get_known_users()

        developers = filter(lambda u: u[0] in privileged_users, all_users)
        cc_developers = list(filter(lambda u: not u[0] in blacklist, developers))
        data = {
            'cc_developers': cc_developers,
            'show_fullname': self.show_fullname
        }
        return 'cc_selector_jinja.html', data, {'domain': 'cc_selector'}
