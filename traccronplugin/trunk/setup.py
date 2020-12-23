# -*- encoding: UTF-8 -*-
"""
Created on 12 Oct. 2010
@author: thierry
Updated on 4 Feb. 2013
@maintainer: t2y
"""

try:
    import setuptools
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()

import pkg_resources
from setuptools import setup

REQUIRES = [
    'Trac >= 0.10',
]

CLASSIFIERS = [
    'Framework :: Trac',
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'License :: OSI Approved :: BSD License',
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development',
]

try:
    LONG_DESCRIPTION = "".join([
        open("README.txt").read(),
    ])
except:
    LONG_DESCRIPTION = ""

setup(
    name='TracCronPlugin',
    version='0.3.1',
    description='Task scheduler plugin for Trac',
    long_description=LONG_DESCRIPTION,
    packages=['traccron'],
    package_data={'traccron': ['templates/*.*']},
    author='Thierry Bressure',
    author_email='thierry@bressure.net',
    maintainer='Tetsuya Morimoto',
    maintainer_email='tetsuya.morimoto@gmail.com',
    license='BSD',
    platforms=['unix', 'linux', 'osx', 'windows'],
    url='http://trac-hacks.org/wiki/TracCronPlugin',
    keywords='trac cron scheduler plugin',
    tests_require=['tox', 'pytest', 'pytest-pep8', 'pytest-capturelog'],
    classifiers=CLASSIFIERS,
    install_requires=REQUIRES,
    entry_points={
        'trac.plugins': [
            'traccron.core = traccron.core',
            'traccron.task = traccron.task',
            'traccron.scheduler = traccron.scheduler',
            'traccron.listener = traccron.listener',
            'traccron.history = traccron.history',
        ]
    },
)
