# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Dan Ordille <dordille@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import posixpath
import re
import unicodedata

from trac.attachment import Attachment
from trac.core import Component, TracError, implements
from trac.util import get_reporter_id
from trac.util.text import stripws
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_link, add_script, \
                            add_stylesheet


class AwesomeAttachments(Component):

    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if req.path_info == '/newticket' and 'submit' in req.args:
            req.add_redirect_listener(self._add_attachments)
            req.args.pop('attachment', None)
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html' and req.path_info == '/newticket':
            add_script(req, 'awesome/js/awesome.js')
            add_stylesheet(req, 'awesome/css/awesome.css')
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

    _ticket_path_re = re.compile(r'/ticket/([0-9]+)$')

    def _add_attachments(self, req, url, permanent):
        match = self._ticket_path_re.search(url)
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

        filename = _normalized_filename(upload.filename)
        if not filename:
            raise TracError(_("No file uploaded"))

        attachment.description = description
        attachment.author = get_reporter_id(req, 'author')
        attachment.ipnr = req.remote_addr

        attachment.insert(filename, upload.file, size)


_control_codes_re = re.compile(
    '[' +
    ''.join(filter(lambda c: unicodedata.category(c) == 'Cc',
                   map(unichr, xrange(0x10000)))) +
    ']')


def _normalized_filename(filepath):
    # We try to normalize the filename to unicode NFC if we can.
    # Files uploaded from OS X might be in NFD.
    if not isinstance(filepath, unicode):
        filepath = unicode(filepath, 'utf-8')
    filepath = unicodedata.normalize('NFC', filepath)
    # Replace control codes with spaces, e.g. NUL, LF, DEL, U+009F
    filepath = _control_codes_re.sub(' ', filepath)
    # Replace backslashes with slashes if filename is Windows full path
    if filepath.startswith('\\') or re.match(r'[A-Za-z]:\\', filepath):
        filepath = filepath.replace('\\', '/')
    # We want basename to be delimited by only slashes on all platforms
    filename = posixpath.basename(filepath)
    filename = stripws(filename)
    return filename
