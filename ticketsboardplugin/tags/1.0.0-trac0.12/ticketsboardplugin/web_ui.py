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


# Define a name for additional scripts path
SCRIPTS_PATH = 'ticketsboard'

# Define page name
PAGE_NAME = 'ticketsboard'

# Defines for checkbox ticket custom field to filter tickets to print
CHECKBOX_NAME = 'ticketsboard'
CHECKBOX_LABEL = 'On Ticketsboard'

# Sorted list of status to print on ticketsboard
SORTED_STATUS_LIST = ['new','assigned','inprogress','waitreview',
                      'reviewing','integrating','validating','suspended']

# Fields that will be printed and needed for ticketsboard (except 'id' that is
# always present)
WANTED_COLUMNS = ['summary','status','type','owner','reviewer', CHECKBOX_NAME]



class TicketsboardPage(Component):
    """Show tickets status as a virtual whiteboard ('ticketsboard').

    Add a navigation item named 'ticketsboard' that will show all active
    tickets sorted by status.
    Representation is a table based on a whiteboard shape.
    Each ticket is inside a box that is 'drag&droppable' to change the ticket
    status.

    Do not forget to add `ticketsboard` to the mainnav option in [trac].
    """
    implements(IEnvironmentSetupParticipant, INavigationContributor,
               IRequestHandler, ITemplateProvider)

    # For assignReviewer part plugin
    have_reviewer_plugin = False

    def __init__(self):
        # Check activation of assignReviewer part
        self.have_reviewer_plugin = self.env.is_component_enabled(
                "ticketsboardplugin.assignreviewer.assignrevieweroperation")

        self.log.debug("Ticketsboard: assignReviewer plugin part is%spresent" %
                       " " if self.have_reviewer_plugin else " not ")

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
                                           SORTED_STATUS_LIST)
        self.log.debug("Ticketsboard: Upgrade needed: %s" % any(missing_data))
        return any(missing_data)

    def upgrade_environment(self, db):
        """Perform the environment upgrade for the needed status and
        checkbox.
        """
        missing_data = _trac_needs_upgrade(self.env, self.config,
                                           CHECKBOX_NAME,
                                           SORTED_STATUS_LIST)

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
                print "  Ticket-workflow is too linked to your needs."
                print "  So, please do this modification manually."

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
                                                self.have_reviewer_plugin)

        # Retrieve tickets corresponding to each wanted status
        for status in SORTED_STATUS_LIST:
            # Ask for each status the corresponding tickets.
            # Specifying the wanted tickets fields needed and a restriction.
            # As there may be a lot of tickets for each status we add a filter
            # which is a checkbox ticket custom field.
            query_string = _set_query_string(status, (CHECKBOX_NAME, '1'),
                                             WANTED_COLUMNS)
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
        data['status_list'] = SORTED_STATUS_LIST
        data['tickets'] = tickets

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
def _set_query_string(status, filter_, wanted_columns):
    """Set a query string with following options:
    `status`: ask only tickets with the corresponding status
    `filter_`: add a filter in addition of status
    `wanted_columns`: tickets fields that we wanted to retrieve
    """
    option = '%s=%s' % filter_
    columns = ['col=%s' % column for column in wanted_columns]
    status = 'status=%s' % status
    return '&'.join([status, option] + columns)

def _execute_query(env, req, query_string):
    """Execute a query corresponding to the given string"""
    query = Query.from_string(env, query_string)
    return query.execute(req)

def _update_tickets_changes(env, req, assign_reviewer):
    """Change ticket status according to user request given through the html
    page.

    But be careful, there are restrictions for some status:
    - new state: will clear owner and reviewer fields
    - assigned state: will set owner field
    - inprogress state: will set owner field
    - reviewing state: will set reviewer field
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

        # Prepare fields to update
        values['status'] = status
        if new_owner != "":
            values['owner'] = new_owner
        if new_reviewer != "":
            values['reviewer'] = new_reviewer

        # For some status you need more informations
        if status == "reviewing" and assign_reviewer:
            # To put a ticket in 'reviewing' state the reviewer field has to be
            # set (if assignReviewer part is enable)
            # if this field is empty use the one given by html input text form
            if new_reviewer == "" and t['reviewer'] in ["", "--"]:
                error_msg += ('You cannot push ticket #%s in \"reviewing\" '
                              'without adding a reviewer. ' % ticket_id)
                continue

        elif status == "assigned":
            # To put a ticket in 'assigned' states the owner field has to be set
            # if this field is empty use the one given by html input text form
            if new_owner == "" and t['owner'] in ["", "somebody"]:
                error_msg += ('You cannot push ticket #%s in \"%s\" without '
                              'adding an owner. ' % (ticket_id, status))
                continue

        elif status == "new":
            # To put a ticket in 'new' state the reviewer and owner fields have
            # to be empty
            values['owner'] = ""
            values['reviewer'] = ""

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
