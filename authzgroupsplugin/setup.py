# Copyright David Abrahams 2007. Distributed under the Boost
# Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#!/usr/bin/env/python

from setuptools import setup

setup(
    name = 'TracAuthzGroups',
    version = '1.0.0',
    packages = [ 'authzgroups' ],

    author = 'Matthew Good',

    author_email = 'trac@matt-good.net',
    
    description = 'This plugin allows reusing the groups from your SVN authz file for user permissions in Trac.',

    license = 'Boost Software License 1.0',

    keywords = 'trac plugin svn authz',
    url = 'http://trac-hacks.org/wiki/AuthzGroupsPlugin',
    
    classifiers = [
      'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
             'authzgroups = authzgroups',
        ]
    }
)
    
