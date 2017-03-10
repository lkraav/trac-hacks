# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import json

from trac.config import Option
from trac.core import Component, implements
from trac.notification.mail import EmailDistributor
from trac.perm import IPermissionRequestor
from trac.util.html import html
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider, add_ctxtnav, add_script, \
                            add_script_data, add_stylesheet
from trac.web.main import IRequestFilter, IRequestHandler

MODE = 'quietmode'
LISTEN = 'quietlisten'


class QuietEmailDistributor(EmailDistributor):
    """Specializes Announcer's email distributor to honor quiet mode."""
    def distribute(self, transport, recipients, event):
        if hasattr(event, 'author') and self._is_quiet_mode(event.author):
            self.log.debug("%s skipping distribution of %s because quiet "
                           "mode is enabled for %s", self.__class__.__name__,
                           event.__class__.__name__, event.author)
            return
        self.log.debug("%s dispatching to EmailDistributor",
                       self.__class__.__name__)
        super(QuietEmailDistributor, self).distribute(transport, recipients,
                                                      event)

    def _is_quiet_mode(self, user):
        for val, in self.env.db_query("""
                SELECT value FROM session_attribute
                WHERE sid=%s AND name=%s
                """, (user, MODE)):
            return val == '1'
        else:
            return False


class QuietBase(object):
    """Shared class for common methods."""

    enter_label = Option('quiet', 'enter_label', _('Enter Quiet Mode'))
    leave_label = Option('quiet', 'leave_label', _('Leave Quiet Mode'))

    def _get_label(self, req, is_quiet=None):
        if is_quiet is None:
            is_quiet = self._is_quiet(req)
        return is_quiet and _(self.leave_label) or _(self.enter_label)

    def _set_quiet_action(self, req, action):
        if action == 'toggle':
            return self._set_quiet(req, not self._is_quiet(req))
        elif action in ('enter', 'leave'):
            return self._set_quiet(req, action == 'enter')
        else:
            return self._is_quiet(req)

    def _is_quiet(self, req):
        """Returns true if the user requested quiet mode."""
        val = req.session.get(MODE, '0')
        return val == '1'

    def _set_quiet(self, req, yes):
        """Set or unset quiet mode for the user."""
        val = yes and '1' or '0'
        req.session[MODE] = val
        req.session.save()
        return val == '1'


class QuietModule(Component, QuietBase):
    implements(IRequestFilter, ITemplateProvider, IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['QUIET_MODE']

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('quiet', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if 'QUIET_MODE' in req.perm and \
                req.path_info.startswith(('/ticket', '/newticket',
                                          '/changeset', '/query', '/report')):
            href = req.href(MODE, 'toggle')
            a = html.a(self._get_label(req), href=href, id=MODE)
            add_ctxtnav(req, a)
            add_script(req, 'quiet/quiet.js')
            add_stylesheet(req, 'quiet/quiet.css')
            add_script_data(req, {'quiet': {'toggle': MODE,
                                            'listen': LISTEN}})
        return template, data, content_type


class QuietAjaxModule(Component, QuietBase):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/' + MODE)

    def process_request(self, req):
        try:
            action = req.path_info[req.path_info.rfind('/') + 1:]
            is_quiet = self._set_quiet_action(req, action)
            data = {'label': self._get_label(req, is_quiet),
                    'is_quiet': is_quiet}
            process_json(req, data)
        except Exception:
            process_error(req)


class QuietListenerAjaxModule(Component):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/' + LISTEN)

    def process_request(self, req):
        try:
            data = self._get_listeners(req)
            process_json(req, data)
        except Exception:
            process_error(req)

    def _get_listeners(self, req):
        listeners = []
        for key, action in self.env.config.options('quiet'):
            if not key.endswith('.action'):
                continue
            num = key.split('.', 1)[0]
            only, eq = self.env.config.get('quiet', num + '.only_if', ''), ''
            if only and '=' in only:
                only, eq = only.split('=', 1)
            submit = self.env.config.get('quiet', num+'.submit',
                                         'false').lower()
            listeners.append({
                'action': action,
                'selector': self.env.config.get('quiet',
                                                num + '.selector', ''),
                'only': only, 'eq': eq,
                'submit': submit == 'true',
            })
        return listeners


def process_json(req, data):
    try:
        process_msg(req, 200, 'application/json', json.dumps(data))
    except Exception:
        process_error(req)


def process_error(req):
    import traceback
    msg = "Oops...\n" + traceback.format_exc() + "\n"
    process_msg(req, 500, 'text/plain', msg)


def process_msg(req, code, type, msg):
    req.send_response(code)
    req.send_header('Content-Type', type)
    req.send_header('Content-Length', len(msg))
    req.end_headers()
    req.write(msg)
