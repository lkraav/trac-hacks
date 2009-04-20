#!/usr/bin/env python

from setuptools import setup

setup(
    name='TracDeveloper',
    version='0.2',
    packages=['tracdeveloper', 'tracdeveloper.dozer'],
    author='Alec Thomas',
    description='Adds some features to Trac that are useful for developers',
    url='http://trac-hacks.org/wiki/TracDeveloperPlugin',
    license='BSD',
    entry_points = {
        'trac.plugins': [
            'developer = tracdeveloper.main',
            'developer.apidoc = tracdeveloper.apidoc',
            'developer.debugger = tracdeveloper.debugger',
            'developer.plugins = tracdeveloper.plugins',
            'developer.javascript = tracdeveloper.javascript',
            'developer.log = tracdeveloper.log',
            'developer.dozer = tracdeveloper.dozer [PIL]',
        ]
    },
    extras_require = {
        'PIL': ['PIL'],
    },
    package_data = {
        'tracdeveloper' : [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/developer/*.html',
        ],
        'tracdeveloper.dozer' : [
            'htdocs/*.css',
            'templates/*.html',
        ],
    }
)
