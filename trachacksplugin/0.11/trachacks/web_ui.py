# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008 Alec Thomas
# Copyright (C) 2009-2010 Michael Renzmann
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import random
import re
from string import Template

from genshi.builder import tag as builder
from trac.core import Component, TracError, implements
from trac.config import ConfigurationError, IntOption, Option
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.resource import Resource, ResourceNotFound, resource_exists
from trac.ticket.model import Component as TicketComponent
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from trac.util.compat import sorted
from trac.util.translation import _, tag_
from trac.web.api import (
    IRequestFilter, IRequestHandler, ITemplateStreamFilter, RequestDone
)
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider, add_ctxtnav, add_notice,
    add_script, add_stylesheet, add_warning
)

from acct_mgr.api import IAccountChangeListener, IPasswordStore
from acct_mgr.htfile import HtPasswdStore
from svnauthz.io import AuthzFileReader, AuthzFileWriter
from trachacks.validate import *
from trachacks.util import FakeRequest, natural_sort
from tractags.api import TagSystem
from tractags.macros import TagWikiMacros
from tractags.query import Query
from tracvote import VoteSystem


_SVN_CONFIG_DIR = os.environ.get('TRACHACKS_SVN_CONFIG_DIR',
                                 '/var/www/trac-hacks.org/trac/.subversion')


def pluralise(n, word):
    """Return a (naively) pluralised phrase from a count and a singular
    word."""
    if n == 0:
        return 'No %ss' % word
    elif n == 1:
        return '%i %s' % (n, word)
    else:
        return '%i %ss' % (n, word)


def get_page_name(hack_name, hack_type):
    """Compute wiki page name from hack name and type"""
    page_name = hack_name
    if not page_name.lower().endswith(hack_type):
        page_name += hack_type.title()
    return page_name


class HackDoesntExist(Aspect):
    """Validate that the hack does not exist."""
    def __init__(self, env):
        self.env = env

    def __call__(self, context, hack_name):
        hack_type = context.data.get('type', 'plugin')
        page_name = get_page_name(hack_name, hack_type)
        if WikiPage(self.env, page_name).exists:
            raise ValidationError('Page already exists.')

        repos = self.env.get_repository()
        path = '/%s' % page_name.lower()
        if repos.has_node(path):
            raise ValidationError(
                'Resulting path "%s" already exists in repository.' % path
            )

        try:
            TicketComponent(self.env, page_name)
        except ResourceNotFound:
            pass
        else:
            raise ValidationError(
                'Resulting component "%s" already exists.' % page_name
            )

        authz_file = self.env.config.getpath('trac', 'authz_file')
        authz = AuthzFileReader().read(authz_file)
        authz_paths = [p.get_path() for p in authz.get_paths()]
        for ap in authz_paths:
            if ap.startswith(path):
                raise ValidationError(
                    'Resulting path "%s" already exists in authz file.' % path
                )

        return hack_name


class ReleasesExist(Aspect):
    """Validate that any of the selected releases exist."""
    def __init__(self, env):
        self.env = env

    def __call__(self, context, selected):
        if selected:
            tags = TagSystem(self.env)
            req = FakeRequest(self.env)
            releases = [r.id for r, _ in tags.query(req, 'realm:wiki release')]
            if isinstance(selected, (basestring, unicode)):
                selected = [selected]
            for s in selected:
                if s not in releases:
                    hack = context.data.get('name', '') + \
                           context.data.get('type', '').title()
                    self.env.log.error(
                        "Invalid release %s selected for new hack %s" % (s, hack)
                    )
                    raise ValidationError('Selected release "%s" invalid?!'
                                          % str(s))
        return selected


