from trac.core import *
from trac.util.text import exception_to_unicode
from trac.ticket.api import ITicketChangeListener
from trac.attachment import IAttachmentChangeListener
from trac.web.chrome import add_notice, add_warning, ITemplateProvider
from trac.admin.api import IAdminPanelProvider
from trac.util.translation import gettext as _

class HipchatRelay(Component):
    """ This component does stuff. """
    implements(ITicketChangeListener, IAttachmentChangeListener, ITemplateProvider, IAdminPanelProvider)
    
    def _sendText(self, ticketid, text, projectkey):
        try:
            token = self.config.get('hipchatrelay', 'token')
            botname = self.config.get('hipchatrelay', 'botname')
            color = self.config.get('hipchatrelay', 'color')
            channel = self.config.get('hipchatrelay', projectkey) 
            if channel == "":
                channel = self.config.get('hipchatrelay', 'defaultchannel')
            ticket_url = self.env.abs_href.ticket(ticketid)
            ticket_href = "<a href='%s'>#[%s]</a>" % (ticket_url, ticketid)
            output = "Ticket %s %s" % (ticket_href, text)
            #self._debug("DEBUG: %s\n\n%s" % (type(text), text))
            # CC the default channel with all ticket status updates
            if channel != self.config.get('hipchatrelay', 'defaultchannel'):
                self._send_to_hipchat(token, botname, color, self.config.get('hipchatrelay', 'defaultchannel'), output)
            self._send_to_hipchat(token, botname, color, channel, output)
        except Exception, e:
            mystring = "UNEXPECTED ERROR: %s" % exception_to_unicode(e)
            self._debug(mystring)
            return

    def _send_to_hipchat(self, token, botname, color, channel, output):
        import urllib2, urllib
        url = "https://api.hipchat.com/v1/rooms/message?format=json&auth_token=%s" % token
        values = {'room_id' : channel, 'from' : botname, 'message' : output, 'color' : color, 'notify': '1'}
        data = urllib.urlencode(values)
        request = urllib2.Request(url, data)
        response = urllib2.urlopen(request)
        self._debug(response.read())

    def _debug(self, mystr):
        self.env.log.debug(str(mystr))

    # ITicketChangeListener methods
    def ticket_created(self, ticket):
        projectkey = ticket.values['project_name'].replace(" ", "_")
        reporter = ticket.values['reporter']
        summary = ticket.values['summary']
        type = ticket.values['type']
        text = "submitted by <b>%s</b><br />Type: %s<br />Summary: %s" % (reporter, type, summary)
        self._sendText(ticket.id, text, projectkey)

    def ticket_changed(self, ticket, comment, author, old_values):
        projectkey = ticket.values['project_name'].replace(" ", "_")
        status = ticket['status']
        summary = ticket.values['summary']
        if old_values == {}:
            text = "comment added by %s" % author
            text = text + "<br />Summary: %s" % summary
        else:
            if old_values.has_key('status'):
                old_values.pop('status')
                if status == 'assigned':
                    text = "assigned to <b>%s</b> by <b>%s</b>" % (ticket['owner'], author)
                elif status == 'accepted':
                    text = "accepted by <b>%s</b>" % author
                elif status == "closed":
                    text = "resolved by <b>%s</b> as <i>%s</i>" % (author, ticket['resolution'])
                elif status == "reopened":
                    text = "reopened by <b>%s</b>" % author
                else:
                    text = "changed by <b>%s</b>" % author
            else:
                text = "changed by <b>%s</b>" % author
            text = text + "<br />Summary: %s" % summary
            for i in old_values:
                if i in ['resolution', 'status', 'owner', 'summary']: # don't print changes to resolution, status, summary, or owner
                    pass
                elif old_values[i] == "":
                    text = text + "<br /><b>%s</b> was set to <i>%s</i>" % (i, ticket[i])
                elif ticket[i] == "":
                    text = text + "<br /><b>%s</b> was deleted" % (i)
                elif i == "description":
                    text = text + "<br /><b>%s</b> was changed to:<br /><pre>%s</pre>" % (i, ticket[i])
                else:
                    text = text + "<br /><b>%s</b> changed from <i>%s</i> to <i>%s</i>" % (i, old_values[i], ticket[i])
        if comment != "":
            text = text + "<br />Comment:<br /><pre>%s</pre>" % comment
        self._sendText(ticket.id, text, projectkey)

    def ticket_deleted(self, ticket):
        self._sendText(ticket.id, "deleted by <b>%s</b>" % author)

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('ticket', _('Ticket System'),
                   'hipchatrelay', _('Hipchat Relay'))

    def render_admin_panel(self, req, cat, page, customfield):
        req.perm.require('TRAC_ADMIN')
        options = ('token', 'botname', 'color', 'defaultchannel', 'project_map')
        # render admin panel
        project_map = self.config.get('ticket-custom', 'project_name.options').replace(" ", "_").split("|")
        for pos in range(len(project_map)):
            projkey = project_map[pos]
            project_map[pos] = [projkey, self.config.get('hipchatrelay', projkey)]

        # deal with saving data
        if req.method == 'POST':
            for option in options:
                if option == 'project_map':
                    for pos in range(len(project_map)):
                        projkey = project_map[pos][0]
                        self.config.set('hipchatrelay', projkey, req.args.get(projkey))
                else:
                    self.config.set('hipchatrelay', option, req.args.get(option))
            try:
                self.config.save()
                add_notice(req, _('Your changes have been saved.'))
            except Exception, e:
                self.log.error('Error writing to trac.ini: %s', exception_to_unicode(e))
                add_warning(req, _('Error writing to trac.ini, make sure it is '
                                   'writable by the web server. Your changes have '
                                   'not been saved.'))
            req.redirect(req.href.admin(cat, page))
        genshidata = dict((option, self.config.get('hipchatrelay', option)) for option in options)
        genshidata['project_map'] = project_map
        return 'admin_hipchatrelay.html', genshidata

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return

    # IAttachmentChangeListener
    def attachment_added(self, attachment):
        #get_ticket(attachment.parent_id), or something
        # find ticket informations..and attachments
        self._debug(attachment.parent_id)

    def attachment_deleted(attachment):
        self._debug(attachment)

