#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracContacts',
    description='Add contact data to Trac',
    keywords='trac plugin contact person address addressbook address-book',
    version='0.3',
    url='https://trac-hacks.org/wiki/ContactsPlugin',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='CM Lubinski',
    author_email='clubinski@networkninja.com',
    long_description="""
    Adds a new menu item for contacts. Stores the contacts with their
    first name, last name, position, email, and phone.
    """,
    packages=['contacts'],
    package_data={
        'contacts': [
            'templates/*.html',
            'htdocs/*'
        ]
    },
    entry_points={
        'trac.plugins': [
            'contacts.db = contacts.db',
            'contacts.web_ui = contacts.web_ui',
        ]
    }
)