class ValidTypeSelected(Aspect):
    """Validate that a valid type is selected."""
    def __init__(self, env):
        self.env = env

    def __call__(self, context, type_):
        if not (type_ and isinstance(type_, basestring) and len(type_)):
            raise ValidationError('No type selected?!')

        tags = TagSystem(self.env)
        req = FakeRequest(self.env)
        types = [r.id for r, _ in tags.query(req, 'realm:wiki type')]
        if type_ not in types:
            raise ValidationError('Selected type "%s" invalid?!' % str(type_))
        return type_


class TracHacksHandler(Component):
    """Trac-Hacks request handler."""
    implements(INavigationContributor, IRequestHandler, IRequestFilter,
               ITemplateProvider, IPermissionRequestor, ITemplateStreamFilter)

    limit = IntOption('trachacks', 'limit', 25,
        'Default maximum number of hacks to display.')
    template = Option('trachacks', 'template', 'NewHackTemplate',
        'Name of wiki page that serves as template for new hacks.')
    lock_file = Option('trachacks', 'lock_file', '/var/tmp/newhack.lock',
        'Path and name of lock file to secure new hack creation')

    path_match = re.compile(r'/(?:hacks/?(cloud|list)?|newhack)')
    title_extract = re.compile(r'=\s+([^=]*)=', re.MULTILINE | re.UNICODE)

    def __init__(self):
        # Validate form
        form = Form('content')
        form.add('name', Chain(
                 Pattern(r'[A-Z][A-Za-z0-9]+(?:[A-Z][A-Za-z0-9]+)*\Z'),
                 HackDoesntExist(self.env),
                 ),
                 'Name must be in CamelCase.')
        form.add('title', MinLength(8),
                 'Please write a few words for the description.')
        form.add('description', MinLength(16),
                 'Please write at least a sentence or two for the description.')
        form.add('installation', MinLength(16),
                 'Please write at least a sentence or two for the installation.')
        form.add('release', Chain(MinLength(1), ReleasesExist(self.env)),
                 'At least one release must be checked.',
                 path='//dd[@id="release"]', where='append')
        form.add('type', ValidTypeSelected(self.env),
                 'No type selected?!',
                 path='//dd[@id="type"]', where='append')

        self.form = form

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        context = data.get('form_context')
        if context and context.errors and req.path_info == '/newhack':
            stream |= context.inject_errors()
        return stream

    # IRequestHandler methods
    def match_request(self, req):
        #return self.path_match.match(req.path_info)
        return req.path_info == '/newhack'

    def process_request(self, req):
        data = {}
        tag_system = TagSystem(self.env)

        #match = self.path_match.match(req.path_info)
        #view = 'cloud'
        #if match.group(1):
        #    view = match.group(1)

        authz_file = self.env.config.getpath('trac', 'authz_file')
        if not authz_file:
            raise ConfigurationError(
                tag_("The configuration option %(option)s is empty or "
                     "missing.", option=builder.tt("[trac] authz_file")))

        if not os.path.exists(authz_file):
            raise ConfigurationError(
                tag_("The authz file is not found at %(path)s.",
                     path=builder.tt(authz_file)))

        # Hack types and their description
        types = []
        for category in sorted([r.id for r, _ in
                                tag_system.query(req, 'realm:wiki type')]):
            page = WikiPage(self.env, category)
            match = self.title_extract.search(page.text)
            if match:
                title = '%s' % match.group(1).strip()
            else:
                title = '%s' % category
            types.append((category, title))

        # Trac releases
        releases = natural_sort([r.id for r, _ in
                                 tag_system.query(req, 'realm:wiki release')])

        data['types'] = types
        data['releases'] = releases

        selected_releases = req.args.getlist('release') or \
                            ('0.12', '1.0', 'anyrelease')
        data['selected_releases'] = selected_releases

        hacks = self.fetch_hacks(req, data, [t[0] for t in types],
                                 selected_releases)

        add_stylesheet(req, 'tags/css/tractags.css')
        add_stylesheet(req, 'hacks/css/trachacks.css')
        add_script(req, 'hacks/js/trachacks.js')

        if req.path_info == '/newhack':
            return self.render_new(req, data, hacks)
        #else:
        #    views = ['cloud', 'list']
        #    for v in views:
        #        if v != view:
        #            args = req.args
        #            add_ctxtnav(req, builder.a(v.title(),
        #                        href=req.href.hacks(v, **args)))
        #        else:
        #            add_ctxtnav(req, v.title())
        #    if view == 'list':
        #        return self.render_list(req, data, hacks)
        #    else:
        #        return self.render_cloud(req, data, hacks)

    # IRequestHandler methods
    def pre_process_request(self, req, handler):
        from trac.wiki.web_ui import WikiModule
        if isinstance(handler, WikiModule):
            path = req.path_info
            args = req.args

            if not (req.method == 'GET'):
                self.env.log.debug('Hacks: no notice: no GET request')
            elif not (path.startswith('/wiki/') or path == '/wiki'):
                self.env.log.debug('Hacks: no notice: not a wiki path')
            elif not 'hack' in args:
                self.env.log.debug('Hacks: no notice: hack= missing')
            elif args['hack'] != 'created':
                self.env.log.debug('Hacks: no notice: hack=%s' % args['hack'])
            else:
                self.env.log.debug('Hacks: notice added')
                add_notice(req, 'Your hack has been created successfully.')
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            ticket = data['ticket']
            component = ticket['component']
            if ticket.exists and component:
                wiki_resource = Resource('wiki', component)
                if resource_exists(self.env, wiki_resource):
                    add_ctxtnav(req, component, req.href.wiki(component),
                                _("Go to Project's Wiki Page"))
                else:
                    self.env.log.warn('No wiki page for component "%s"'
                                      % component)
        return template, data, content_type

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        #if req.path_info == '/newhack':
        return 'newhack'
        #else:
        #    return 'hacks'

    def get_navigation_items(self, req):
        #yield ('mainnav', 'hacks',
        #        builder.a('View Hacks', href=req.href.hacks(), accesskey='H'))
        if 'HACK_CREATE' in req.perm:
            yield ('mainnav', 'newhack',
                   builder.a('New Hack', href=req.href.newhack()))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        htdocs = resource_filename(__name__, 'htdocs')
        return [('hacks', htdocs), ('newhack', htdocs)]

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['HACK_CREATE']

    # Internal methods
    def render_new(self, req, data, hacks):
        req.perm.require('HACK_CREATE')

        tag_system = TagSystem(self.env)

        hacks = list(hacks)
        hack_names = set(r[2].id for r in hacks)
        users = set(u.id for u, _ in tag_system.query(req, 'realm:wiki user'))
        exclude = \
            hack_names.union(users).union(data['types']).union(data['releases'])

        cloud = {}

        for votes, rank, resource, tags, title in hacks:
            for tag in tags:
                if tag in exclude:
                    continue
                try:
                    cloud[tag] += 1
                except KeyError:
                    cloud[tag] = 1

        # Pick the top 25 tags + a random sample of 10 from the rest.
        cloud = sorted(cloud.items(), key=lambda i: -i[1])
        remainder = cloud[25:]
        cloud = dict(cloud[:25] +
                     random.sample(remainder, min(10, len(remainder))))

        # Render the cloud
        min_px = 8
        max_px = 20

        def cloud_renderer(tag, count, percent):
            self.env.log.debug("cloud: %s = %2.2f%%" % (tag, percent * 100))
            return builder.a(tag, href='#', style='font-size: %ipx' %
                             int(min_px + percent * (max_px - min_px)))

        data['cloud'] = TagWikiMacros(self.env). \
                        render_cloud(req, cloud, cloud_renderer)

        add_script(req, 'common/js/wikitoolbar.js')
        add_script(req, 'common/js/folding.js')

        data['focus'] = 'name'

        # Populate data with form submission
        if req.method == 'POST' \
                and 'create' in req.args or 'preview' in req.args:
            data.update(req.args)

            context = self.form.validate(data)
            data['form_context'] = context

            repos = self.env.get_repository()

            vars = {}
            vars['OWNER'] = req.authname
            vars['WIKINAME'] = get_page_name(data['name'], data.get('type', ''))
            vars['TYPE'] = data.setdefault('type', 'plugin')
            vars['TITLE'] = data.setdefault('title', 'No title available')
            vars['LCNAME'] = vars['WIKINAME'].lower()
            vars['SOURCEURL'] = repos.get_path_url(vars['LCNAME'], None) or \
                                'http://localhost/svn/' + vars['LCNAME']
            vars['DESCRIPTION'] = data.setdefault('description',
                                                  'No description available')
            vars['INSTALLATION'] = data.setdefault('installation',
                                                   'No installation available')

            if 'create' in req.args and not context.errors:
                success, message = self.create_hack(req, data, vars)
                if success:
                    target = '%s?%s' % \
                        (req.href.wiki(vars['WIKINAME']), 'hack=created')
                    req.redirect(target)
                    raise RequestDone
                else:
                    add_warning(req, message)
            elif 'preview' in req.args and not context.errors:
                page = WikiPage(self.env, self.template)
                if not page.exists:
                    raise TracError('New hack template %s does not exist.' %
                                    self.template)
                template = Template(page.text).substitute(vars)
                template = re.sub(r'\[\[ChangeLog[^\]]*\]\]',
                                  'No changes yet', template)
                add_stylesheet(req, 'common/css/wiki.css')
                data['page_preview'] = wiki_to_html(template, self.env, req)
        else:
            data['form_context'] = None
            data['type'] = 'plugin'
            data['release'] = ['0.11']

        return 'hacks_new.html', data, None

    def create_hack(self, req, data, vars):
        import fcntl

        messages = []
        created = False
        have_lock = False
        lock_file = open(self.lock_file, "w")
        try:
            rv = fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if rv:
                raise TracError('Failed to acquire lock, error: %i' % rv)
            have_lock = True
        except IOError:
            messages.append(
                'A hack is currently being created by another user. '
                'Please wait a few seconds, then click the "Create hack" '
                'button again.'
            )

        if have_lock:
            steps_done = []
            try:
                page_name = vars['WIKINAME']
                hack_path = vars['LCNAME']
                selected_releases = data['selected_releases']

                # Step 1: create repository paths
                self._create_repository_paths(req, page_name, hack_path,
                                              selected_releases)
                steps_done.append('repository')

                # Step 2: Add permissions
                from svnauthz.model import User, Path, PathAcl

                authz_file = self.config.getpath('trac', 'authz_file')
                authz = AuthzFileReader().read(authz_file)

                svn_path_acl = PathAcl(User(req.authname), r=True, w=True)
                authz.add_path(Path("/%s" % hack_path, acls=[svn_path_acl, ]))
                AuthzFileWriter().write(authz_file, authz)
                steps_done.append('permissions')

                # Step 3: Add component
                component = TicketComponent(self.env)
                component.name = page_name
                component.owner = req.authname
                component.insert()
                steps_done.append('component')

                # Step 4: Create wiki page
                template_page = WikiPage(self.env, self.template)
                page = WikiPage(self.env, page_name)
                page.text = Template(template_page.text).substitute(vars)
                page.save(req.authname, 'New hack %s, created by %s'
                                        % (page_name, req.authname), '0.0.0.0')
                steps_done.append('wiki')

                # Step 5: Tag the new wiki page
                res = Resource('wiki', page_name)
                tags = sorted(set(data['tags'].split() + selected_releases + \
                                  [data['type'], req.authname]))
                TagSystem(self.env).set_tags(req, res, tags)
                steps_done.append('tags')

                rv = fcntl.flock(lock_file, fcntl.LOCK_UN)
                created = True
            except Exception, e:
                try:
                    if 'tags' in steps_done:
                        res = Resource('wiki', page_name)
                        tags = data['tags'].split() + selected_releases
                        TagSystem(self.env).delete_tags(req, res, tags)
                    if 'wiki' in steps_done:
                        WikiPage(self.env, page_name).delete()
                    if 'component' in steps_done:
                        TicketComponent(self.env, page_name).delete()
                    if 'permissions' in steps_done:
                        authz_file = self.env.config.getpath('trac', 'authz_file')
                        authz = AuthzFileReader().read(authz_file)
                        authz.del_path(Path("/%s" % hack_path))
                        AuthzFileWriter().write(authz_file, authz)
                    # TODO: rollback subversion path creation
                    rv = fcntl.flock(lock_file, fcntl.LOCK_UN)
                except:
                    self.env.log.error("Rollback failed")
                    rv = fcntl.flock(lock_file, fcntl.LOCK_UN)
                self.env.log.error(e, exc_info=True)
                raise TracError(str(e))
        return created, messages

    def _create_repository_paths(self, req, page_name, hack_path,
                                 selected_releases):
        from subprocess import Popen, PIPE

        env = os.environ.copy()
        env['LC_ALL'] = env['LANG'] = 'en_US.UTF-8'
        repos = self.env.get_repository()
        svn_path = ('file://%s' % repos.params['dir']).rstrip('/')
        paths = ['%s/%s' % (svn_path, hack_path)]
        paths.extend('%s/%s/%s' % (svn_path, hack_path, release)
                     for release in selected_releases
                     if release != 'anyrelease')
        message = 'New hack %s, created by %s' % (page_name, req.authname)
        args = ['/usr/bin/svn', 'mkdir', '-q', '--username', req.authname,
                '--config-dir', _SVN_CONFIG_DIR, '--non-interactive',
                '-m', message, '--'] + paths
        saved_umask = os.umask(002)
        try:
            proc = Popen(args, stdout=PIPE, stderr=PIPE, close_fds=True,
                         env=env)
        finally:
            os.umask(saved_umask)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception('Failed to create Subversion paths:\n%s%s' %
                            (stdout, stderr))

    def render_list(self, req, data, hacks):
        ul = builder.ul()
        for votes, rank, resource, tags, title \
                in sorted(hacks, key=lambda h: h[2].id):
            li = builder.li(builder.a(resource.id,
                                      href=req.href.wiki(resource.id)),
                            ' - ', title)
            ul(li)
        data['body'] = ul
        # TODO Top-n + sample
        return 'hacks_view.html', data, None

    def render_cloud(self, req, data, hacks):
        by_name = dict([(r[2].id, r) for r in hacks])

        def link_renderer(tag, count, percent):
            votes, rank, resource, tags, title = by_name[tag]
            href = req.href.wiki(resource.id)
            font_size = 10.0 + (percent * 20.0)
            colour = 128.0 - (percent * 128.0)
            colour = '#%02x%02x%02x' % ((colour,) * 3)
            a = builder.a(tag, rel='tag', title=title, href=href, class_='tag',
                          style='font-size: %ipx; color: %s'
                                % (font_size, colour))
            return a

        # TODO Top-n + sample
        cloud_hacks = dict([(hack[2].id, hack[0]) for hack in hacks])
        data['body'] = TagWikiMacros(self.env).render_cloud(req, cloud_hacks,
                                                            link_renderer)

        return 'hacks_view.html', data, None

    def fetch_hacks(self, req, data, types, releases):
        """Return a list of hacks in the form

        [votes, rank, resource, tags, title]
        """
        tag_system = TagSystem(self.env)
        vote_system = VoteSystem(self.env)

        query = 'realm:wiki (%s) (%s)' % \
                (' or '.join(releases), ' or '.join(types))
        self.env.log.debug(query)
        tagged = tag_system.query(req, query)

        # Limit
        try:
            limit = int(req.args.get('limit', self.limit))
            data['limit_message'] = 'top %s' % limit
        except ValueError:
            data['limit_message'] = 'all'
            limit = 9999
        data['limit'] = limit

        # Query
        q = req.args.get('q', '')
        data['query'] = q
        query = Query(q.lower())

        # Build hacks list
        hacks = []
        for resource, tags in tagged:
            page = WikiPage(self.env, resource.id)
            if q:
                text = page.name.lower() + page.text.lower() + ' '.join(tags)
                if not query(text):
                    continue
            _, count, _ = vote_system.get_vote_counts(resource)
            match = self.title_extract.search(page.text)
            count_string = pluralise(count, 'vote')
            if match:
                title = '%s (%s)' % (match.group(1).strip(), count_string)
            else:
                title = '%s' % count_string
            hacks.append([count, None, resource, tags, title])

        # Rank
        total_hack_count = len(hacks)
        hacks = sorted(hacks, key=lambda i: -i[0])
        remainder = hacks[limit:]
        hacks = hacks[:limit] + random.sample(remainder,
                                              min(limit, len(remainder)))

        # Navigation
        #if len(hacks) >= limit:
        #    add_ctxtnav(req, builder.a('More', href='?action=more'))
        #    limit = len(hacks)
        #    data['limit'] = data['limit_message'] = limit
        #else:
        #    add_ctxtnav(req, 'More')
        #if q or limit != self.limit:
        #    add_ctxtnav(req, builder.a('Default', href='?action=default'))
        #else:
        #    add_ctxtnav(req, 'Default')
        #if total_hack_count > limit:
        #    add_ctxtnav(req, builder.a('All', href='?action=all'))
        #else:
        #    add_ctxtnav(req, 'All')
        #if limit > 10:
        #    limit = min(limit, len(hacks))
        #    add_ctxtnav(req, builder.a('Less', href='?action=less'))
        #else:
        #    add_ctxtnav(req, 'Less')
        #for i, hack in enumerate(hacks):
        #    hack[1] = i
        return hacks


