#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'PencilPreview',
    version = '1.0',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'HTML Preview for Evolus Pencil .ep mockup files',
    packages = ['pencilpreview'],
    
    entry_points = {'trac.plugins': [
            'pencilpreview.preview = pencilpreview.preview',
        ]
    },
)
