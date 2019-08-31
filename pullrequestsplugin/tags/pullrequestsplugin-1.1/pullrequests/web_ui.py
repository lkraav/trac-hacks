# -*- coding: utf-8 -*-

import re

from datetime import datetime

from genshi.builder import tag

from trac.admin import *
from trac.config import ListOption
from trac.core import *
from trac.resource import Resource
from trac.ticket.api import ITicketManipulator
from trac.util import get_reporter_id
from trac.util.datefmt import format_datetime, utc
from trac.util.presentation import Paginator
from trac.web.api import IRequestFilter
from trac.web.chrome import Chrome, add_link, add_script, add_stylesheet, add_notice, add_warning, web_context
from trac.wiki.formatter import format_to_oneliner
from trac.wiki.macros import WikiMacroBase
from trac.wiki.api import parse_args

from pullrequests.model import PullRequest


class PullRequestsModule(Component):

    implements(IAdminPanelProvider, IRequestFilter, ITicketManipulator)

    create_commands = ListOption('pullrequests', 'create_commands', 'open')
    update_commands = ListOption('pullrequests', 'update_commands', 'reviewed, closed')

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'PULL_REQUEST' in req.perm:
            yield ('pr', "Pull Requests", 'list', "List")

    def render_admin_panel(self, req, category, panel, path_info):
        if panel == 'list':
            req.perm.require('PULL_REQUEST')
            return self.render_pr_list_panel(req, category, panel, path_info)

    def render_pr_list_panel(self, req, category, panel, path_info):
        def format_datetime_utc(t):
            return format_datetime(t, tzinfo=utc, locale=getattr(req, 'lc_time', None))

        def format_wikilink(pr):
            resource = Resource('ticket', pr.ticket)
            context = web_context(req, resource)
            return format_to_oneliner(self.env, context, pr.wikilink)

        # Detail view?
        if path_info:
            id = path_info
            pr = PullRequest.select_by_id(self.env, id)
            if not pr:
                raise TracError("Pull request does not exist!")
            if req.method == 'POST':
                if req.args.get('save'):
                    pr.status = req.args.get('status')
                    pr.add_reviewer(req.authname)

                    PullRequest.update_status_and_reviewers(self.env, pr)
                    add_notice(req, 'Your changes have been saved.')
                    req.redirect(req.href.admin(category, panel))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(category, panel))

            Chrome(self.env).add_wiki_toolbars(req)
            data = {'view': 'detail',
                    'pr': pr,
                    'statuses': self.create_commands + self.update_commands,
                    'format_datetime_utc': format_datetime_utc,
            }

        else:
            #Pagination
            page = int(req.args.get('page', 1))
            max_per_page = int(req.args.get('max', 10))

            prs = PullRequest.select_all_paginated(self.env, page, max_per_page)
            total_count = PullRequest.count_all(self.env)

            paginator = Paginator(prs, page - 1, max_per_page, total_count)
            if paginator.has_next_page:
                next_href = req.href.admin(category, panel, max=max_per_page, page=page + 1)
                add_link(req, 'next', next_href, 'Next Page')
            if paginator.has_previous_page:
                prev_href = req.href.admin(category, panel, max=max_per_page, page=page - 1)
                add_link(req, 'prev', prev_href, 'Previous Page')
    
            pagedata = []
            shown_pages = paginator.get_shown_pages(21)
            for page in shown_pages:
                pagedata.append([req.href.admin(category, panel, max=max_per_page, page=page), None,
                                str(page), 'Page %d' % (page,)])
            paginator.shown_pages = [dict(zip(['href', 'class', 'string', 'title'], p)) for p in pagedata]
            paginator.current_page = {'href': None, 'class': 'current',
                                    'string': str(paginator.page + 1),
                                    'title':None}
            data = {'view': 'list',
                    'paginator': paginator,
                    'max_per_page': max_per_page,
                    'prs': prs,
                    'format_datetime_utc': format_datetime_utc,
                    'format_wikilink': format_wikilink,
            }

        return 'pullrequests.html', data, None

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        path = req.path_info
        if path.startswith('/ticket/'):
            if data and 'ticket' in data and 'fields' in data:
                self._append_pr_links(req, data)
        return template, data, content_type

    def _append_pr_links(self, req, data):
        rendered = ''
        ticket = data['ticket']
        items = PullRequest.select(self.env, ticket=str(ticket.id))
        if items:
            ticket.values['PRs'] = True # Activates field
            results = []
            for pr in reversed(items):
                label = 'PR:%s (%s)' % (pr.id, pr.status)
                href = req.href.ticket(pr.ticket) + '#comment:%s' % (pr.comment,)
                link = tag.a(label, href=href)
                results.append(link)
            rendered = tag.span(*[e for pair in zip(results, [' '] * len(results)) for e in pair][:-1])
        data['fields'].append({
            'name': 'PRs',
            'rendered': rendered,
            'type': 'textarea', # Full row
        })

    # ITicketManipulator methods

    command_pr_url = r'(?P<command>[A-Za-z]+) PR: (?P<wikilink>\S+)'
    command_pr_id = r'(?P<command>[A-Za-z]+) PR:(?P<id>[0-9]+)'

    command_pr_url_re = re.compile(command_pr_url)
    command_pr_id_re = re.compile(command_pr_id)    

    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        if 'preview' in req.args:
            # During preview: Do nothing
            return []

        if 'PULL_REQUEST' in req.perm:
            comment = req.args.get('comment')
            author = get_reporter_id(req, 'author')
            if comment:
                req.args['comment'] = self._handle_comment(req, ticket, comment, author)
        return []

    def _handle_comment(self, req, ticket, comment, author):
        def create_pr_and_inline_id(m):
            command = m.group('command')
            wikilink = m.group('wikilink')
            if command in self.create_commands:
                id = None
                status = command
                reviewers = ''
                opened = modified = datetime.now(utc)
                comment_number = (ticket.get_comment_number(ticket['changetime']) or 0) + 1
                pr = PullRequest(id, status, author, reviewers, opened, modified, ticket.id, comment_number, wikilink)
                PullRequest.add(self.env, pr)
                add_notice(req, 'A new pull request has been created.')

                return u'%s PR:%s %s' % (command, pr.id, wikilink)
            else:
                return m.group(0)
            return u'[%s %s]' % (('/hours/%s' % ticket.id), match.group())
        comment = self.command_pr_url_re.sub(create_pr_and_inline_id, comment)

        for m in self.command_pr_id_re.finditer(comment):
            command = m.group('command')
            id = m.group('id')
            if command in self.update_commands:
                pr = PullRequest.select_by_id(self.env, id)
                if pr is None:
                    add_warning(req, 'Pull request %s was not found.' % (id,))
                    continue
                pr.status = command
                pr.add_reviewer(author)
                PullRequest.update_status_and_reviewers(self.env, pr)
                add_notice(req, 'Pull request %s has been updated.' % (id,))

        return comment