USER_PAGE_TEMPLATE = """\
= %(user)s

[[ListTagged(%(user)s)]]
"""


class TracHacksHtPasswdStore(HtPasswdStore):
    """Do some basic validation on new users and create a new user page."""
    implements(IPasswordStore, IAccountChangeListener)

    # IPasswordStore
    def set_password(self, user, password):
        perm = PermissionSystem(self.env)
        all_perms = [p[0] for p in perm.get_all_permissions()]
        if user in all_perms:
            raise TracError('%s is a reserved name that can not be registered.'
                            % user)

        needles = [':', '[', ']']
        for needle in needles:
            if needle in user:
                raise TracError('Character "%s" may not be used in user names.'
                                % needle)

        if len(user) < 3:
            raise TracError("User name must be at least 3 characters long.")
        if not re.match(r'^\w+$', user):
            raise TracError("User name must consist only of alpha-numeric "
                            "characters.")
        if user.isupper():
            raise TracError("User name must not consist of upper-case "
                            "characters only.")

        if WikiPage(self.env, user).exists:
            raise TracError('wiki page "%s" already exists' % user)

        return HtPasswdStore.set_password(self, user, password)

    def delete_user(self, user):
        HtPasswdStore.delete_user(self, user)

    # IAccountChangeListener
    def user_created(self, user, password):
        page = WikiPage(self.env, user)

        req = FakeRequest(self.env, user)
        tag_system = TagSystem(self.env)
        tag_system.add_tags(req, page.resource, ('user', ))

        page.text = USER_PAGE_TEMPLATE % {'user': user}
        page.save(user, 'New user //%s// registered' % user, None)

        self.env.log.debug("New user %s registered" % user)

    def user_password_changed(self, user, password):
        pass

    def user_deleted(self, user):
        pass

    def user_password_reset(self, user, email, password):
        pass

    def user_email_verification_requested(self, user, token):
        pass
