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

from trac.attachment import Attachment
from trac.core import Component, TracError, implements
from trac.ticket.web_ui import TicketModule
from trac.util import get_reporter_id
from trac.util.translation import _, tag_
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_link, add_script


class AwesomeAttachments(Component):

    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if req.path_info.rstrip() == '/newticket' and 'submit' in req.args:
            req.add_redirect_listener(self._add_attachments)
            req.args.pop('attachment', None)
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

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('awesome', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # Private methods

    def _add_attachments(self, req, url, permanent):
        match = TicketModule.ticket_path_re.match(url)
        if match:
            tid = match.group(1)
            attachments = req.args.getlist('attachment[]')
            descriptions = req.args.getlist('description[]')
            for attachment, description in zip(attachments, descriptions):
                if hasattr(attachment, 'filename'):
                    self._create_attachment(req, tid, attachment, description)

    def _create_attachment(self, req, tid, upload, description):
        attachment = Attachment(self.env, 'ticket', tid)

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
