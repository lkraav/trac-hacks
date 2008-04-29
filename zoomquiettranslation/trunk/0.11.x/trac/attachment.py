# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2005 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Jonas Borgström <jonas@edgewall.com>
#         Christopher Lenz <cmlenz@gmx.de>

from datetime import datetime
import os
import re
import shutil
import time
import unicodedata

from genshi.builder import tag

from trac import perm, util
from trac.config import BoolOption, IntOption
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.mimeview import *
from trac.perm import PermissionError, PermissionSystem, IPermissionPolicy
from trac.resource import *
from trac.util import get_reporter_id, create_unique_file, content_disposition
from trac.util.datefmt import to_timestamp, utc
from trac.util.text import unicode_quote, unicode_unquote, pretty_size
from trac.util.translation import _
from trac.web import HTTPBadRequest, IRequestHandler
from trac.web.chrome import add_link, add_stylesheet, add_ctxtnav, \
                            INavigationContributor
from trac.web.href import Href
from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.formatter import format_to_oneliner


class InvalidAttachment(TracError):
    """Exception raised when attachment validation fails."""


class IAttachmentChangeListener(Interface):
    """Extension point interface for components that require notification when
    attachments are created or deleted."""

    def attachment_added(attachment):
        """Called when an attachment is added."""

    def attachment_deleted(attachment):
        """Called when an attachment is deleted."""


class IAttachmentManipulator(Interface):
    """Extension point interface for components that need to manipulate
    attachments.
    
    Unlike change listeners, a manipulator can reject changes being committed
    to the database."""

    def prepare_attachment(req, attachment, fields):
        """Not currently called, but should be provided for future
        compatibility."""

    def validate_attachment(req, attachment):
        """Validate an attachment after upload but before being stored in Trac
        environment.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be any of `description`, `username`, `filename`,
        `content`, or `None` to indicate an overall problem with the
        attachment. Therefore, a return value of `[]` means everything is
        OK."""

class ILegacyAttachmentPolicyDelegate(Interface):
    """Interface that can be used by plugins to seemlessly participate to the
       legacy way of checking for attachment permissions.

       This should no longer be necessary once it becomes easier to 
       setup fine-grained permissions in the default permission store.
    """

    def check_attachment_permission(action, username, resource, perm):
        """Return the usual True/False/None security policy decision
           appropriate for the requested action on an attachment.

            :param action: one of ATTACHMENT_VIEW, ATTACHMENT_CREATE,
                                  ATTACHMENT_DELETE
            :param username: the user string
            :param resource: the `Resource` for the attachment. Note that when
                             ATTACHMENT_CREATE is checked, the resource `.id`
                             will be `None`. 
            :param perm: the permission cache for that username and resource
            """


