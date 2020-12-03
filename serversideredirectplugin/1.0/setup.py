#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 Martin Scharrer <martin@scharrer-online.de>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracServerSideRedirectPlugin',
    version='1.0.2',
    packages=['tracserversideredirect'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description="Server side redirect plugin for Trac.",
    url='https://trac-hacks.org/wiki/ServerSideRedirectPlugin',
    license='GPLv3 or 3-Clause BSD',
    zip_safe=False,
    keywords='trac plugin server redirect',
    classifiers=['Framework :: Trac'],
    dependency_links=[
        'https://trac-hacks.org/svn/extracturlplugin/0.11'
        '#egg=TracExtractUrl-0.5'],
    install_requires=['TracExtractUrl>=0.5', 'Trac'],
    entry_points={'trac.plugins': [
        'tracserversideredirect.plugin = tracserversideredirect.plugin']},
    test_suite='tracserversideredirect.tests.suite'
)
