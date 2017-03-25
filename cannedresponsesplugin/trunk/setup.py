#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'CannedResponsesPlugin',
    version = '0.11.1',
    packages = ['CannedResponsesPlugin'],

    author = "Daniel Atallah",
    author_email = "datallah@pidgin.im",
    url = 'https://trac-hacks.org/wiki/CannedResponsesPlugin',
    description = "Allows defining and using canned responses for tickets.",
    long_description = """This plugin allows the administrator to define a list \
                          of canned responses.  The administrator or others with \
                          appropriate ticket permissions can use the canned \
                          response to close the ticket or place it in a pending \
                          status with the appropriate canned response as a comment.""",

    license = "BSD",

    entry_points = {
        'trac.plugins': [
             'CannedResponsesPlugin.plugin = CannedResponsesPlugin.plugin'
         ]
    },
)