class Attachment(object):

    def __init__(self, env, parent_realm_or_attachment_resource,
                 parent_id=None, filename=None, db=None):
        if isinstance(parent_realm_or_attachment_resource, Resource):
            self.resource = parent_realm_or_attachment_resource
        else:
            self.resource = Resource(parent_realm_or_attachment_resource,
                                     parent_id).child('attachment', filename)
        self.env = env
        self.parent_realm = self.resource.parent.realm
        self.parent_id = unicode(self.resource.parent.id)
        if self.resource.id:
            self._fetch(self.resource.id, db)
        else:
            self.filename = None
            self.description = None
            self.size = None
            self.date = None
            self.author = None
            self.ipnr = None

    def _set_filename(self, val):
        self.resource.id = val

    filename = property(lambda self: self.resource.id, _set_filename)

    def _fetch(self, filename, db=None):
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT filename,description,size,time,author,ipnr "
                       "FROM attachment WHERE type=%s AND id=%s "
                       "AND filename=%s ORDER BY time",
                       (self.parent_realm, unicode(self.parent_id), filename))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            self.filename = filename
            raise ResourceNotFound(_("Attachment '%(title)s' does not exist.",
                                     title=self.title), _('Invalid Attachment'))
        self.filename = row[0]
        self.description = row[1]
        self.size = row[2] and int(row[2]) or 0
        time = row[3] and int(row[3]) or 0
        self.date = datetime.fromtimestamp(time, utc)
        self.author = row[4]
        self.ipnr = row[5]

    def _get_path(self):
        path = os.path.join(self.env.path, 'attachments', self.parent_realm,
                            unicode_quote(self.parent_id))
        if self.filename:
            path = os.path.join(path, unicode_quote(self.filename))
        return os.path.normpath(path)
    path = property(_get_path)

    def _get_title(self):
        return '%s:%s: %s' % (self.parent_realm, 
                              self.parent_id, self.filename)
    title = property(_get_title)

    def delete(self, db=None):
        assert self.filename, 'Cannot delete non-existent attachment'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM attachment WHERE type=%s AND id=%s "
                       "AND filename=%s", (self.parent_realm, self.parent_id,
                       self.filename))
        if os.path.isfile(self.path):
            try:
                os.unlink(self.path)
            except OSError:
                self.env.log.error('Failed to delete attachment file %s',
                                   self.path, exc_info=True)
                if handle_ta:
                    db.rollback()
                raise TracError(_('Could not delete attachment'))

        self.env.log.info('Attachment removed: %s' % self.title)
        if handle_ta:
            db.commit()

        for listener in AttachmentModule(self.env).change_listeners:
            listener.attachment_deleted(self)


    def insert(self, filename, fileobj, size, t=None, db=None):
        # FIXME: `t` should probably be switched to `datetime` too
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        self.size = size and int(size) or 0
        timestamp = int(t or time.time())
        self.date = datetime.fromtimestamp(timestamp, utc)

        # Make sure the path to the attachment is inside the environment
        # attachments directory
        attachments_dir = os.path.join(os.path.normpath(self.env.path),
                                       'attachments')
        commonprefix = os.path.commonprefix([attachments_dir, self.path])
        assert commonprefix == attachments_dir

        if not os.access(self.path, os.F_OK):
            os.makedirs(self.path)
        filename = unicode_quote(filename)
        path, targetfile = create_unique_file(os.path.join(self.path,
                                                           filename))
        try:
            # Note: `path` is an unicode string because `self.path` was one.
            # As it contains only quoted chars and numbers, we can use `ascii`
            basename = os.path.basename(path).encode('ascii')
            filename = unicode_unquote(basename)

            cursor = db.cursor()
            cursor.execute("INSERT INTO attachment "
                           "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                           (self.parent_realm, self.parent_id, filename,
                            self.size, timestamp, self.description,
                            self.author, self.ipnr))
            shutil.copyfileobj(fileobj, targetfile)
            self.resource.id = self.filename = filename

            self.env.log.info('New attachment: %s by %s', self.title,
                              self.author)

            if handle_ta:
                db.commit()

            for listener in AttachmentModule(self.env).change_listeners:
                listener.attachment_added(self)

        finally:
            targetfile.close()

    def select(cls, env, parent_realm, parent_id, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT filename,description,size,time,author,ipnr "
                       "FROM attachment WHERE type=%s AND id=%s ORDER BY time",
                       (parent_realm, unicode(parent_id)))
        for filename,description,size,time,author,ipnr in cursor:
            attachment = Attachment(env, parent_realm, parent_id)
            attachment.filename = filename
            attachment.description = description
            attachment.size = size and int(size) or 0
            time = time and int(time) or 0
            attachment.date = datetime.fromtimestamp(time, utc)
            attachment.author = author
            attachment.ipnr = ipnr
            yield attachment

    def delete_all(cls, env, parent_realm, parent_id, db):
        """Delete all attachments of a given resource.

        As this is usually done while deleting the parent resource,
        the `db` argument is ''not'' optional here.
        """
        attachment_dir = None
        for attachment in list(cls.select(env, parent_realm, parent_id, db)):
            attachment_dir = os.path.dirname(attachment.path)
            attachment.delete(db)
        if attachment_dir:
            try:
                os.rmdir(attachment_dir)
            except OSError:
                env.log.error("Can't delete attachment directory %s",
                              attachment_dir, exc_info=True)
            
    select = classmethod(select)
    delete_all = classmethod(delete_all)

    def open(self):
        self.env.log.debug('Trying to open attachment at %s', self.path)
        try:
            fd = open(self.path, 'rb')
        except IOError:
            raise ResourceNotFound(_("Attachment '%(filename)s' not found",
                                     filename=self.filename))
        return fd


