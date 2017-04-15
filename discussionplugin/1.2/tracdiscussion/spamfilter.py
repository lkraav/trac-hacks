# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2012-2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Component, implements

from tracspamfilter.api import RejectContent
from tracspamfilter.filtersystem import FilterSystem

from tracdiscussion.api import IDiscussionFilter


class DiscussionSpamFilter(Component):
    """[extra] Implements an adapter for Trac Spam Filtering.

    Deny creation of topics and messages with bad content using methods
    provided by [http://trac.edgewall.org/wiki/SpamFilter TracSpamFilter].
    """

    implements(IDiscussionFilter)

    # IDiscussionFilter methods

    def filter_topic(self, context, topic):
        req = context.req
        try:
            self._spam_test(req, topic['author'],
                            [(None, topic['author']),
                             (None, topic['subject']),
                             (None, topic['body'])], req.remote_addr)
        except RejectContent, error:
            # Topic contains SPAM.
            return False, error.message
        return True, topic

    def filter_message(self, context, message):
        req = context.req
        try:
            self._spam_test(req, message['author'],
                            [(None, message['author']),
                             (None, message['body'])],
                            req.remote_addr)
        except RejectContent, error:
            # Message contains SPAM.
            return False, error.message
        return True, message

    def _spam_test(self, req, author, changes, ip):
        FilterSystem(self.env).test(req, author, changes)
