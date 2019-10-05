#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2014, 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import ResourceManager

from trac.cache import cached
from trac.core import Component, implements
from trac.util import arity
from trac.util.html import tag
from trac.web.api import IRequestHandler, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_script_data, add_stylesheet, web_context
from trac.wiki.api import IWikiChangeListener, WikiSystem
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage
from datetime import datetime

try:
    import json
except:
    from tracrpc.json_rpc import json

try:
    from trac.web.chrome import web_context
except ImportError:
    from trac.mimeview.api import Context
    web_context = Context.from_request


class FieldTooltip(Component):
    """ Provides tooltip for ticket fields. (In Japanese/KANJI) チケットフィールドのツールチップを提供します。
        if wiki page named 'help/field-name is supplied, use it for tooltip text. """
    implements(IRequestHandler, IRequestFilter, ITemplateProvider, IWikiChangeListener)
    operations = {
        'del_owner': 'Clears the owner field.',
        'set_owner': 'Sets the owner to the selected or entered owner. Defaults to the current user. When `[ticket] restrict_owner = true`, the select will be populated with users that have `TICKET_MODIFY` permission and an authenticated session.',
        'set_owner_to_self': 'Sets the owner to the logged in user.',
        'may_set_owner': 'Sets the owner to the selected or entered owner. Defaults to the existing owner.',
        'del_resolution': 'Clears the resolution field.',
        'set_resolution': 'Sets the resolution to the selected value.',
        'leave_status': 'Makes no change to the ticket.',
        'reset_workflow': 'Resets the status of tickets that are in states no longer defined.',
    }
    operations.update({
        'del_owner.ja': u'チケットの所有者を削除します。',
        'set_owner.ja': u'チケットの所有者を選択された所有者か入力された所有者に設定します。',
        'set_owner_to_self.ja': u'チケットの所有者をログインユーザに設定します。',
        'may_set_owner.ja': u'チケットの所有者を選択された所有者か入力された所有者に設定します。',
        'del_resolution.ja': u'チケットの解決方法を削除します。',
        'set_resolution.ja': u'チケットの解決方法を選択された解決方法か入力された解決方法に設定します。',
        'leave_status.ja': u'チケットの現在のステータスを変更しません。',
        'reset_workflow.ja': u'チケットのステータスをリセットし、未定義とします。',
    })
    _default_pages = {
        'reporter': 'The author of the ticket.',
        'type': 'The category of the ticket (for example, defect or enhancement request). See TicketTypes for more details.',
        'component': 'The project module or subsystem this ticket concerns.',
        'version': 'Version of the project that this ticket pertains to.',
        'keywords': 'Keywords that a ticket is marked with. Useful for searching and report generation.',
        'priority': 'The importance of this issue, ranging from \'\'trivial\'\' to \'\'blocker\'\'. A dropdown list when multiple priorities are defined.',
        'milestone': 'Due date of when this issue should be resolved. A dropdown list containing the milestones.',
        'assigned to': 'Principal person responsible for handling the issue.',
        'owner': 'Principal person responsible for handling the issue.',
        'cc': 'A comma-separated list of other users or email addresses to notify. Note that this does not imply responsiblity or any other policy.',
        'resolution': 'Reason for why a ticket was closed. One of `fixed`, `invalid`, `wontfix`, `duplicate`, `worksforme`.',
        'status': 'What is the current status? The statuses are defined in the [TracWorkflow#BasicTicketWorkflowCustomization ticket workflow]. For the default workflow the statuses are `new`, `assigned`, `accepted`, `closed` and `reopened`.',
        'summary': 'A brief description summarizing the problem or issue. Simple text without WikiFormatting.',
        'description': 'The body of the ticket. A good description should be specific, descriptive and to the point. Accepts WikiFormatting.',
        # workflow
        'accept': 'Accept this ticket and ' + operations['set_owner_to_self'],
        'create': 'Create new unassigned ticket',
        'create_and_assign': 'Assign this ticket and ' + operations['may_set_owner'],
        'leave': operations['leave_status'],
        'reassign': 'Assign this ticket and ' + operations['set_owner'],
        'reopen': 'Reopen this ticket and ' + operations['del_resolution'],
        'resolve': 'Close this ticket and ' + operations['set_resolution'],
        # default
        '../nohint': '//,,(sorry, no hint is presented... click icon above to add),,//',
        '../nohint-readonly': '//,,(sorry, no hint is presented.),,//',
    }
    # for locale=ja
    _default_pages.update({
        'reporter.ja': u'このチケットの作成者',
        'type.ja': u'このチケットの種類 (例えば、不具合 (defect), 機能追加 (enhancement request) など) 詳細は [trac:TicketTypes TicketTypes] 参照。',
        'component.ja': u'このチケットが紐づくモジュールやサブシステム。',
        'version.ja': u'このチケットが関連するプロジェクトのバージョン。',
        'keywords.ja': u'チケットに付与するキーワード。検索や、レポートの生成で利用できる。',
        'priority.ja': u'\'\'trivial\'\' から \'\'blocker\'\' の範囲で示されるチケットの重要度。定義した他の優先度を含めプルダウンで表示。',
        'milestone.ja': u'このチケットを遅くともいつまでに解決すべきか。マイルストーン一覧をプルダウンで表示。',
        'assigned to.ja': u'次にチケットを扱うべき人。',
        'owner.ja': u'チケットを扱っている人。',
        'cc.ja': u'通知すべきユーザ名またはE-Mailアドレスのカンマ区切りリスト。なお、責任などのどんな意味も持っていない。',
        'resolution.ja': u'チケットが解決された際の理由。{{{修正した(fixed)}}}、{{{無効なチケット(invalid)}}}、{{{修正しない(wontfix)}}}、{{{他のチケットと重複(duplicate)}}}、{{{再現しない(worksforme)}}}など。',
        'status.ja': u'チケットの現在の状態。 {{{new}}}, {{{assigned}}}, {{{closed}}}, {{{reopened}}} など。',
        'summary.ja': u'問題や課題の簡単な説明。WikiFormatting されない。',
        'description.ja': u'チケットの内容。WikiFormatting される。状況を特定する、的を射た説明がよい。',
        # workflow
        'accept.ja': u'このチケットを引き受け、' + operations['set_owner_to_self.ja'],
        'create': u'チケットを作成します。所有者は設定しません。',
        'create_and_assign': u'このチケットを引き受け、' + operations['may_set_owner.ja'],
        'leave.ja': operations['leave_status.ja'],
        'reassign.ja': operations['set_owner.ja'],
        'reopen.ja': u'チケットを再び扱い、' + operations['del_resolution.ja'],
        'resolve.ja': u'解決したものとし、' + operations['set_resolution.ja'],
        # default
        '../nohint.ja': u'//,,(説明はありません ... 追加するにはアイコンをクリック),,//',
        '../nohint-readonly.ja': u'//,,(説明はありません.),,//',
    })
    # blocking, blockedby for MasterTicketsPlugin, TicketRelationsPlugin
    # position for QueuesPlugin
    # estimatedhours for EstimationToolsPlugin, TracHoursPlugin, SchedulingToolsPlugin
    # startdate, duedate for SchedulingToolsPlugin
    # totalhours for TracHoursPlugin
    # duetime for TracMileMixViewPlugin
    # completed,storypoints,userstory for TracStoryPointsPlugin
    # fields = "'estimatedhours', 'hours', 'billable', 'totalhours', 'internal'" for T&E;
    #    See http://trac-hacks.org/wiki/TimeEstimationUserManual
    # and any more default tooltip text...

    _wiki_prefix = 'help/'

    @cached
    def pages(self, db=None):
        # retrieve wiki contents for field help
        pages = {}
        prefix_len = len(FieldTooltip._wiki_prefix)
        wiki_pages = WikiSystem(self.env).get_pages(FieldTooltip._wiki_prefix)
        for page in wiki_pages:
            # FIXME
            # if 'WIKI_VIEW' not in self.perm('wiki', pages):
            #     continue
            if arity(WikiPage.__init__) == 5:
                text = WikiPage(self.env, page, db=db).text
            else:  # == 4
                text = WikiPage(self.env, page).text
            if '----' in text:
                pages[page[prefix_len:]] = text[0:text.find('----')]
            else:
                pages[page[prefix_len:]] = text
        return pages

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return [('fieldtooltip', ResourceManager().resource_filename(__name__, 'htdocs'))]

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, metadata=None):
        if template in ['ticket.html']:
            add_script(req, 'fieldtooltip/tooltip.js')
            add_stylesheet(req, 'fieldtooltip/tooltip.css')
        return template, data, metadata

    # IRequestHandler Methods
    def match_request(self, req):
        return req.path_info == '/fieldtooltip/tooltip.jsonrpc'

    def process_request(self, req):
        def to_html(dom):
            return format_to_html(self.env, web_context(req), dom, False)
        payload = json.load(req)
        if 'method' not in payload or not payload['method'] == 'wiki.getPage':
            req.send_response(501)  # Method Not Implemented
            req.end_headers()
            return
        if req.get_header('If-None-Match') == str(id(self.pages)):
            req.send_response(304)  # Not Modified
            req.end_headers()
            return
        content = json.dumps({
            'pages': {page: to_html(self.pages[page]) for page in self.pages},
            'defaults': {page: to_html(self._default_pages[page]) for page in self._default_pages},
        }, indent=4)
        req.send_response(200)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(content))
        req.send_header('ETag', "%s" % id(self.pages))
        req.end_headers()
        req.write(content)

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        if page.name.startswith(self._wiki_prefix):
            del self.pages

    def wiki_page_changed(self, page, version, t, comment, author):
        if page.name.startswith(self._wiki_prefix):
            del self.pages

    def wiki_page_deleted(self, page):
        if page.name.startswith(self._wiki_prefix):
            del self.pages

    def wiki_page_version_deleted(self, page):
        if page.name.startswith(self._wiki_prefix):
            del self.pages

    def wiki_page_renamed(self, page, old_name):
        if page.name.startswith(self._wiki_prefix):
            del self.pages
