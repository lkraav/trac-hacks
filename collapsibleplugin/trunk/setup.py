#!/usr/bin/python3

# Copyright 2010 Matthew Noyes
# Copyright 2023 Dirk Stöcker
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from setuptools import setup, find_packages

VERSION = 0.6
NAME = 'TracCollapsiblePlugin'
PACKAGE = 'traccollapsible'

setup(
    name=NAME,
    version=VERSION,
    description='Embed wiki-text in a foldable structure, trac ticket attachment style',
    license = 'Apache v2',
    keywords = "trac plugin",
    author='Matthew Noyes, Dirk Stöcker',
    maintainer='Dirk Stöcker',
    maintainer_email='trac@dstoecker.de',
    url = 'https://trac-hacks.org/wiki/CollapsiblePlugin',
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: Apache Software License',
    ],
    requires = ['trac',  'trac', ],
        install_requires = [
            'setuptools',
            'Trac>=1.5',
        ],
    packages = find_packages(exclude=['*.texts*']),
    entry_points = { 'trac.plugins': [
        '%s = %s' % (NAME, PACKAGE),
        # Add additional components here
    ] }
)
