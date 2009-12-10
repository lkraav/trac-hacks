# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
import random
from trac.core import *
from trac.config import *
from trac.perm import IPermissionRequestor, PermissionCache
from trac.web.chrome import Chrome
from trac.resource import Resource, render_resource_link
from acct_mgr.htfile import HtPasswdStore
from acct_mgr.api import IPasswordStore, IAccountChangeListener
from trac.wiki.formatter import wiki_to_oneliner
from trac.wiki.model import WikiPage
from trac.wiki.macros import WikiMacroBase
from trac.util.compat import sorted
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet, add_script, add_ctxtnav
from tractags.api import TagSystem
from tractags.macros import render_cloud
from tractags.query import Query
from tracvote import VoteSystem
from genshi.builder import tag as builder
from genshi.filters.transform import Transformer
from trachacks.validate import *


def pluralise(n, word):
    """Return a (naively) pluralised phrase from a count and a singular
    word."""
    if n == 0:
        return 'No %ss' % word
    elif n == 1:
        return '%i %s' % (n, word)
    else:
        return '%i %ss' % (n, word)


def natural_sort(l):
  """Sort the given list in the way that humans expect."""
  convert = lambda text: int(text) if text.isdigit() else text
  alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
  return sorted(l, key=alphanum_key)


class HackDoesntExist(Aspect):
    """Validate that the hack does not exist."""
    def __init__(self, env):
        self.env = env

    def __call__(self, context, name):
        page_name = name + context.data.get('type', '').title()
        if WikiPage(self.env, page_name).exists or WikiPage(self.env, name).exists:
            raise ValidationError('Page already exists.')
        return name


class TracHacksHandler(Component):
    """Trac-Hacks request handler."""
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
               IPermissionRequestor, ITemplateStreamFilter)

    limit = IntOption('trachacks', 'limit', 25,
        'Default maximum number of hacks to display.')

    path_match = re.compile(r'/hacks/?(new|cloud|list)?')
    title_extract = re.compile(r'=\s+([^=]*)=', re.MULTILINE | re.UNICODE)

    def __init__(self):
        # Validate form
        form = Form('content')
        form.add('name', Chain(
                Pattern(r'[A-Z][A-Za-z0-9]+(?:[A-Z][A-Za-z0-9]+)*'),
                HackDoesntExist(self.env),
                ),
                 'Name must be in CamelCase.')
        form.add('title', MinLength(8),
                 'Please write a few words for the description.')
        form.add('description', MinLength(16),
                 'Please write at least a sentence or two for the description.')
        form.add('release', MinLength(1), 'At least one release must be checked.',
                 path='//dd[@id="release"]', where='append')
        self.form = form

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        context = data.get('form_context')
        if context and context.errors and req.path_info == '/hacks/new':
            stream |= context.inject_errors()
        return stream

    # IRequestHandler methods

    def match_request(self, req):
        return self.path_match.match(req.path_info)

    def process_request(self, req):
        data = {}
        tag_system = TagSystem(self.env)

        match = self.path_match.match(req.path_info)
        view = 'cloud'
        if match.group(1):
            view = match.group(1)

        # Hack types
        types = [r.id for r, _ in tag_system.query(req, 'realm:wiki type')]
        # Trac releases
        releases = natural_sort([r.id for r, _ in
                                 tag_system.query(req, 'realm:wiki release')])

        data['types'] = types
        data['releases'] = releases

        selected_releases = req.args.get('release', set(['0.10', '0.11', 'anyrelease']))

        data['selected_releases'] = selected_releases

        hacks = self.fetch_hacks(req, data, types, selected_releases)

        add_stylesheet(req, 'tags/css/tractags.css')
        add_stylesheet(req, 'hacks/css/trachacks.css')
        add_script(req, 'hacks/js/trachacks.js')

        views = ['cloud', 'list', 'new']
        for v in views:
            if v != view:
                if v != 'new':
                    args = req.args
                else:
                    args = {}
                add_ctxtnav(req, builder.a(v.title(),
                            href=req.href.hacks(v, **args)))
            else:
                add_ctxtnav(req, v.title())
        if view == 'list':
            return self.render_list(req, data, hacks)
        elif view == 'new':
            return self.render_new(req, data, hacks)
        return self.render_cloud(req, data, hacks)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'hacks'

    def get_navigation_items(self, req):
        yield ('mainnav', 'hacks',
                builder.a('Hacks', href=req.href.hacks(), accesskey='H'))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('hacks', resource_filename(__name__, 'htdocs'))]

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
        exclude = hack_names.union(users).union(data['types']).union(data['releases'])

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
            self.env.log.debug(percent)
            return builder.a(tag, href='#', style='font-size: %ipx' %
                             int(min_px + percent * (max_px - min_px)))

        data['cloud'] = render_cloud(self.env, req, cloud, cloud_renderer)

        add_script(req, 'common/js/wikitoolbar.js')
        add_script(req, 'common/js/folding.js')

        data['focus'] = 'name'

        # Populate data with form submission
        if req.method == 'POST' and 'create' in req.args or 'preview' in req.args:
            data.update(req.args)

            context = self.form.validate(data)
            data['form_context'] = context
        else:
            data['form_context'] = None
            data['type'] = 'plugin'
            data['release'] = ['0.11']

        self.env.log.debug('MUPPETS AHOY')
        return 'hacks_new.html', data, None

    def render_list(self, req, data, hacks):
        ul = builder.ul()
        for votes, rank, resource, tags, title in sorted(hacks, key=lambda h: h[2].id):
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
                style='font-size: %ipx; color: %s' % (font_size, colour))
            return a

        # TODO Top-n + sample
        cloud_hacks = dict([(hack[2].id, hack[0]) for hack in hacks])
        data['body'] = render_cloud(self.env, req, cloud_hacks, link_renderer)

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
        if len(hacks) >= limit:
            add_ctxtnav(req, builder.a('More', href='?action=more'))
            limit = len(hacks)
            data['limit'] = data['limit_message'] = limit
        else:
            add_ctxtnav(req, 'More')
        if q or limit != self.limit:
            add_ctxtnav(req, builder.a('Default', href='?action=default'))
        else:
            add_ctxtnav(req, 'Default')
        if total_hack_count > limit:
            add_ctxtnav(req, builder.a('All', href='?action=all'))
        else:
            add_ctxtnav(req, 'All')
        if limit > 10:
            limit = min(limit, len(hacks))
            add_ctxtnav(req, builder.a('Less', href='?action=less'))
        else:
            add_ctxtnav(req, 'Less')
        for i, hack in enumerate(hacks):
            hack[1] = i
        return hacks



