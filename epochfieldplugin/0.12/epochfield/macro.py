#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

"""
formatter.req.session.get('lc_time'): userPref->dateformat: {'iso8601' | '' }
formatter.req.tz:  userPref->timezone: {GMT+5:00 | etc }; if default, 
"""

from trac.core import Component, implements
from trac.wiki.api import IWikiMacroProvider
from datetime import datetime
from trac.util.datefmt import format_datetime, from_utimestamp, to_timestamp, \
    format_date, format_time

class Macro(Component):
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield "Epoch"
        yield "EpochToDate"
        yield "EpochToDateTime"
        yield "EpochToTime"

    def get_macro_description(self, name):
        return """
        Epoch(unix time) to datetime String, Timezone sensitive, follows system|user's timezone|dateformat preferences.
        ||= Wiki Markup =||= Display =||
        || {{{[[Epoch(1449442800000000)]]}}} || [[Epoch(1449442800000000)]] ||
        || {{{[[Epoch(1449442800000000, %X)]]}}} || [[Epoch(1449442800000000, %X)]] ||
        || {{{[[Epoch(1449442800000000, %x)]]}}} || [[Epoch(1449442800000000, %x)]] ||
        """

    def is_inline(self, content):
        return False

    def expand_macro(self, formatter, name, content, args=None):
        data = content and content.split(',')[0] or None
        _format = content and content.find(',') != -1 and \
            content.split(',')[1].strip() or \
            formatter.req.session.get('lc_time', None)
        dateformatter = {"Epoch": format_datetime,
                      "EpochToDate": format_date,
                      "EpochToDateTime": format_datetime,
                      "EpochToTime": format_time }.get(name)
        return not data.isdigit() and data or \
            _format and \
             dateformatter(from_utimestamp(long(data)), _format, tzinfo=formatter.req.tz) or \
             dateformatter(from_utimestamp(long(data)), tzinfo=formatter.req.tz)
