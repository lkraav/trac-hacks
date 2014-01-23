#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 GMV SGI Team <http://www.gmv-sgi.es>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

PACKAGE = 'STractistics'
VERSION = '0.6'


setup(
    name=PACKAGE,
    version=VERSION,
    author='GMV Soluciones Globales Internet, Daniel Gómez Brito, Manuel Jesús Recena Soto',
    author_email='dagomez@gmv.com',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    license='BSD 3-Clause',
    description='Allows to gauge project activity at a glance.',
    url='http://trac-hacks.org/wiki/StractisticsPlugin',
    packages = ['stractistics'],
    entry_points={
        'trac.plugins': [
            '%s = stractistics.web_ui' % PACKAGE
        ]
    },
    package_data={
        'stractistics': [
            'templates/*.html',
            'htdocs/css/*.css',
            'htdocs/images/*.jpg',
            'htdocs/swf/*.swf',
            'htdocs/javascript/*.js',
            'htdocs/javascript/js-ofc-library/*.js',
            'htdocs/javascript/js-ofc-library/charts/*.js'
        ]
    }
)
