# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from __future__ import with_statement

from pkg_resources import parse_version, resource_filename

from trac import __version__
from trac.core import Component, TracError, implements
from trac.resource import (
    Resource, ResourceNotFound, get_resource_description, get_resource_url)
from trac.ticket.api import TicketSystem
from trac.util.html import Markup, tag
from trac.util.text import shorten_line, to_unicode
from trac.util.translation import dgettext
from trac.versioncontrol.api import RepositoryManager
from trac.versioncontrol.cache import CachedRepository
from trac.web.chrome import Chrome, add_script, add_script_data, web_context
from trac.wiki.model import WikiPage

try:
    from trac.web.chrome import chrome_resource_path
except ImportError:
    from trac.web.chrome import _chrome_resource_path as chrome_resource_path

from tracbacklink.api import _


_parsed_version = parse_version(__version__)

if _parsed_version >= parse_version('1.4'):
    _use_jinja2 = True
elif _parsed_version >= parse_version('1.3'):
    _use_jinja2 = hasattr(Chrome, 'jenv')
else:
    _use_jinja2 = False


IRequestFilter = ITemplateProvider = ITemplateStreamFilter = None

if _use_jinja2:
    from trac.web.api import IRequestFilter
    from trac.web.chrome import ITemplateProvider
else:
    from genshi.filters.transform import Transformer
    from genshi.path import Path
    from trac.web.chrome import ITemplateStreamFilter

    class PathOnce(Path):

        def test(self, ignore_context=False):
            def test_once(event, namespaces, variables, updateonly=False):
                if match[0] is True:
                    return None
                rv = test(event, namespaces, variables, updateonly=updateonly)
                if rv is True:
                    match[0] = True
                return rv

            match = [False]
            test = super(PathOnce, self).test(ignore_context=ignore_context)
            return test_once

    class TransformerOnce(Transformer):

        def __init__(self, path='.'):
            super(TransformerOnce, self).__init__(PathOnce(path))


def dgettext_messages(msgid, **kwargs):
    return dgettext('messages', msgid, **kwargs)


