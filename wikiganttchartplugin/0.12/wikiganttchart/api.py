# -*- coding: utf_8 -*-
#
# Copyright (C) 2014 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from datetime import date, datetime

from trac.core import TracError
from trac.config import ChoiceOption, IntOption, Option
from trac.util import arity
from trac.util.datefmt import parse_date, utc
from trac.util.translation import domain_functions, dgettext


TEXTDOMAIN = 'wikiganttchart'


_, tag_, N_, gettext, add_domain = domain_functions(
    TEXTDOMAIN,
    ('_', 'tag_', 'N_', 'gettext', 'add_domain'))


if arity(Option.__init__) <= 5:
    def _option_with_tx(Base): # Trac 0.12.x
        class Option(Base):
            def __getattribute__(self, name):
                if name == '__class__':
                    return Base
                val = Base.__getattribute__(self, name)
                if name == '__doc__':
                    val = dgettext(TEXTDOMAIN, val)
                return val
        return Option
else:
    def _option_with_tx(Base): # Trac 1.0 or later
        def fn(*args, **kwargs):
            kwargs['doc_domain'] = TEXTDOMAIN
            return Base(*args, **kwargs)
        return fn


ChoiceOption = _option_with_tx(ChoiceOption)
IntOption = _option_with_tx(IntOption)
Option = _option_with_tx(Option)


def iso8601_parse_date(text, tzinfo=utc):
    try:
        return parse_date(text, tzinfo=tzinfo)
    except TracError, e:
        raise ValueError(e)


def iso8601_format_date(t):
    if isinstance(t, date):
        t = datetime(t.year, t.month, t.day, tzinfo=utc)
    return t.strftime('%Y-%m-%d')


try:
    import babel

except ImportError:
    locale_en = None

    def l10n_format_datetime(t, format=None, locale=None):
        return iso8601_format_date(t)

else:
    from babel.core import Locale
    from babel.dates import format_date as babel_format_date

    _DATE_FORMATS = {
        'ca': {'MMMd': u'MMM d'},
        'da': {'MMMd': u'd. MMM'},
        'de': {'MMMd': u'd. MMM'},
        'el': {'MMMd': u'd MMM'},
        'en': {'MMMd': u'MMM d'},
        'es': {'MMMd': u'd MMM'},
        'fa': {'MMMd': u'd LLL'},
        'fi': {'MMMd': u'd. MMM'},
        'fr': {'MMMd': u'd MMM'},
        'gl': {'MMMd': u'd MMM'},
        'he': {'MMMd': u'MMM d'},
        'hu': {'MMMd': u'MMM d'},
        'it': {'MMMd': u'd MMM'},
        'ja': {'MMMd': u'M月d日'},
        'ko': {'MMMd': u'MMM d일'},
        'nl': {'MMMd': u'd-MMM'},
        'pl': {'MMMd': u'MMM d'},
        'pt': {'MMMd': u'd MMM'},
        'ro': {'MMMd': u'd MMM'},
        'ru': {'MMMd': u'd MMM'},
        'sv': {'MMMd': u'd MMM'},
        'tr': {'MMMd': u'd MMM'},
        'uk': {'MMMd': u'd MMM'},
        'vi': {'MMMd': u'd MMM'},
        'zh': {'MMMd': u'MMMd日'},
    }
    locale_en = Locale.parse('en_US')

    def l10n_format_datetime(t, format='medium', locale=None):
        if not locale:
            locale = locale_en
        formats = _DATE_FORMATS.get(locale.language)
        if formats and format in formats:
            format = formats[format]
        return babel_format_date(t, format, locale)
