# -*- coding: utf8 -*- 

'''
Created on 2014-03-12 

@author: cauly
'''
from setuptools import find_packages, setup

setup(
    name='TracCatagorizedFields', version='1.0',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': [
            'traccatagorizedfields = CatagorizedFields',
        ],
    },
)
