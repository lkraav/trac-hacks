# Copyright (c) 2013 Jean-Philippe Save
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pkg_resources import resource_filename

from trac.env import IEnvironmentSetupParticipant
from trac.core import implements, Component
from trac.util import Markup
from trac.web import IRequestHandler
from trac.web.chrome import add_stylesheet, add_script, \
    INavigationContributor, ITemplateProvider
from trac.ticket.query import *
from trac.ticket.api import TicketSystem
from trac.ticket import Ticket
from trac.ticket.default_workflow import get_workflow_config


# Define a name for additional scripts path
SCRIPTS_PATH = 'ticketsboard'

# Define page name
PAGE_NAME = 'ticketsboard'

# Defines for checkbox ticket custom field to filter tickets to print
CHECKBOX_NAME = 'ticketsboard'
CHECKBOX_LABEL = 'On Ticketsboard'

# Default sorted list of status to print on ticketsboard
DEFAULT_SORTED_STATUS_LIST = ['new','assigned','reviewing','closed']

# Fields that will be printed and needed for ticketsboard (except 'id' that is
# always present)
NEEDED_FIELDS = ['summary','status','type','owner','reviewer', CHECKBOX_NAME]



class TicketsboardPage(Component):
    """Show tickets status as a virtual whiteboard ('ticketsboard').

    Add a navigation item named 'ticketsboard' that will show all active
    tickets sorted by status.
    Representation is a table based on a whiteboard shape.
    Each ticket is inside a box that is 'drag&droppable' to change the ticket
    status.

    This plugin integrates several configurations that can be managed in the
    trac.ini config file through a section [ticketsboard]:
    - statuses: contains the list of status printed on the ticketsboard.
    - fields: contains a list of additional tickets fields that user wants
      to see in the ticketsboard.

    Do not forget to add `ticketsboard` to the mainnav option in [trac].
    """
    implements(IEnvironmentSetupParticipant, INavigationContributor,
               IRequestHandler, ITemplateProvider)

    def __init__(self):
        # Check activation of assignReviewer part
        self.have_reviewer_plugin = self.env.is_component_enabled(
                "ticketsboardplugin.assignreviewer.assignrevieweroperation")

        self.log.debug("Ticketsboard: assignReviewer plugin part is%spresent" %
                       " " if self.have_reviewer_plugin else " not ")

        # Retrieve actions on status from custom ticket workflow section of
        # trac.ini config file
        self.states_actions = get_workflow_config(self.config)

        # Retrieve status list from trac.ini config file
        self.status_list = self.config.get("ticketsboard",
                                           "statuses").strip(',').split(',')
        if self.status_list == ['']:
            self.status_list = DEFAULT_SORTED_STATUS_LIST

        # Retrieve additional wanted fields from trac.ini config file
        user_fields = self.config.get("ticketsboard",
                                      "fields").strip(',').split(',')
        if '' in user_fields:
            user_fields.remove('')
        self.wanted_fields = []
        self.wanted_fields.extend(NEEDED_FIELDS)
        self.wanted_fields.extend(user_fields)
        self.wanted_fields = list(set(self.wanted_fields))
        self.additionnal_fields = list(set(self.wanted_fields) -
                set(NEEDED_FIELDS))

        # Filters to add to the ticket query
        self.filters = [(CHECKBOX_NAME, '1')]

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if environment_needs_upgrade(self.config):
            upgrade_environment(self.config)

    def environment_needs_upgrade(self, db):
        """Returns the upgrade need according to the presence of all needed
        status and checkbox.
        """
        missing_data = _trac_needs_upgrade(self.env, self.config,
                                           CHECKBOX_NAME,
                                           self.status_list)
        self.log.debug("Ticketsboard: Upgrade needed: %s" % any(missing_data))
        return any(missing_data)

    def upgrade_environment(self, db):
        """Perform the environment upgrade for the needed status and
        checkbox.
        """
        missing_data = _trac_needs_upgrade(self.env, self.config,
                                           CHECKBOX_NAME,
                                           self.status_list)

        if any(missing_data):
            print "Ticketsboard plugin needs an upgrade"
            missing_checkbox, missing_status = missing_data
            if missing_checkbox:
                self.config.set("ticket-custom", CHECKBOX_NAME, "checkbox")
                self.config.set("ticket-custom", CHECKBOX_NAME + ".label",
                                CHECKBOX_LABEL)
                self.config.set("ticket-custom", CHECKBOX_NAME + ".value",
                                "false")
                self.config.save()
                print "  A \"%s\" ticket field has been added." % \
                    CHECKBOX_LABEL

            if missing_status:
                print "  Some ticket-workflow states are missing"
                for status in missing_status:
                    print "   - %s" % status
                print "  Please, synchronise your ticket-workflow states " + \
                      "with the statuses field of [ticketsboard] section " + \
                      "inside trac.ini config file."

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        """Returns the name of the navigation item that will be highlighted as
        active/current.
        """
        return PAGE_NAME

    def get_navigation_items(self, req):
        """Returns an iterable object over the navigation item to add,
        it is a tuple in the form (category, name, text).
        """
        url = req.href.ticketsboard()
        # Ticketsboard navigation item could be seen only if TICKET_VIEW
        # permission is allowed
        if req.perm.has_permission("TICKET_VIEW"):
            yield ('mainnav', PAGE_NAME,
                   Markup('<a href="%s">%s</a>' % (url,
                       PAGE_NAME.capitalize())))

    # IRequestHandler methods
    def match_request(self, req):
        """Return whether the handler wants to process the given request.
        So for us, only the ticketsboard requests.
        """
        return req.path_info == "/%s" % PAGE_NAME

    def process_request(self, req):
        """Returns the ticketsboard html template page and the data to
        substitute for the template.
        """
        # Dictionary of substitutions for the template html page
        data = {}
        # Dictionary of tickets informations sorted by status
        tickets = {}
        # Message to print for illegal operations made on the ticketsboard
        # (new tickets status not allowed...)
        error_msg = ""
        # Show only tickets impacted by user
        filter_user_current = ''
        filter_user_switch = req.authname

        # Interaction and style needed for the ticketsboard.html page
        # (JQuery-ui is for drag/drop functionality)
        add_script(req, '%s/js/jquery-ui.js' % SCRIPTS_PATH)
        add_script(req, '%s/js/ticketsboard.js' % SCRIPTS_PATH)
        add_stylesheet(req, "%s/css/ticketsboard.css" % SCRIPTS_PATH)

        # User wants to save changes on ticket status. So we have to update
        # tickets changes inside the db
        # We use the input form named 'ticketsboard_submit' in the html page to
        # interact with user to apply change request
        if req.method == 'POST' and req.args.get('ticketsboard_submit'):
            self.log.debug("Ticketsboard POST: %s" % req.args)
            error_msg = _update_tickets_changes(self.env, req,
                                                self.have_reviewer_plugin,
                                                self.states_actions)

        # User wants to filter his request to show only his tickets.
        if req.args.get('user'):
            self.log.debug("Ticketsboard POST/GET with user param: %s" % req.args)
            filter_user_current = req.args.get('user')
            filter_user_switch = ''

        # Retrieve tickets corresponding to each wanted status
        for status in self.status_list:
            # Ask for each status the corresponding tickets.
            # Specifying the wanted tickets fields needed and restrictions.
            # As there may be a lot of tickets for each status we add filters.
            if filter_user_current:
                # We would like tickets only owned or in review by a specific
                # user.
                owner_conditions = [('status', status),
                                    ('owner', filter_user_current)]
                owner_conditions.extend(self.filters)
                reviewer_conditions = [('status', status),
                                       ('reviewer', filter_user_current)]
                reviewer_conditions.extend(self.filters)
                conditions = [owner_conditions, reviewer_conditions]
            else:
                condition = [('status', status)]
                condition.extend(self.filters)
                conditions = [condition]

            query_string = _set_query_string(conditions, self.wanted_fields,
                                             'summary')
            # Execute the query
            tickets[status] = _execute_query(self.env, req, query_string)

        # Print queries result for debug
        if self.env.log_level == 'DEBUG':
            for status, tickets_list in tickets.items():
                self.log.debug('Ticketsboard: With status %s' % status)
                for ticket in tickets_list:
                    self.log.debug('Ticketsboard:  ticket #%s' % ticket['id'])

        # Store the collected informations needed to fill the template html page
        data['error_msg'] = error_msg
        data['status_list'] = self.status_list
        data['tickets'] = tickets
        data['add_fields'] = self.additionnal_fields
        if filter_user_switch:
            data['filter_user_current'] = filter_user_current
            data['filter_user_current_url'] = "ticketsboard"
            data['filter_user_switch_url'] = "ticketsboard?user=%s" % \
                                             filter_user_switch
            data['filter_user_switch_url_msg'] = "Show only my tickets"
        else:
            data['filter_user_current'] = filter_user_current
            data['filter_user_current_url'] = "ticketsboard?user=%s" % \
                                              filter_user_current
            data['filter_user_switch_url'] = "ticketsboard"
            data['filter_user_switch_url_msg'] = "Show all tickets"

        # Return the wanted page to print with the variables to substitute
        return ('%s.html' % PAGE_NAME, data, None)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Returns the directory with static resources (style sheets and Java
        Script)
        """
        return [(SCRIPTS_PATH, resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Returns the directory containing the provided template
        files.
        """
        return [resource_filename(__name__, 'templates')]



