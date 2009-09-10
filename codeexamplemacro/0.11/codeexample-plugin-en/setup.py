#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name = 'CodeExample',
    version = '0.3.2',
    author = 'Alexander Slesarev',
    author_email = 'nuald@codedgers.com',
    description = 'The Trac plugin for code examples colouring.',
    license = 'LGPL',
    packages = find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        codeexample = codeexample
    """,
    test_suite = 'codeexample.tests.suite',
    package_data = {'codeexample': ['templates/*.html', 'htdocs/css/*.css',
                                  'htdocs/js/*.js']},
)
