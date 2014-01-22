# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Dan Ordille <dordille@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import unicodedata

from genshi.builder import tag
from trac.attachment import Attachment
from trac.core import Component, TracError, implements
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.web_ui import TicketModule
from trac.util import get_reporter_id
from trac.util.text import exception_to_unicode
from trac.util.translation import _, tag_
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_link, add_notice,\
                            add_script, add_warning
try:
    from trac.util.html import to_fragment
except ImportError:
    from genshi.builder import Fragment
    from trac.util.text import to_unicode
    try:
        from babel.support import LazyProxy
    except ImportError:
        LazyProxy = None
    def to_fragment(input):
        """Convert input to a `Fragment` object."""
        if isinstance(input, TracError):
            input = input.message
        if LazyProxy and isinstance(input, LazyProxy):
            input = input.value
        if isinstance(input, Fragment):
            return input
        return tag(to_unicode(input))


class AwesomeAttachments(Component):
  
    implements(IRequestFilter, ITemplateProvider)
  
    ### IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html' and \
                req.path_info.rstrip() == '/newticket':
            add_script(req, 'awesome/js/awesome.js')
            add_link(req, 'image',
                     req.href.chrome('awesome/images/add.png'),
                     'add', 'text/png', 'add-image')
            add_link(req, 'image',
                     req.href.chrome('awesome/images/delete.png'),
                     'delete', 'text/png', 'delete-image')
            add_link(req, 'image',
                     req.href.chrome('awesome/images/edit.png'),
                     'edit', 'text/png', 'edit-image')

        return template, data, content_type

    ### ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('awesome', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


class TicketUploadModule(TicketModule):

    def _create_attachment(self, req, ticket, upload, description):
        if hasattr(upload, 'filename'):
            attachment = Attachment(self.env, 'ticket', ticket.id)
      
        if hasattr(upload.file, 'fileno'):
            size = os.fstat(upload.file.fileno())[6]
        else:
            upload.file.seek(0, 2)
            size = upload.file.tell()
            upload.file.seek(0)
        if size == 0:
            raise TracError(_("Can't upload empty file"))
        
        max_size = self.env.config.get('attachment', 'max_size')
        if 0 <= max_size < size:
            raise TracError(_('Maximum attachment size: %(num)s bytes',
                              num=max_size), _("Upload failed"))
        
        filename = unicodedata.normalize('NFC',
                                         unicode(upload.filename, 'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        if not filename:
            raise TracError(_("No file uploaded"))
      
        attachment.description = description
        if 'author' in req.args:
            attachment.author = get_reporter_id(req, 'author')
            attachment.ipnr = req.remote_addr
      
        attachment.insert(filename, upload.file, size)
      
    def _do_create(self, req, ticket):
        ticket.insert()

        # Notify
        try:
            tn = TicketNotifyEmail(self.env)
            tn.notify(ticket, newticket=True)
        except Exception, e:
            self.log.error("Failure sending notification on creation of "
                    "ticket #%s: %s", ticket.id, exception_to_unicode(e))
            add_warning(req, tag_("The ticket has been created, but an error "
                                  "occurred while sending notifications: "
                                  "%(message)s", message=to_fragment(e)))

        # Redirect the user to the newly created ticket or add attachment
        ticketref = tag.a('#', ticket.id, href=req.href.ticket(ticket.id))
        if req.args['attachment[]'] != '':
            if isinstance(req.args['attachment[]'], list):
                for i in range(len(req.args['attachment[]'])):
                    self._create_attachment(req, ticket,
                                            req.args['attachment[]'][i],
                                            req.args['description[]'][i])
            else:
                self._create_attachment(req, ticket, req.args['attachment[]'],
                                        req.args['description[]'])

        if 'TICKET_VIEW' not in req.perm('ticket', ticket.id):
            add_notice(req, tag_("The ticket %(ticketref)s has been created, "
                                 "but you don't have permission to view it.",
                                 ticketref=ticketref))
            req.redirect(req.href.newticket())

        req.redirect(req.href.ticket(ticket.id))
