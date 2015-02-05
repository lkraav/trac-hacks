'''
Created on 03.11.2014

@author: barbara.streppel
'''
from setuptools import find_packages, setup
# name can be any name.  This name will be used to create the .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='Transmanager',
    version='0.1.0',
    author='Gefasoft AG, Barbara Streppel',
    description='Plugin for managing translation files',
    url='http://www.gefasoft-muenchen.de',
    download_url='http://trac-hacks.org/wiki/TranslationManagerPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points={"trac.plugins": [
            "transmgr.main = transmgr.main",
    ]
    },
    package_data={'transmgr': [
        'htdocs/css/*.css',
        'htdocs/js/*.js',
        'templates/*.html',
        'templates/*.txt',
    ]}
)
