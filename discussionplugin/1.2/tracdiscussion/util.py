# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from genshi.input import HTML
from genshi.filters import Transformer

from trac.util import to_list
from trac.util.html import Markup
from trac.util.text import to_unicode
from trac.wiki.formatter import format_to_oneliner


# Formats wiki text to single line HTML but removes all links.
def format_to_oneliner_no_links(env, context, content):
    stream = HTML(format_to_oneliner(env, context, to_unicode(content)))
    return Markup(stream | Transformer('//a').unwrap())


def prepare_topic(uids, topic):
    """Unpack list of topic subscribers and get topic status."""
    if topic:
        topic['subscribers'] = to_list(topic['subscribers'] or '', ' ')
        topic['unregistered_subscribers'] = \
            set(topic['subscribers']).difference(uids)
        topic['status'] = topic_status_to_list(topic['status'])
    return topic


def topic_status_to_list(status):
    if status == 0:
        return set(['unsolved'])
    status_list = set([])
    if status & 0x01:
        status_list.add('solved')
    else:
        status_list.add('unsolved')
    if status & 0x02:
        status_list.add('locked')
    return status_list


def topic_status_from_list(status_list):
    status = 0
    if 'solved' in status_list:
        status |= 0x01
    if 'locked' in status_list:
        status |= 0x02
    return status
