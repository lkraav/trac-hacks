# -*- coding: utf8 -*-
#
# Copyright (C) Cauly Kan, mail: cauliflower.kan@gmail.com
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.


'''
Created on 2014-03-12 

@author: cauly
'''
from setuptools import find_packages, setup

setup(
    name='TracAccreditation', version='1.1',
    packages=find_packages(exclude=['*.tests*']),
    license = "BSD 3-Clause",
    entry_points = {
        'trac.plugins': [
            'tracaccreditation = Accreditation',
        ],
    },
)
