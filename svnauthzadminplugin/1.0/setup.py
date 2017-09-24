#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'SvnAuthzAdminPlugin'
VERSION = '1.0'

setup(
    name=PACKAGE, version=VERSION,
    author='Gergely Kis',
    author_email='trac@kisgergely.com',
    url='https://www.trac-hacks.org/wiki/SvnAuthzAdminPlugin',
    description='SvnAuthz File Administration Plugin for Trac',
    license='GPL',
    package_dir={
        'svnauthz': 'svnauthz',
    },
    packages=['svnauthz'],
    package_data={
        'svnauthz': [
            'templates/*',
        ]
    },
    entry_points={
        'trac.plugins': [
            'svnauthz.api = svnauthz.api',
            'svnauthz.admin_ui = svnauthz.admin_ui',
        ]
    },
    zip_safe=False,
    install_requires=['Trac'],
    keywords="trac plugin subversion svn authz",
    classifiers=['Framework :: Trac'],
)
