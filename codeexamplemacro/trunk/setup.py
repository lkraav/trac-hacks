#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='CodeExampleMacro',
    version='1.2',
    author='Alexander Slesarev',
    author_email='nuald@codedgers.com',
    description='The Trac plugin for code examples colouring.',
    license='LGPL',
    url='http://trac-hacks.org/wiki/CodeExampleMacro',
    packages=find_packages(exclude=['*.tests*']),
    entry_points="""
        [trac.plugins]
        codeexample = codeexample
    """,
    test_suite='codeexample.tests.suite',
    tests_require=['mocker'],
    package_data={'codeexample': [
        'templates/*.html', 'htdocs/css/*.css', 'htdocs/js/*.js',
        'htdocs/img/*.gif', 'htdocs/img/*.png',
    ]},
)
