#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'SvnAuthzAdminPlugin'
VERSION = '1.0'

setup(
    name=PACKAGE, version=VERSION,
    author='Gergely Kis',
    author_email='trac@kisgergely.com',
    url='http://www.trac-hacks.org/wiki/SvnAuthzAdminPlugin',
    description='SvnAuthz File Administration Plugin for Trac',
    license='GPL',
    package_dir={
        'svnauthz': 'svnauthz',
        'svnauthz_test': 'svnauthz_test',
    },
    packages=['svnauthz', 'svnauthz_test'],
    package_data={
        'svnauthz': [
            'templates/*',
        ]
    },
    entry_points={
        'trac.plugins': [
            'svnauthz.admin_ui = svnauthz.admin_ui',
        ]
    },
    zip_safe=False,
    install_requires=['Trac>=1.0'],
    keywords="trac plugin subversion svn authz",
    classifiers=['Framework :: Trac'],
)
