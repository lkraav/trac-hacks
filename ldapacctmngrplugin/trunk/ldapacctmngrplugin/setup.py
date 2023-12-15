#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'LDAPAcctMngrPlugin',
    version = '0.10',
    packages = find_packages(),

    author = 'Adam Li',
    author_email = 'adamli528@gmail.com',
    description = 'A LDAP authentication plugin for AccountManager',
    license = 'Apache License 2.0',
    classifiers=[
        'Framework :: Trac',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    install_requires = ['TracAccountManager', 'python-ldap'],
    entry_points = {
        'trac.plugins': [
            'security.ldapstore = security.ldapstore'
        ],
    },
)
