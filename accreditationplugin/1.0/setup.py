# -*- coding: utf8 -*- 

'''
Created on 2014-03-12 

@author: cauly
'''
from setuptools import find_packages, setup

setup(
    name='TracAccreditation', version='1.1',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': [
            'tracaccreditation = Accreditation',
        ],
    },
)