# Internal functions
def _set_query_string(conditions, wanted_columns, order):
    """Set a query string with following options:
    `conditions`: filter request with several conditions (status...) conditions
    is a double list of 'or' conditions of 'and' conditions:
    [[and_conditions],[and_conditions],...]
    Reminder, trac query allows only to have 'and conditions' inside 'or
    conditions' and not the opposite.
    `wanted_columns`: tickets fields that we wanted to retrieve
    `order`: how to sort the result (summary, ticket_id...)
    """
    and_cond = []
    for or_cond in conditions:
        and_cond.append('&'.join(['%s=%s' % cond for cond in or_cond]))
    options = '&or&'.join(and_cond)
    columns = ['col=%s' % column for column in wanted_columns]
    order = 'order=%s' % order
    return '&'.join([options] + columns + [order])

def _execute_query(env, req, query_string):
    """Execute a query corresponding to the given string"""
    query = Query.from_string(env, query_string)
    return query.execute(req)

def _update_tickets_changes(env, req, assign_reviewer, states_actions):
    """Change ticket status according to user request given through the html
    page.

    But be careful, there are restrictions for some status according to
    operations in the ticket workflow.
    For example:
    - new state: can clear owner and reviewer fields
    - assigned state: can set owner field
    - inprogress state: can set owner field
    - reviewing state: can set reviewer field
    """

    # Error message to return
    error_msg = ""

    # Tickets can be updated only if 'TICKET_MODIFY' permission is allowed
    if not req.perm.has_permission("TICKET_MODIFY"):
        return 'You need \"TICKET_MODIFY\" permission to save changes'

    # Retrieve informations from html page:
    # We use the input form named:
    # 'ticketsboard_changes' for changes on tickets status
    # 'reviewer' for changes on reviewer field
    # 'owner' for changes on owner field
    changes_value = req.args.get('ticketsboard_changes')
    new_owner = req.args.get('owner').strip()
    new_reviewer = req.args.get('reviewer').strip()

    # Parse all changes on ticket status
    # changes format given by the hmtl and JS is as following:
    # 'ticket_id:new_status,ticket_id:new_status,...'
    for change in changes_value.rstrip(',').split(','):

        [ticket_id, status] = change.split(':')
        values = {}
        t = Ticket(env, int(ticket_id))
        current_error_msg = ''

        # Prepare fields to update
        values['status'] = status
        if new_owner != "":
            values['owner'] = new_owner
        if new_reviewer != "":
            values['reviewer'] = new_reviewer

        # For some status you have restrictions to check
        for operation in states_actions[status]['operations']:
            if operation == 'set_reviewer' and assign_reviewer:
                # To put a ticket in this state the reviewer field has to be set
                # (if assignReviewer part is enable)
                # if this field is empty use the one given by html input text
                # form
                if new_reviewer == "" and t['reviewer'] in ["", "--"]:
                    current_error_msg += ('You cannot push ticket #%s in \"%s\"'
                                          ' without adding a reviewer. ' %
                                          (ticket_id, status))

            elif operation == 'set_owner':
                # To put a ticket in this state the owner field has to be set
                # if this field is empty use the one given by html input text
                # form
                if new_owner == "" and t['owner'] in ["", "somebody"]:
                    current_error_msg += ('You cannot push ticket #%s in \"%s\"'
                                          ' without adding an owner. ' %
                                          (ticket_id, status))

            elif operation == 'del_reviewer':
                # To put a ticket in this state the reviewer field has to be
                # empty
                values['reviewer'] = ""

            elif operation == 'del_owner':
                # To put a ticket in this state the owner field has to be empty
                values['owner'] = ""

        # Do not update ticket when there is an error in restrictions
        if current_error_msg != '':
            error_msg += current_error_msg
            continue

        # Update ticket
        t.populate(values)
        t.save_changes(req.authname)

    return error_msg

def _trac_needs_upgrade(env, config, wb_checkbox, wanted_status):
    """Check status and checkbox presence"""

    # Retrieve current status
    all_status = TicketSystem(env).get_all_status()

    # Parse all status to check that all needed status are present
    # and store the missing status
    missing_status = set(wanted_status) - set(all_status)

    # Check that the checkbox is present
    missing_checkbox = not config.get("ticket-custom", wb_checkbox)

    # Return:
    #  if the checkbox is missing
    #  the missing status
    return missing_checkbox, missing_status
