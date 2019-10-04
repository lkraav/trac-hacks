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
    _default_pages = {'reporter': 'The author of the ticket.',
                      'type': 'The nature of the ticket (for example, defect or enhancement request). See TicketTypes for more details.',
                      'component': 'The project module or subsystem this ticket concerns.',
                      'version': 'Version of the project that this ticket pertains to.',
                      'keywords': 'Keywords that a ticket is marked with. Useful for searching and report generation.',
                      'priority': 'The importance of this issue, ranging from trivial to blocker. A pull-down if different priorities where defined.',
                      'milestone': 'When this issue should be resolved at the latest. A pull-down menu containing a list of milestones.',
                      'assigned to': 'Principal person responsible for handling the issue.',
                      'owner': 'Principal person responsible for handling the issue.',
                      'cc': 'A comma-separated list of other users or E-Mail addresses to notify. Note that this does not imply responsiblity or any other policy.',
                      'resolution': 'Reason for why a ticket was closed. One of fixed, invalid, wontfix, duplicate, worksforme.',
                      'status': 'What is the current status? One of new, assigned, closed, reopened.',
                      'summary': 'A brief description summarizing the problem or issue. Simple text without WikiFormatting.',
                      'description': 'The body of the ticket. A good description should be specific, descriptive and to the point. Accepts WikiFormatting.',
                      # workflow
                      'leave': 'makes no change to the ticket.',
                      'resolve': '-',
                      'reassign': '-',
                      'accept': '-',
                      'reopen': '-',
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
                      'leave.ja': u'変更しない。',
                      'resolve.ja': u'解決したものとする。',
                      'reassign.ja': u'割り当てを変える。',
                      'accept.ja': u'引き受ける。',
                      'reopen.ja': u'再び扱う。',
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
            #FIXME
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
            add_script_data(req, {'fieldtooltip_default_pages': self._default_pages})
        return template, data, metadata

    # IRequestHandler Methods
    def match_request(self, req):
        return req.path_info == '/fieldtooltip/tooltip.jsonrpc'

    def process_request(self, req):
        payload = json.load(req)
        if not 'method' in payload or not payload['method'] == 'wiki.getPage':
            req.send_response(501)  # Method Not Implemented
            req.end_headers()
            return
        if req.get_header('If-None-Match') == str(id(self.pages)):
            req.send_response(304)  # Not Modified
            req.end_headers()
            return
            
        content = json.dumps({page:format_to_html(self.env, web_context(req), self.pages[page], False) for page in self.pages}, indent=4)
        req.send_response(200)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(content))
        req.send_header('ETag', "%s" % id(self.pages))
        req.end_headers()
        req.write(content)
    
    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        if page.name.startwith(self._wiki_prefix):
            del self.pages

    def wiki_page_changed(self, page, version, t, comment, author):
        if page.name.startwith(self._wiki_prefix):
            del self.pages

    def wiki_page_deleted(self, page):
        if page.name.startwith(self._wiki_prefix):
            del self.pages

    def wiki_page_version_deleted(self, page):
        if page.name.startwith(self._wiki_prefix):
            del self.pages

    def wiki_page_renamed(self, page, old_name):
        if page.name.startwith(self._wiki_prefix):
            del self.pages