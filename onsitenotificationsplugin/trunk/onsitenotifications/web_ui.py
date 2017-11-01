# -*- coding: utf-8 -*-

import re

from genshi.builder import tag, Markup

from trac.core import *
from trac.notification.api import (INotificationDistributor,
                                   INotificationFormatter, NotificationSystem,
                                   get_target_id)
from trac.resource import Resource, get_resource_description, get_resource_url
from trac.web.api import IRequestHandler
from trac.web.chrome import add_ctxtnav, INavigationContributor
from trac.util.compat import set
from trac.util.text import to_unicode

from onsitenotifications.model import OnSiteMessage


class OnSiteNotificationsDistributor(Component):
    """Distributes notification events as on-site messages."""

    implements(INotificationDistributor, INavigationContributor,
               IRequestHandler)

    formatters = ExtensionPoint(INotificationFormatter)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'on-site-notification'

    def get_navigation_items(self, req):
        messages = OnSiteMessage.select_by_sid(self.env, req.session.sid,
                                               req.session.authenticated)
        yield ('metanav', 'on-site-notification',
               tag.a(Markup('&#128235; '), len(messages),
                     title="%(count)s notifications available" % {
                           'count': len(messages) },
                     href=req.href.notification()) if messages else
               tag.span(Markup('&#128234; '),
                        title="No notifications",
                        class_='missing'))

    # INotificationDistributor

    def transports(self):
        yield 'on-site'

    def distribute(self, transport, recipients, event):
        if transport != 'on-site':
            return

        if event.realm == 'ticket' and event.category == 'batchmodify':
            for ticket_event in event.get_ticket_change_events(self.env):
                self.distribute(transport, recipients, ticket_event)
            return

        formats = {}
        for f in self.formatters:
            for style, realm in f.get_supported_styles(transport):
                if realm == event.realm:
                    formats[style] = f
        if not formats:
            self.log.error("OnSiteDistributor: No formats found for %s %s",
                           transport, event.realm)
            return

        msgdict = {}
        for sid, authed, addr, fmt in recipients:
            if fmt not in formats:
                self.log.debug("OnSiteDistributor: Format %s not available "
                               "for %s %s", fmt, transport, event.realm)
                continue

            if sid:
                msgdict.setdefault(fmt, set()).add((sid, authed))

        for fmt, sids in msgdict.iteritems():
            message = formats[fmt].format(transport, fmt, event)
            message = to_unicode(message)
            for sid, authenticated in sids:
                OnSiteMessage.add(self.env, sid, authenticated, message,
                                  event.realm, get_target_id(event.target))

    # IRequestHandler methods

    MATCH_REQUEST_RE = re.compile(r'/notification(?:/(\d+))?$')

    def match_request(self, req):
        match = self.MATCH_REQUEST_RE.match(req.path_info)
        if match:
            if match.group(1):
                req.args['message-id'] = match.group(1)
            return True

    def process_request(self, req):
        if 'message-id' in req.args:
            id = int(req.args.get('message-id'))
            return self._render_message(req, id)
        return self._render_list(req)

    def _render_list(self, req):
        if req.method == 'POST':
            action = req.args.get('action')
            if action == 'deletenotifications':
                OnSiteMessage.delete_by_sid(self.env, req.session.sid,
                                            req.session.authenticated)

        messages = OnSiteMessage.select_by_sid(self.env, req.session.sid,
                                               req.session.authenticated)
        items = []
        for message in messages:
            r = Resource(message['realm'], message['target'])
            items.append({
                'resource': get_resource_description(self.env, r),
                'details': get_resource_description(self.env, r,
                                                    format='summary'),
                'resource_href': get_resource_url(self.env, r, req.href),
                'details_href': req.href.notification(message['id']),
            })

        data = { 'items': items }
        return "onsitenotification_list.html", data, None

    def _render_message(self, req, id):
        message = OnSiteMessage.select_by_id(self.env, id)
        if not (message['sid'] == req.session.sid and 
                message['authenticated'] == req.session.authenticated):
            raise ResourceNotFound("Message does not exist")
        if not message:
            raise ResourceNotFound("Message does not exist")

        resource = Resource(message['realm'], message['target'])
        data = {
            'message': {
                'subject': get_resource_description(self.env, resource),
                'body': message['message'],
            },
        }

        return "onsitenotification.html", data, None