class AttachmentModule(Component):

    implements(IEnvironmentSetupParticipant, IRequestHandler,
               INavigationContributor, IWikiSyntaxProvider,
               IResourceManager)

    change_listeners = ExtensionPoint(IAttachmentChangeListener)
    manipulators = ExtensionPoint(IAttachmentManipulator)

    CHUNK_SIZE = 4096

    max_size = IntOption('attachment', 'max_size', 262144,
        """Maximum allowed file size for ticket and wiki attachments.""")

    render_unsafe_content = BoolOption('attachment', 'render_unsafe_content',
                                       'false',
        """Whether attachments should be rendered in the browser, or
        only made downloadable.

        Pretty much any file may be interpreted as HTML by the browser,
        which allows a malicious user to attach a file containing cross-site
        scripting attacks.

        For public sites where anonymous users can create attachments it is
        recommended to leave this option disabled (which is the default).""")

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        """Create the attachments directory."""
        if self.env.path:
            os.mkdir(os.path.join(self.env.path, 'attachments'))

    def environment_needs_upgrade(self, db):
        return False

    def upgrade_environment(self, db):
        pass

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return req.args.get('realm')

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'^/(raw-)?attachment/([^/]+)(?:[/:](.*))?$',
                         req.path_info)
        if match:
            raw, realm, path = match.groups()
            if raw:
                req.args['format'] = 'raw'
            req.args['realm'] = realm
            if path:
                req.args['path'] = path.replace(':', '/')
            return True

    def process_request(self, req):
        parent_id = None
        parent_realm = req.args.get('realm')
        path = req.args.get('path')
        filename = None
        
        if not parent_realm or not path:
            raise HTTPBadRequest(_('Bad request'))

        parent_realm = Resource(parent_realm)
        action = req.args.get('action', 'view')
        if action == 'new':
            parent_id = path.rstrip('/')
        else:
            segments = path.split('/')
            parent_id = '/'.join(segments[:-1])
            filename = len(segments) > 1 and segments[-1]

        parent = parent_realm(id=parent_id)
        
        # Link the attachment page to parent resource
        parent_name = get_resource_name(self.env, parent)
        parent_url = get_resource_url(self.env, parent, req.href)
        add_link(req, 'up', parent_url, parent_name)
        add_ctxtnav(req, _('Back to %(parent)s', parent=parent_name), 
                    parent_url)
        
        if action != 'new' and not filename: 
            # there's a trailing '/', show the list
            return self._render_list(req, parent)

        attachment = Attachment(self.env, parent.child('attachment', filename))
        
        if req.method == 'POST':
            if action == 'new':
                self._do_save(req, attachment)
            elif action == 'delete':
                self._do_delete(req, attachment)
        elif action == 'delete':
            data = self._render_confirm_delete(req, attachment)
        elif action == 'new':
            data = self._render_form(req, attachment)
        else:
            data = self._render_view(req, attachment)

        add_stylesheet(req, 'common/css/code.css')
        return 'attachment.html', data, None

    # IWikiSyntaxProvider methods
    
    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('raw-attachment', self._format_link)
        yield ('attachment', self._format_link)

    # Public methods

    def attachment_data(self, context):
        """Return the list of viewable attachments.

        :param context: the rendering context corresponding to the parent
                        `Resource` of the attachments
        """
        parent = context.resource
        attachments = []
        for attachment in Attachment.select(self.env, parent.realm, parent.id):
            if 'ATTACHMENT_VIEW' in context.perm(attachment.resource):
                attachments.append(attachment)
        new_att = parent.child('attachment')
        return {'attach_href': get_resource_url(self.env, new_att,
                                                context.href, action='new'),
                'can_create': 'ATTACHMENT_CREATE' in context.perm(new_att),
                'attachments': attachments,
                'parent': context.resource}
    
    def get_history(self, start, stop, realm):
        """Return an iterable of tuples describing changes to attachments on
        a particular object realm.

        The tuples are in the form (change, realm, id, filename, time,
        description, author). `change` can currently only be `created`.
        """
        # Traverse attachment directory
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT type, id, filename, time, description, author "
                       "  FROM attachment "
                       "  WHERE time > %s AND time < %s "
                       "        AND type = %s",
                       (to_timestamp(start), to_timestamp(stop), realm))
        for realm, id, filename, ts, description, author in cursor:
            time = datetime.fromtimestamp(ts, utc)
            yield ('created', realm, id, filename, time, description, author)

    def get_timeline_events(self, req, resource_realm, start, stop):
        """Return an event generator suitable for ITimelineEventProvider.

        Events are changes to attachments on resources of the given
        `resource_realm.realm`.
        """
        for change, realm, id, filename, time, descr, author in \
                self.get_history(start, stop, resource_realm.realm):
            attachment = resource_realm(id=id).child('attachment', filename)
            if 'ATTACHMENT_VIEW' in req.perm(attachment):
                yield ('attachment', time, author, (attachment, descr), self)

    def render_timeline_event(self, context, field, event):
        attachment, descr = event[3]
        if field == 'url':
            return self.get_resource_url(attachment, context.href)
        elif field == 'title':
            name = get_resource_name(self.env, attachment.parent)
            title = get_resource_summary(self.env, attachment.parent)
            return tag(tag.em(os.path.basename(attachment.id)),
                       _(" attached to "), tag.em(name, title=title))
        elif field == 'description':
            return format_to_oneliner(self.env, context(attachment.parent),
                                      descr)
   
    # IResourceManager methods
    
    def get_resource_realms(self):
        yield 'attachment'

    def get_resource_url(self, resource, href, **kwargs):
        """Return an URL to the attachment itself.

        A `format` keyword argument equal to `'raw'` will be converted
        to the raw-attachment prefix.
        """
        format = kwargs.get('format')
        prefix = 'attachment'
        if format == 'raw':
            kwargs.pop('format')
            prefix = 'raw-attachment'
        parent_href = unicode_unquote(get_resource_url(self.env,
                            resource.parent(version=None), Href('')))
        if not resource.id: 
            # link to list of attachments, which must end with a trailing '/' 
            # (see process_request)
            return href(prefix, parent_href) + '/'
        else:
            return href(prefix, parent_href, resource.id, **kwargs)

    def get_resource_description(self, resource, format=None, **kwargs):
        if format == 'compact':
            return '%s:%s' % (get_resource_shortname(self.env,
                                                     resource.parent),
                              resource.filename)
        elif format == 'summary':
            return Attachment(self.env, resource).description
        if resource.id:
            return _("Attachment '%(id)s' in %(parent)s", id=resource.id,
                     parent=get_resource_name(self.env, resource.parent))
        else:
            return _("Attachments of %(parent)s",
                     parent=get_resource_name(self.env, resource.parent))

    # Internal methods

    def _do_save(self, req, attachment):
        req.perm(attachment.resource).require('ATTACHMENT_CREATE')

        if 'cancel' in req.args:
            req.redirect(get_resource_url(self.env, attachment.resource.parent,
                                          req.href))

        upload = req.args['attachment']
        if not hasattr(upload, 'filename') or not upload.filename:
            raise TracError(_('No file uploaded'))
        if hasattr(upload.file, 'fileno'):
            size = os.fstat(upload.file.fileno())[6]
        else:
            upload.file.seek(0, 2) # seek to end of file
            size = upload.file.tell()
            upload.file.seek(0)
        if size == 0:
            raise TracError(_("Can't upload empty file"))

        # Maximum attachment size (in bytes)
        max_size = self.max_size
        if max_size >= 0 and size > max_size:
            raise TracError(_('Maximum attachment size: %(num)s bytes',
                              num=max_size), _('Upload failed'))

        # We try to normalize the filename to unicode NFC if we can.
        # Files uploaded from OS X might be in NFD.
        filename = unicodedata.normalize('NFC', unicode(upload.filename,
                                                        'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        if not filename:
            raise TracError(_('No file uploaded'))
        # Now the filename is known, update the attachment resource
        # attachment.filename = filename
        attachment.description = req.args.get('description', '')
        attachment.author = get_reporter_id(req, 'author')
        attachment.ipnr = req.remote_addr

        # Validate attachment
        for manipulator in self.manipulators:
            for field, message in manipulator.validate_attachment(req,
                                                                  attachment):
                if field:
                    raise InvalidAttachment(_('Attachment field %(field)s is '
                                              'invalid: %(message)s',
                                              field=field, message=message))
                else:
                    raise InvalidAttachment(_('Invalid attachment: %(message)s',
                                              message=message))

        if req.args.get('replace'):
            try:
                old_attachment = Attachment(self.env,
                                            attachment.resource(id=filename))
                if not (old_attachment.author and req.authname \
                        and old_attachment.author == req.authname):
                    req.perm(attachment.resource).require('ATTACHMENT_DELETE')
                old_attachment.delete()
            except TracError:
                pass # don't worry if there's nothing to replace
            attachment.filename = None
        attachment.insert(filename, upload.file, size)

        req.redirect(get_resource_url(self.env, attachment.resource(id=None),
                                      req.href))

    def _do_delete(self, req, attachment):
        req.perm(attachment.resource).require('ATTACHMENT_DELETE')

        parent_href = get_resource_url(self.env, attachment.resource.parent,
                                       req.href)
        if 'cancel' in req.args:
            req.redirect(parent_href)

        attachment.delete()
        req.redirect(parent_href)

    def _render_confirm_delete(self, req, attachment):
        req.perm(attachment.resource).require('ATTACHMENT_DELETE')
        return {'mode': 'delete',
                'title': _('%(attachment)s (delete)',
                           attachment=get_resource_name(self.env,
                                                        attachment.resource)),
                'attachment': attachment}

    def _render_form(self, req, attachment):
        req.perm(attachment.resource).require('ATTACHMENT_CREATE')
        return {'mode': 'new', 'author': get_reporter_id(req),
            'attachment': attachment, 'max_size': self.max_size}

    def _render_list(self, req, parent):
        attachment = parent.child('attachment')
        data = {
            'mode': 'list',
            'attachment': None, # no specific attachment
            'attachments': self.attachment_data(Context.from_request(req,
                                                                     parent))
        }

        return 'attachment.html', data, None

    def _render_view(self, req, attachment):
        req.perm(attachment.resource).require('ATTACHMENT_VIEW')
        can_delete = 'ATTACHMENT_DELETE' in req.perm(attachment.resource)
        req.check_modified(attachment.date, str(can_delete))

        data = {'mode': 'view',
                'title': get_resource_name(self.env, attachment.resource),
                'attachment': attachment}

        fd = attachment.open()
        try:
            mimeview = Mimeview(self.env)

            # MIME type detection
            str_data = fd.read(1000)
            fd.seek(0)
            
            mime_type = mimeview.get_mimetype(attachment.filename, str_data)

            # Eventually send the file directly
            format = req.args.get('format')
            if format in ('raw', 'txt'):
                if not self.render_unsafe_content:
                    # Force browser to download files instead of rendering
                    # them, since they might contain malicious code enabling 
                    # XSS attacks
                    req.send_header('Content-Disposition', 'attachment')
                if format == 'txt':
                      mime_type = 'text/plain'
                elif not mime_type:
                    mime_type = 'application/octet-stream'
                if 'charset=' not in mime_type:
                    charset = mimeview.get_charset(str_data, mime_type)
                    mime_type = mime_type + '; charset=' + charset
                req.send_file(attachment.path, mime_type)

            # add ''Plain Text'' alternate link if needed
            if (self.render_unsafe_content and 
                mime_type and not mime_type.startswith('text/plain')):
                plaintext_href = get_resource_url(self.env,
                                                  attachment.resource,
                                                  req.href, format='txt')
                add_link(req, 'alternate', plaintext_href, _('Plain Text'),
                         mime_type)

            # add ''Original Format'' alternate link (always)
            raw_href = get_resource_url(self.env, attachment.resource,
                                        req.href, format='raw')
            add_link(req, 'alternate', raw_href, _('Original Format'),
                     mime_type)

            self.log.debug("Rendering preview of file %s with mime-type %s"
                           % (attachment.filename, mime_type))

            data['preview'] = mimeview.preview_data(
                Context.from_request(req, attachment.resource), fd,
                os.fstat(fd.fileno()).st_size, mime_type,
                attachment.filename, raw_href, annotations=['lineno'])
            return data
        finally:
            fd.close()

    def _format_link(self, formatter, ns, target, label):
        link, params, fragment = formatter.split_link(target)
        ids = link.split(':', 2)
        attachment = None
        if len(ids) == 3:
            known_realms = ResourceSystem(self.env).get_known_realms()
            # new-style attachment: TracLinks (filename:realm:id)
            if ids[1] in known_realms:
                attachment = Resource(ids[1], ids[2]).child('attachment',
                                                            ids[0])
            else: # try old-style attachment: TracLinks (realm:id:filename)
                if ids[0] in known_realms:
                    attachment = Resource(ids[0], ids[1]).child('attachment',
                                                                ids[2])
        else: # local attachment: TracLinks (filename)
            attachment = formatter.resource.child('attachment', link)
        if attachment:
            try:
                model = Attachment(self.env, attachment)
                format = None
                if ns.startswith('raw'):
                    format = 'raw'
                href = get_resource_url(self.env, attachment, formatter.href,
                                        format=format)
                return tag.a(label, class_='attachment', href=href + params,
                             title=get_resource_name(self.env, attachment))
            except ResourceNotFound, e:
                pass
            # FIXME: should be either:
            #
            # model = Attachment(self.env, attachment)
            # if model.exists:
            #     ...
            #
            # or directly:
            #
            # if attachment.exists:
            #
            # (related to #4130)
        return tag.a(label, class_='missing attachment', rel='nofollow')


class LegacyAttachmentPolicy(Component):

    implements(IPermissionPolicy)
    
    delegates = ExtensionPoint(ILegacyAttachmentPolicyDelegate)

    # IPermissionPolicy methods

    _perm_maps = {
        'ATTACHMENT_CREATE': {'ticket': 'TICKET_APPEND', 'wiki': 'WIKI_MODIFY',
                              'milestone': 'MILESTONE_MODIFY'},
        'ATTACHMENT_VIEW': {'ticket': 'TICKET_VIEW', 'wiki': 'WIKI_VIEW',
                            'milestone': 'MILESTONE_VIEW'},
        'ATTACHMENT_DELETE': {'ticket': 'TICKET_ADMIN', 'wiki': 'WIKI_DELETE',
                              'milestone': 'MILESTONE_DELETE'},
    }

    def check_permission(self, action, username, resource, perm):
        perm_map = self._perm_maps.get(action)
        if not perm_map or not resource or resource.realm != 'attachment':
            return
        legacy_action = perm_map.get(resource.parent.realm)
        if legacy_action:
            decision = legacy_action in perm
            if not decision:
                self.env.log.debug('LegacyAttachmentPolicy denied %s '
                                   'access to %s. User needs %s' %
                                   (username, resource, legacy_action))
            return decision
        else:
            for d in self.delegates:
                decision = d.check_attachment_permission(action, username,
                        resource, perm)
                if decision is not None:
                    return decision
