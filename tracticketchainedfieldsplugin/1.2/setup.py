#!/usr/bin/env python

import sys
from setuptools import find_packages, setup

setup(
    name = 'TracTicketChainedFields',
    version = '1.2',
    packages = ['tcf'],
    package_data = { 'tcf': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 'tests/*.*' ] },
    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Trac Ticket Chained Fields plugin for Trac.",
    license = "BSD",
    keywords = "trac ticket chained fields",
    url = "https://trac-hacks.org/wiki/TracTicketChainedFieldsPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {'trac.plugins': ['tcf = tcf.web_ui']},
)
