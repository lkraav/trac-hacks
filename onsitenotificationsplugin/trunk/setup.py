#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'OnSiteNotifications',
    version = '1.1',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'On-site notifications',
    packages = ['onsitenotifications', 'onsitenotifications.upgrades'],
    package_data = {'onsitenotifications': [
            'templates/*.html',
        ]
    },
    entry_points = {'trac.plugins': [
            'onsitenotifications.core = onsitenotifications.core',
            'onsitenotifications.web_ui = onsitenotifications.web_ui',
        ]
    },
)
