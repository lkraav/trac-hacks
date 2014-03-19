# -*- coding: utf8 -*- 

'''
Created on 2014-03-19 

@author: cauly
'''

from setuptools import find_packages, setup

setup(
    name='TracFieldOfTablePlugin', version='1.0',
    packages=find_packages(exclude=['*.tests*']),
    author='Cauly Kan',
    author_email='cauliflower.kan@gmail.com',
    entry_points = {
        'trac.plugins': [
            'tracfieldoftableplugin = FieldOfTable',
        ],
    },
    package_data = {'FieldOfTable': ['htdoc/*.js', 'htdoc/*.css']}
)