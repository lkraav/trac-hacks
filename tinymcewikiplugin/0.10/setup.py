from setuptools import setup

PACKAGE = 'tinymcewiki'
VERSION = '0.2'

setup(name=PACKAGE, version=VERSION, packages=['tinymcewiki'],
        package_data={'tinymcewiki' : [ 'htdocs/css/*.css', 'templates/*.cs']})
