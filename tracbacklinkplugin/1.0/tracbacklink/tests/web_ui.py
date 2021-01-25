# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import io
import os
import pkg_resources
import tempfile
import unittest

from trac.attachment import Attachment
from trac.test import EnvironmentStub
from trac.ticket.model import Milestone, Ticket
from trac.ticket.roadmap import MilestoneModule  # for IResourceManager
from trac.ticket.web_ui import TicketModule  # for trac/ticket/templates/
from trac.util.html import Markup
from trac.wiki.admin import WikiAdmin
from trac.wiki.model import WikiPage
from trac.versioncontrol.api import DbRepositoryProvider, RepositoryManager

del MilestoneModule, TicketModule

from tracbacklink.api import MockRequest, TracBackLinkSystem
from tracbacklink.web_ui import TracBackLinkModule

from .api import RepositoryStubConnector, _add_cset


class TracBackLinkModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, path=_mkdtemp(),
                                   enable=['trac.*', RepositoryStubConnector])
        _import_default_pages(self.env)
        self.env.enable_component(TracBackLinkSystem)
        system = TracBackLinkSystem(self.env)
        system.environment_created()

    def tearDown(self):
        self.env.db_transaction("DROP TABLE IF EXISTS backlink")
        self.env.reset_db()

    def test_wiki_backlinks(self):
        with self.env.db_transaction:
            _save_wiki(self.env, 'SandBox', 'blah',
                              comment='comment TracWiki')
            _save_wiki(self.env, 'SandBox', 'See TracWiki')
            _insert_attachment(self.env, 'wiki', 'SandBox',
                              'attachment TracWiki')
        target = WikiPage(self.env, 'TracWiki')
        rv = self._get_backlinks_content(target)
        self.assertIsInstance(rv, Markup)
        self.assertIn(u'<h3 class="foldable">Back Links'
                      u'<span class="trac-count">(1)</span></h3>', rv)
        self.assertIn(u'<a href="/trac.cgi/wiki/SandBox">wiki:SandBox</a> – ',
                      rv)
        self.assertIn(u' href="/trac.cgi/wiki/SandBox?version=2"', rv)
        self.assertIn(u' title="comment TracWiki"', rv)
        self.assertIn(u'>@2</a>', rv)
        self.assertIn(u' title="attachment TracWiki"', rv)
        self.assertIn(u' href="/trac.cgi/attachment/wiki/SandBox/file.txt"',
                      rv)
        self.assertIn(u'>attachment:file.txt</a></div>', rv)

    def test_ticket_backlinks(self):
        with self.env.db_transaction:
            target = _insert_ticket(self.env, 'Target')
            text = '#%d' % target.id
            ticket = _insert_ticket(self.env, 'Source', description=text)
            # comment:1 has a link
            ticket.save_changes('anonymous', text)
            # comment:2 has no links
            ticket.save_changes('anonymous', text)
            ticket.modify_comment(ticket['changetime'], 'anonymous', 'empty')
            # comment:3 has a link
            ticket.save_changes('anonymous', 'empty')
            ticket.modify_comment(ticket['changetime'], 'anonymous', text)
            _insert_attachment(self.env, 'ticket', ticket.id,
                              'attachment ' + text)
        rv = self._get_backlinks_content(target)
        self.assertIsInstance(rv, Markup)
        self.assertIn(u'<h3 class="foldable">Back Links'
                      u'<span class="trac-count">(1)</span></h3>', rv)
        self.assertIn(u' href="/trac.cgi/ticket/2"', rv)
        self.assertIn(u' title="defect: Source (new)"', rv)
        self.assertIn(u' class="new ticket"', rv)
        self.assertIn(u'>#2</a> Source – <a ', rv)
        self.assertIn(u' title="#1"', rv)
        self.assertIn(u' href="/trac.cgi/ticket/2#comment:1"', rv)
        self.assertIn(u'>comment:1</a>, <a ', rv)
        self.assertIn(u' href="/trac.cgi/ticket/2#comment:3"', rv)
        self.assertIn(u'>3</a> – <a', rv)
        self.assertIn(u' title="attachment #1"', rv)
        self.assertIn(u' href="/trac.cgi/attachment/ticket/2/file.txt"', rv)
        self.assertIn(u'>attachment:file.txt</a></div>', rv)

    def test_milestone_backlinks(self):
        with self.env.db_transaction:
            target = Milestone(self.env, 'milestone3')
            _insert_milestone(self.env, 'release', 'See milestone:milestone3')
            _insert_attachment(self.env, 'milestone', 'release',
                               'attachment milestone:milestone3')
        rv = self._get_backlinks_content(target)
        self.assertIsInstance(rv, Markup)
        self.assertIn(u'<h3 class="foldable">Back Links'
                      u'<span class="trac-count">(1)</span></h3>', rv)
        self.assertIn(u'<a href="/trac.cgi/milestone/release"'
                      u'>Milestone release</a> – <a ', rv)
        self.assertIn(u' title="attachment milestone:milestone3"', rv)
        self.assertIn(u' href="/trac.cgi/attachment/milestone/release/'
                      u'file.txt"', rv)
        self.assertIn(u'>attachment:file.txt</a></div>', rv)

    def test_changeset_backlinks(self):
        with self.env.db_transaction:
            target = _insert_ticket(self.env, 'Target')
            tktid = target.id
            manager = RepositoryManager(self.env)
            provider = DbRepositoryProvider(self.env)
            reponame = ''
            provider.add_repository(reponame, '/', 'cached-stub')
            _add_cset(self.env, reponame, 'closes #%d' % tktid, 1)
            _add_cset(self.env, reponame, 'refs #%d' % tktid, 2)
            manager.notify('changeset_added', reponame, [1, 2])

        rv = self._get_backlinks_content(target)
        self.assertIsInstance(rv, Markup)
        self.assertIn(u'<h3 class="foldable">Back Links'
                      u'<span class="trac-count">(1)</span></h3>', rv)
        self.assertIn(u'<a href="/trac.cgi/browser">source:(default)</a> – '
                      u'<a ', rv)
        self.assertIn(u' title="closes #1"', rv)
        self.assertIn(u' href="/trac.cgi/changeset/1"', rv)
        self.assertIn(u'>[1]</a> <a ', rv)
        self.assertIn(u' title="refs #1"', rv)
        self.assertIn(u' href="/trac.cgi/changeset/2"', rv)
        self.assertIn(u'>[2]</a></div>', rv)

    def _get_backlinks_content(self, target):
        mod = TracBackLinkModule(self.env)
        req = MockRequest(self.env)
        return mod._get_backlinks_content(req, target)


