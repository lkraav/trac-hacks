# -*- coding: utf-8 -*-

import time

from trac.core import Component, implements
from trac.db import *
from trac.perm import IPermissionRequestor
from trac.util import Markup, format_datetime
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_stylesheet, add_script

# Determine SpamFilterPlugin presence.
try:
    from tracspamfilter.api import FilterSystem
    has_spam_filter = True
except ImportError:
    has_spam_filter = False


class GuestbookPlugin(Component):
    """
      Guestbook plugin for Trac. Allows to get some feedback from anonymous users
      even if Trac's Wiki is read-only.
    """
    implements(IPermissionRequestor, INavigationContributor,
               ITemplateProvider, IRequestHandler)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['GUESTBOOK_VIEW', 'GUESTBOOK_APPEND', 'GUESTBOOK_DELETE']

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('guestbook', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'guestbook'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('GUESTBOOK_VIEW'):
            return
        yield 'mainnav', 'guestbook', Markup('<a href="%s">%s</a>' % \
          (self.env.href.guestbook(), self.env.config.get('guestbook',
          'title', 'Guestbook')))

    # IRequestHandler methods

    def match_request(self, req):
        if req.path_info == '/guestbook' or \
                req.path_info.startswith('/guestbook/'):
            return True
        else:
            return False

    def process_request(self, req):
        req.perm.assert_permission('GUESTBOOK_VIEW')

        # getting cursor
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if 'action' in req.args:
            # process append request
            if req.args['action'] == 'newentry':
                req.perm.assert_permission('GUESTBOOK_APPEND')

                # get form values
                author = req.args['author']
                title = req.args['title']
                text = req.args['text']

                # check for spam
                self.log.debug('has_spam_filter: %s' % (has_spam_filter,))
                if has_spam_filter:
                    FilterSystem(self.env).test(req, author, 
                    [(None, title), (None, text)], req.remote_addr)

                self._append_message(cursor, author, title, text)

            # process delete request
            if req.args['action'] == 'delete':
                req.perm.assert_permission('GUESTBOOK_DELETE')
                self._delete_message(cursor, req.args['id'])

        # adding stylesheets
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'guestbook/css/guestbook.css')

        # adding scripts
        add_script(req, 'common/js/trac.js')
        add_script(req, 'common/js/wikitoolbar.js')

        # passing variables to template
        data = {'guestbook_title': self.env.config.get('guestbook',
                                                       'title', 'Guestbook'),
                'guestbook_messages': self._get_messages(req, cursor),
                'guestbook_append': req.perm.has_permission('GUESTBOOK_VIEW')
        }

        # database commit and return page content
        db.commit()
        return 'guestbook.html', data, None

    # Private methods

    def _get_messages(self, req, cursor):
        cursor.execute("""
            SELECT id, author, time, title, body FROM guestbook
            ORDER BY time""")
        columns = ['id', 'author', 'time', 'title', 'body']
        messages = []
        for message in cursor:
            message = dict(zip(columns, message))
            message['time'] =  format_datetime(message['time'])
            message['title'] = wiki_to_oneliner(message['title'], self.env)
            message['body'] = wiki_to_html(message['body'], self.env, req)
            messages.append(message)
        return messages

    def _append_message(self, cursor, author, title, text):
        cursor.execute("""
            INSERT INTO guestbook (author, time, title, body)
            VALUES (%s, %s, %s, %s)
            """, (author or 'anonymous', str(time.time()),
                  title or 'untitled', text))

    def _delete_message(self, cursor, id):
        cursor.execute("DELETE FROM guestbook WHERE id = %s", [id])
