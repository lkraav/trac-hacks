#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import sys
from setuptools import setup

min_python = (2, 5)
if sys.version_info < min_python:
    print("TracTicketTemplate requires Python %d.%d or later" % min_python)
    sys.exit(1)

extra = {}

try:
    import babel
    from trac.util.dist import get_l10n_js_cmdclass
except ImportError:
    babel = None
else:
    extra['cmdclass'] = get_l10n_js_cmdclass()
    extractors = [
        ('**.py', 'python', None),
        ('**/templates/**.html', 'genshi', None),
        ('**/templates/**.txt', 'genshi',
         {'template_class': 'genshi.template:NewTextTemplate'}),
    ]
    extra['message_extractors'] = {
        'tickettemplate': extractors,
    }

setup(
    name='TracTicketTemplate',
    version='1.0',
    packages=['tickettemplate'],
    package_data={'tickettemplate': ['*.txt', 'templates/*.*', 'htdocs/*.*',
                                     'tests/*.*', 'locale/*.*',
                                     'locale/*/LC_MESSAGES/*.*']},
    author="Richard Liao",
    author_email='richard.liao.i@gmail.com',
    maintainer="Richard Liao",
    maintainer_email="richard.liao.i@gmail.com",
    description="Ticket template plugin for Trac.",
    license="3-Clause BSD",
    keywords="trac ticket template",
    url="http://trac-hacks.org/wiki/TracTicketTemplatePlugin",
    classifiers=[
        'Framework :: Trac',
    ],

    install_requires=['simple_json' if sys.version_info < (2, 6) else ''],
    test_suite='tickettemplate.tests',
    entry_points={
        'trac.plugins': ['tickettemplate = tickettemplate.ttadmin'],
    },
    **extra
)
