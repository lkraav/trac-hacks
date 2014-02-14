#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'LdapAuthStorePlugin'
VERSION = '0.3.0'

setup(
    name=PACKAGE,
    version=VERSION,
    description="LDAP (using LdapPlugin) password store plugin for TracAccountManager",
    maintainer='Immo Goltz',
    maintainer_email='immo.goltz@gmail.com',
    url='http://trac-hacks.org/wiki/LdapAuthStorePlugin',
    keywords = "trac ldap permission group acl accountmanager",
    license="BSD",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
    include_package_data=True,
    install_requires = [ 'TracAccountManager',
                         'LdapPlugin', ],
    entry_points = {
        'trac.plugins': [
            'ldapauthstore.ldap_store = ldapauthstore.ldap_store',
        ]
    }
)
