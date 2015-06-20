#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import sys

from setuptools import setup, find_packages

setup(
    name = 'LDAPAcctMngrPlugin',
    version = '0.9',
    packages = find_packages(),

    author = 'Adam Li',
    author_email = 'adamli528@gmail.com',
    description = 'A LDAP authentication plugin for AccountManager',
    license = 'Apache License 2.0',
    install_requires = ['TracAccountManager'],
    entry_points = {
        'trac.plugins': [
            'security.ldapstore = security.ldapstore'
        ],
    },
)