class TracBackLinkModule(Component):

    implements(*filter(None, (IRequestFilter, ITemplateProvider,
                              ITemplateStreamFilter)))

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, metadata):
        if template == 'ticket.html':
            type_ = 'ticket'
            key = 'ticket'
        elif template == 'wiki_view.html':
            type_ = 'wiki'
            key = 'page'
        elif template == 'milestone_view.html':
            type_ = 'milestone'
            key = 'milestone'
        else:
            type_ = None
        content = self._get_backlinks_content(req, data.get(key)) \
                  if type_ else None
        if content is not None:
            script_data = {'type': type_, 'content': content}
            add_script_data(req, tracbacklink=script_data)
            add_script(req, 'tracbacklink/base.js')
            # tracbacklink/base.js should be added before common/js/wiki.js
            if type_ == 'wiki':
                href = chrome_resource_path(req, 'common/js/wiki.js')
                scripts = req.chrome['scripts']
                for idx, script in enumerate(scripts):
                    if script['attrs']['src'] == href:
                        scripts.insert(idx, scripts.pop())
                        break
                else:
                    raise RuntimeError('Unable to find %s in '
                                       'web.chrome["scripts"]' % href)
        return template, data, metadata

    # ITemplateProvider methods

    _htdocs_dir = resource_filename(__name__, 'htdocs')

    def get_htdocs_dirs(self):
        yield 'tracbacklink', self._htdocs_dir

    def get_templates_dirs(self):
        return ()

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            key = 'ticket'
            xfmr = TransformerOnce('//div[@id="ticket"]').after
        elif filename == 'wiki_view.html':
            key = 'page'
            xfmr = TransformerOnce('//div[@id="content"]'
                                   '//div[@class="wikipage searchable"]').after
        elif filename == 'milestone_view.html':
            key = 'milestone'
            xfmr = TransformerOnce('//div[@id="attachments" or @id="help"]') \
                   .before
        else:
            return stream
        content = self._get_backlinks_content(req, data.get(key))
        if content is not None:
            stream |= xfmr(tag(content))
        return stream

    # Internal methods

    def _get_backlinks_content(self, req, model):
        if model is None or not model.exists:
            return None
        resource = model.resource
        sources = self._get_backlink_sources(resource)
        rendered = self._render_backlinks(req, sources)
        if not rendered:
            return None
        keys = self._sort_backlink_keys(rendered, resource.realm)
        header = tag.h3(_("Back Links"),
                        tag.span('(%d)' % len(rendered), class_='trac-count'),
                        class_='foldable')
        body = tag.div(tag.ul(tag.li(tag.div(rendered[key])) for key in keys),
                       class_='backlinks')
        contents = tag.div(header, body, id='backlinks',
                           class_='collapsed noprint')
        return Markup(contents)

    def _get_backlink_sources(self, resource):
        def normalize_id(realm, id_):
            if realm in ('ticket', 'comment') and \
                    isinstance(id_, basestring) and id_.isdigit():
                id_ = int(id_)
            return id_

        sources = {}
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute("""\
                SELECT src_realm, src_id, src_parent_realm, src_parent_id
                FROM backlink
                WHERE ref_realm=%s AND ref_id=%s OR
                      ref_parent_realm=%s AND ref_parent_id=%s
                ORDER BY time
                """, (resource.realm, to_unicode(resource.id)) * 2)
            for realm, id_, parent_realm, parent_id in cursor:
                id_ = normalize_id(realm, id_)
                parent_id = normalize_id(parent_realm, parent_id)
                key = (parent_realm, parent_id) \
                      if parent_realm else (realm, id_)
                sources.setdefault(key, {})
                if parent_realm:
                    sources[key].setdefault(realm, []).append(id_)
        for values in sources.itervalues():
            for ids in values.itervalues():
                ids.sort()

        return sources

    def _render_backlinks(self, req, sources):
        rendered = {}
        for f in (self._render_ticket_backlinks,
                  self._render_wiki_backlinks,
                  self._render_repository_backlinks,
                  self._render_milestone_backlinks):
            rendered.update(f(req, sources))
        return rendered

    def _render_wiki_backlinks(self, req, sources):
        realm = 'wiki'
        href = req.href
        names = dict((key[1], value) for key, value in sources.iteritems()
                                     if key[0] == realm)
        for name in sorted(names):
            try:
                page = WikiPage(self.env, name)
            except ResourceNotFound:
                continue
            resource = page.resource
            if 'WIKI_VIEW' not in req.perm(resource):
                continue
            rendered = tag(tag.a('wiki:',
                                 self._get_resource_description(resource),
                                 href=self._get_resource_url(resource, href),
                                 title=self._shorten_line(page.comment)))
            child_ids = names[name]
            if 'comment' in child_ids:
                versions = [int(version) for version in child_ids['comment']]
                versions = ','.join(str(version) for version in versions
                                                 if version != page.version)
                if versions:
                    rows = self.env.db_query("""\
                        SELECT version, comment FROM wiki
                        WHERE name=%%s AND version IN (%s)
                        ORDER BY version
                        """ % versions, (name,))
                else:
                    rows = ()
                for idx, (version, comment) in enumerate(rows):
                    version_resource = resource(version=version)
                    url = self._get_resource_url(version_resource, href)
                    rendered(', ' if idx else u' \u2013 ',
                             tag.a('@%d' % version, href=url,
                                   title=self._shorten_line(comment)))
            if 'attachment' in child_ids:
                rendered(self._render_attachment_backlinks(
                    req, child_ids['attachment'], realm, name))
            yield (realm, name), rendered

    def _render_ticket_backlinks(self, req, sources):
        realm = 'ticket'
        tktids = dict((key[1], value)
                       for key, value in sources.iteritems()
                       if key[0] == realm and
                            'TICKET_VIEW' in req.perm(realm, key[1]))
        if not tktids:
            return
        tktsys = TicketSystem(self.env)
        href = req.href
        rows = self.env.db_query("""\
            SELECT id,type,summary,status,resolution FROM ticket
            WHERE id IN (%s)
            """ % ','.join(str(int(tktid)) for tktid in tktids))
        for tktid, type_, summary, status, resolution in rows:
            url = self._get_resource_url(Resource(realm, tktid), href)
            title = tktsys.format_summary(summary, status, resolution,
                                          type_)
            rendered = tag(tag.a('#%s' % tktid, class_='%s ticket' % status,
                                 title=title, href=url),
                           ' ', summary)
            child_ids = tktids[tktid]
            cnums = child_ids.get('comment')
            if cnums:
                comments = dict((cnum.split('.')[-1], comment)
                                for cnum, comment in self.env.db_query("""\
                        SELECT oldvalue, newvalue FROM ticket_change
                        WHERE ticket=%s AND field='comment' AND newvalue!=''
                        ORDER BY time""", (tktid,)))
                for idx, cnum in enumerate(cnums):
                    cnum = unicode(cnum)
                    title = self._shorten_line(comments.get(cnum))
                    rendered(', ' if idx else u' \u2013 ',
                             tag.a(None if idx else 'comment:', cnum,
                                   href=url + '#comment:' + cnum, title=title))
            if 'attachment' in child_ids:
                rendered(self._render_attachment_backlinks(
                    req, child_ids['attachment'], realm, tktid))
            yield (realm, tktid), rendered

    def _render_milestone_backlinks(self, req, sources):
        return self._render_general_backlinks(req, sources, 'milestone',
                                              'MILESTONE_VIEW')

    def _render_repository_backlinks(self, req, sources):
        revs = dict((key[1], value.get('changeset', ()))
                     for key, value in sources.iteritems()
                     if key[0] == 'repository')
        if not revs:
            return
        manager = RepositoryManager(self.env)
        repos_map = {}
        for reponame in revs:
            if reponame in repos_map:
                repos = repos_map[reponame]
            else:
                try:
                    repos = manager.get_repository(reponame)
                except TracError:
                    repos = None
                repos_map[reponame] = repos
            if not repos:
                continue
            context = web_context(req, 'source', '/', parent=repos.resource)
            if not repos.is_viewable(context.perm):
                continue
            rendered = tag(tag.a('source:',
                                 reponame or dgettext_messages("(default)"),
                                 href=req.href('browser', reponame or None)))
            f = self._render_cached_cset_backlinks \
                if isinstance(repos, CachedRepository) else \
                self._render_normal_cset_backlinks
            for idx, item in enumerate(f(req, context, repos, revs[reponame])):
                rendered(' ' if idx else u' \u2013 ', item)
            yield ('repository', reponame), rendered

    def _render_cached_cset_backlinks(self, req, context, repos, revs):
        reponame = repos.reponame
        child_res = repos.resource.child
        href = req.href.changeset
        for srev, message, time in self.env.db_query("""\
                SELECT rev, message, time FROM revision
                WHERE repos=%%s AND rev IN (%s)
                """ % ','.join(('%s',) * len(revs)),
                [repos.id] + revs):
            rev = repos.rev_db(srev)
            if 'CHANGESET_VIEW' not in req.perm(child_res('changeset', rev)):
                continue
            anchor = tag.a('[%s]' % self._display_rev(repos, rev),
                           href=href(rev, reponame or None),
                           title=self._shorten_line(message))
            yield anchor

    def _render_normal_cset_backlinks(self, req, context, repos, revs):
        reponame = repos.reponame
        href = req.href.changeset
        for rev in revs:
            cset = repos.get_changeset(rev)
            if not cset.is_viewable(req.perm):
                continue
            anchor = tag.a('[%s]' % self._display_rev(repos, rev),
                           href=href(cset.rev, reponame or None),
                           title=self._shorten_line(cset.message))
            yield anchor

    def _render_general_backlinks(self, req, sources, realm, action):
        for realm_, name in sources:
            if realm_ != realm:
                continue
            resource = Resource(realm, name)
            if action not in req.perm(resource):
                continue
            url = self._get_resource_url(resource, req.href)
            rendered = tag(tag.a(self._get_resource_description(resource),
                                 href=url))
            child_ids = sources[(realm, name)]
            if 'attachment' in child_ids:
                rendered(self._render_attachment_backlinks(
                    req, child_ids['attachment'], realm, name))
            yield (realm, name), rendered

    def _render_attachment_backlinks(self, req, filenames, realm, id_):
        descriptions = dict(self.env.db_query("""\
            SELECT filename, description
            FROM attachment
            WHERE type=%s AND id=%s""", (realm, id_)))
        for idx, filename in enumerate(filenames):
            title = self._shorten_line(descriptions.get(filename))
            url = req.href('attachment', realm, id_, filename)
            yield (', ' if idx else u' \u2013 ',
                   tag.a(None if idx else 'attachment:',
                         filename, href=url, title=title))

    def _display_rev(self, repos, rev):
        if isinstance(rev, basestring):
            klass = repos.__class__.__name__
            if 'Git' in klass:
                rev = rev[:7]
            elif 'Mercurial' in klass:
                rev = rev[:12]
        else:
            rev = unicode(rev)
        return rev

    def _get_resource_url(self, resource, href):
        return get_resource_url(self.env, resource, href)

    def _get_resource_description(self, resource):
        return get_resource_description(self.env, resource)

    def _shorten_line(self, message):
        return shorten_line(message) if (message or '').strip() else None

    def _sort_backlink_keys(self, keys, realm):
        return sorted(keys, key=lambda k: (0 if realm == k[0] else 1,) + k)