class PRQueryMacro(WikiMacroBase):
    """List all matching pull requests.
    
    Example:
    {{{
        [[PRQuery(status=reviewed,author=joe)]]
    }}}
    """

    def expand_macro(self, formatter, name, content):
        args, kw = parse_args(content)
        status = kw.get('status')
        author = kw.get('author')
        items = PullRequest.select(self.env, status=status, author=author)

        rows = [tag.tr(
                    tag.td(pr.id),
                    tag.td(pr.status),
                    tag.td(tag.a('#%s' % (pr.ticket,), href=formatter.href.ticket(pr.ticket) + '#comment:%s' % (pr.comment,))),
                    tag.td(format_to_oneliner(self.env, formatter.context, pr.wikilink)),
                    tag.td(pr.author),
                    tag.td(pr.reviewers),
                    class_='odd' if idx % 2 else 'even')
                for idx, pr in enumerate(items)]
        if not rows:
            rows = [tag.tr(tag.td('No pull requests found', colspan=6, class_='even'))]

        return tag.table(
            tag.thead(
                tag.tr(
                    tag.th('PR'),
                    tag.th('Status'),
                    tag.th('Ticket'),
                    tag.th('Changes'),
                    tag.th('Author'),
                    tag.th('Reviewers'),
                    class_='trac-columns')),
            tag.tbody(rows),
            class_='listing')
