#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'TracContactForm'

setup(
    name=PACKAGE,
    version=0.2,
    author="Sebastian Krysmanski",
    url="https://trac-hacks.org/wiki/ContactFormPlugin",
    description="A contact form to contact the project team members.",
    keywords="trac plugins email",
    license="Modified BSD",
    install_requires=['Trac'],
    zip_safe=True,
    packages=['contactform'],
    package_data={'contactform': ['templates/*']},
    entry_points={'trac.plugins': '%s = contactform.web_ui' % PACKAGE},
)