def _mkdtemp():
    return os.path.realpath(tempfile.mkdtemp(prefix='trac-testdir-'))


def _import_default_pages(env):
    dir_ = pkg_resources.resource_filename('trac.wiki', 'default-pages')
    pages = pkg_resources.resource_listdir('trac.wiki', 'default-pages')
    wikiadm = WikiAdmin(env)
    with env.db_transaction:
        for name in pages:
            filename = os.path.join(dir_, name)
            wikiadm.import_page(filename, name)


def _insert_attachment(env, realm, id_, description, filename='file.txt',
                       content=b'blah'):
    att = Attachment(env, realm, id_)
    att.description = description
    att.insert(filename, io.BytesIO(content), len(content))
    return att


def _insert_milestone(env, name, description):
    milestone = Milestone(env)
    milestone.name = name
    milestone.description = description
    milestone.insert()
    return milestone


def _insert_ticket(env, summary, status='new', **kwargs):
    ticket = Ticket(env)
    ticket['summary'] = summary
    ticket['status'] = status
    for name in kwargs:
        ticket[name] = kwargs[name]
    ticket.insert()
    return ticket


def _save_wiki(env, name, text, author='anonymous', comment=None):
    page = WikiPage(env, name)
    page.text = text
    page.save(author, comment)
    return page


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TracBackLinkModuleTestCase))
    return suite
