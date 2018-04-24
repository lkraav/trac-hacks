# Based on code from : http://trac-hacks.org/wiki/VotePlugin
# Ported to a 5 star style voting system

import re
import pkg_resources

from trac.core import Component, implements
from trac.config import ListOption
from trac.db import DatabaseManager, Table, Column
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.resource import get_resource_url
from trac.util import get_reporter_id
from trac.util.html import html as tag
from trac.web.api import IRequestFilter, IRequestHandler, Href
from trac.web.chrome import ITemplateProvider, add_ctxtnav, add_stylesheet, \
    add_script

pkg_resources.require('Trac >= 1.0')


class FiveStarVoteSystem(Component):
    """Allow up and down-voting on Trac resources."""

    implements(ITemplateProvider, IRequestFilter, IRequestHandler,
               IEnvironmentSetupParticipant, IPermissionRequestor)

    voteable_paths = ListOption(
        'fivestarvote', 'paths', '^/$,^/wiki*,^/ticket*',
        doc='List of URL paths to allow voting on. Globs are supported.')

    schema = [
        Table('fivestarvote', key=('resource', 'username', 'vote'))[
            Column('resource'),
            Column('username'),
            Column('vote', 'int'),
        ]
    ]

    path_match = re.compile(r'/fivestarvote/([1-5])/(.*)')

    # Public methods

    def get_vote_counts(self, resource):
        """Get total, count and tally vote counts and return them in a
        tuple.
        """
        resource = self.normalise_resource(resource)
        for vsum, total in self.env.db_query("""
                SELECT sum(vote), count(*) FROM fivestarvote
                WHERE resource=%s
                """, (resource,)):
            break
        else:
            vsum = 0
            total = 0
        tally = vsum / total if total > 0 else 0
        return vsum, total, tally

    def get_vote(self, req, resource):
        """Return the current users vote for a resource."""
        resource = self.normalise_resource(resource)
        for vote, in self.env.db_query("""
                SELECT vote FROM fivestarvote
                WHERE username=%s AND resource = %s
                """, (get_reporter_id(req), resource)):
            return vote
        else:
            return 0

    def set_vote(self, req, resource, vote):
        """Vote for a resource."""
        resource = self.normalise_resource(resource)
        with self.env.db_transaction as db:
            db("""
                DELETE FROM fivestarvote
                WHERE username=%s AND resource = %s
                """, (get_reporter_id(req), resource))
            if vote:
                db("""
                    INSERT INTO fivestarvote (resource, username, vote)
                    VALUES (%s, %s, %s)
                    """, (resource, get_reporter_id(req), vote))

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['VOTE_VIEW', 'VOTE_MODIFY']

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('fivestarvote', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods

    def match_request(self, req):
        return 'VOTE_VIEW' in req.perm and self.path_match.match(req.path_info)

    def process_request(self, req):
        req.perm.require('VOTE_MODIFY')
        match = self.path_match.match(req.path_info)
        vote, resource = match.groups()
        resource = self.normalise_resource(resource)

        self.set_vote(req, resource, vote)

        if req.args.get('js'):
            percent, str, title = self.format_votes(resource)
            req.send(','.join(("%s" % percent, str, title)))

        req.redirect(req.get_header('Referer'))

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if 'VOTE_VIEW' not in req.perm:
            return handler

        for path in self.voteable_paths:
            if re.match(path, req.path_info):
                self.render_voter(req)
                break

        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        for count, in self.env.db_query("""
                SELECT COUNT(*) FROM fivestarvote
                """):
            return False
        else:
            return True

    def upgrade_environment(self, db=None):
        db_backend = DatabaseManager(self.env).get_connector()[0]
        for table in self.schema:
            for stmt in db_backend.to_sql(table):
                self.env.db_transaction(stmt)

    # Internal methods

    def render_voter(self, req):
        resource = self.normalise_resource(req.path_info)

        count = self.get_vote_counts(resource)

        add_stylesheet(req, 'fivestarvote/css/fivestarvote.css')

        names = ['', 'one', 'two', 'three', 'four', 'five']
        els = []
        percent = 0
        if count[2] > 0:
            percent = count[2] * 20

        str = "Currently %s/5 stars." % count[2]
        sign = '%'
        style = "width: %s%s" % (percent, sign)
        li = tag.li(str, class_='current-rating', style=style)
        els.append(li)
        classname = ''
        if 'VOTE_MODIFY' in req.perm and get_reporter_id(req) != 'anonymous':
            add_script(req, 'fivestarvote/js/fivestarvote.js',
                       mimetype='text/javascript')
            for i in range(1, 6):
                href = req.href.fivestarvote(i, resource)
                a = tag.a(i, href=href, class_="item %s-star" % names[i])
                li = tag.li(a)
                els.append(li)
            classname = 'active'
        title = "Current Vote: %s users voted for a total of %s" \
                % (count[1], count[0])
        ul = tag.ul(els, id='fivestarvotes', title=title, class_=classname)
        add_ctxtnav(req, ul)

    def normalise_resource(self, resource):
        if isinstance(resource, basestring):
            resource = resource.strip('/')
            # Special-case start page
            if not resource or resource == 'wiki':
                resource = 'wiki/WikiStart'
            return resource
        return get_resource_url(self.env, resource, Href('')).strip('/')

    def format_votes(self, resource):
        count = self.get_vote_counts(resource)

        percent = 0
        if count[2] > 0:
            percent = count[2] * 20

        str = "Currently %s/5 stars." % count[2]
        title = "Current Vote: %s users voted for a total of %s" \
                % (count[1], count[0])
        return (percent, str, title)
