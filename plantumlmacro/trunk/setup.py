#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Polar Technologies - www.polartech.es
# Copyright (C) 2010 Alvaro J Iradier <alvaro.iradier@polartech.es>
# Copyright (C) 2012-2017 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name="TracPlantUml",
    version=2.3,
    packages=['plantuml'],
    author="Alvaro J. Iradier",
    author_email="alvaro.iradier@polartech.es",
    maintainer="Ryan J Ollos",
    maintainer_email='ryan.j.ollos@gmail.com',
    description="A macro to include diagrams from PlantUML",
    license="3-Clause BSD",
    keywords="trac macro uml plantuml embed include",
    url="https://trac-hacks.org/wiki/PlantUmlMacro",
    install_requires=['Trac'],
    classifiers = ['Framework :: Trac'],
    entry_points={
        "trac.plugins": [
            "plantuml.macro = plantuml.macro"
        ]
    }
)
