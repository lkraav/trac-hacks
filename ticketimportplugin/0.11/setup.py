#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

from setuptools import setup

PACKAGE='talm_importer'

setup(
    name='TicketImport',
    version='0.6',
    author='Francois Granade',
    author_email='francois@nexb.com',
    url='http://nexb.com',
    license='BSD',
    description='Import CSV and Excel files',
    zip_safe=True,
    packages=[PACKAGE],
    package_data={PACKAGE: ['templates/*.cs']},
    entry_points={'trac.plugins': 'TicketImport = %s' % (PACKAGE)}
    )
