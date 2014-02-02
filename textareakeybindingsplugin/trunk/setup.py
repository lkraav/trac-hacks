#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TextareaKeyBindings',
    version = '1.0',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'Better keybindings for <textarea> controls',
    packages = ['textareakeybindings'],
    package_data = {'textareakeybindings': ['htdocs/js/*.js',]},

    entry_points = {'trac.plugins': [
            'textareakeybindings.web_ui = textareakeybindings.web_ui',
        ]
    },
)
