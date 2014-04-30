# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2012-2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

# Spamfilter imports.
from trac.util import arity
from tracspamfilter.api import RejectContent
try: #SpamFilter < 0.7
    from tracspamfilter.api import FilterSystem
except ImportError: #SpamFilter 0.7+
    from tracspamfilter.filtersystem import FilterSystem

# Local imports.
from tracdiscussion.api import *

class DiscussionSpamFilter(Component):
    """
        The spam filtering component implements adapter for SpamFilterPluging
        which denies to create topics of messages with bad content.
    """
    implements(IDiscussionFilter)

    # IDiscussionFilter methods.

    def filter_topic(self, context, topic):
        # Test topic for spam.
        try:
            self._spam_test(context.req, topic['author'], [(None,
                topic['author']), (None, topic['subject']), (None,
                topic['body'])], context.req.remote_addr)
        except RejectContent, error:
            # Topic contains spam.
            return False, error.message

        # Topic is fine.
        return True, topic

    def filter_message(self, context, message):
        # Test message for spam.
        try:
            self._spam_test(context.req, message['author'], [(None,
                message['author']), (None, message['body'])],
                context.req.remote_addr)
        except RejectContent, error:
            # Message contains spam.
            return False, error.message

        # Message is fine.
        return True, message

    def _spam_test(self, req, author, changes, ip):
        if arity(FilterSystem.test) == 4: #SpamFilter < 0.3.2 or >= 0.7.0
            FilterSystem(self.env).test(req, author, changes)
        else: #SpamFilter >= 0.3.2 or < 0.7.0
            FilterSystem(self.env).test(req, author, changes, ip)