class TracHacksHtPasswdStore(HtPasswdStore):
    """Do some basic validation on new users and create a new user page."""
    implements(IPasswordStore, IAccountChangeListener)

    # IPasswordStore
    def set_password(self, user, password):
        if len(user) < 3:
            raise TracError('user name must be at least 3 characters long')
        if not re.match(r'^\w+$', user):
            raise TracError('user name must consist only of alpha-numeric characters')

        db = self.env.get_db_cnx()
        page = WikiPage(self.env, user, db=db)
        if page.exists:
            raise TracError('wiki page "%s" already exists' % user)

        return HtPasswdStore.set_password(self, user, password)

    def delete_user(self, user):
        HtPasswdStore.delete_user(self, user)

    # IAccountChangeListener
    def user_created(self, user, password):
        class FakeRequest(object):
            def __init__(self, env, authname):
                self.perm = PermissionCache(env, authname)

        req = FakeRequest(self.env, user)
        resource = Resource('wiki', user)
        tag_system = TagSystem(self.env)
        tag_system.add_tags(req, resource, ['user',])

        db = self.env.get_db_cnx()
        page = WikiPage(self.env, user, db=db)
        page.text = '''= %(user)s =\n\n[[ListTagged(%(user)s)]]\n''' % {'user' : user}
        page.save(user, 'New user %s registered' % user, None)

        self.env.log.debug("New user %s registered" % user)

    def user_password_changed(self, user, password):
        pass

    def user_deleted(self, user):
        pass


class ListHacksMacro(WikiMacroBase):
    """ List of meta types """
    title_extract = re.compile(r'=\s+([^=]*)=', re.MULTILINE | re.UNICODE)

    def expand_macro(self, formatter, name, content):
        req = formatter.req
        tag_system = TagSystem(self.env)
        categories = sorted([r.id for r, _ in
                             tag_system.query(req, 'realm:wiki type')])
        releases = natural_sort([r.id for r, _ in
                                 tag_system.query(req, 'realm:wiki release')])

        if 'update_th_filter' in req.args:
            show_releases = req.args.get('release', ['0.11'])
            if isinstance(show_releases, basestring):
                show_releases = [show_releases]
            req.session['th_release_filter'] = ','.join(show_releases)
        else:
            show_releases = req.session.get('th_release_filter', '0.11').split(',')

        style = "text-align:right; padding-top:1em; margin-right:5em;"
        form = builder.form('\n', style=style, method="get")

        style = "font-size:xx-small;"
        span = builder.span("Show hacks for releases:", style=style)

        for version in releases:
            inp = builder.input(version, type_="checkbox", name="release",
                                value=version)
            if version in show_releases:
                inp(checked="checked")
            span(inp, '\n')

        style = "font-size:xx-small; padding:0; border:solid 1px black;"
        span(builder.input(name="update_th_filter", type_="submit",
                           style=style, value="Update"), '\n')
        form('\n', span, '\n')

        output = form + '\n'

        def link(resource):
            return render_resource_link(self.env, formatter.context,
                                        resource, 'compact')

        for category in categories:
            page = WikiPage(self.env, category)
            match = self.title_extract.search(page.text)
            if match:
                title = '%s' % match.group(1).strip()
            else:
                title = '%s' % category

            style = "padding:1em; margin:0em 5em 2em 5em; border:1px solid #999;"
            fieldset = builder.fieldset('\n', style=style)
            legend = builder.legend(style="color: #999;")
            legend(builder.a(title, href=self.env.href.wiki(category)))
            fieldset(legend, '\n')

            ul = builder.ul('\n', class_="listtagged")
            query = 'realm:wiki (%s) %s' % \
                (' or '.join(show_releases), category)

            lines = 0
            for resource, tags in tag_system.query(req, query):
                lines += 1
                li = builder.li(link(resource), ': ')

                page = WikiPage(self.env, resource)
                match = self.title_extract.search(page.text)
                description = "''no description available''"
                if match:
                    if match.group(1):
                        description = match.group(1).strip()

                li(wiki_to_oneliner(description, self.env, req=req))
                if tags:
                    rendered_tags = [ link(resource('tag', tag))
                                      for tag in natural_sort(tags)
                                      if tag != category ]
                    span = builder.span(style="font-size:xx-small;")
                    span(' (tags: ', rendered_tags[0],
                       [(', ', tag) for tag in rendered_tags[1:]], ')')
                    li(span)
                ul(li, '\n')

            if lines:
                fieldset(ul, '\n')
            else:
                fieldset(builder.p(builder.em("No results for your selection.")), '\n')

            output += fieldset + '\n'
        return output
