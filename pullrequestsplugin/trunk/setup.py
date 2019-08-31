#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'PullRequests',
    version = '1.2',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'Track pull requests',
    packages = ['pullrequests', 'pullrequests.upgrades'],
    package_data = {'pullrequests': [
            'templates/*.html',
        ]
    },
    entry_points = {'trac.plugins': [
            'pullrequests.core = pullrequests.core',
            'pullrequests.web_ui = pullrequests.web_ui',
        ]
    },
)
