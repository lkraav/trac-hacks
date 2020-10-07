#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracLatex',
    version='0.2',
    packages=['latex'],
    include_package_data=True,
    author="Jean-Guilhem Rouel",
    author_email="jean-guilhem.rouel@ercim.org",
    description="Latex support in wiki pages",
    long_description="Macro renders Latex code in wiki pages as PNG images.",
    license="GPLv2",
    keywords="trac latex macro",
    url="https://trac-hacks.org/wiki/LatexMacro",
    entry_points={
        'trac.plugins': [
            'latex.latexmacro=latex.latexmacro'
        ],
    },
    zip_safe=True
)
