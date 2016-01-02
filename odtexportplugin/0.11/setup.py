#!/usr/bin/env python

from setuptools import setup


setup(
    name='OdtExportPlugin',
    version='0.7',
    packages=['odtexport'],
    author='Aurelien Bompard',
    author_email='aurelien@bompard.org',
    description='A plugin to export wiki pages as OpenDocument (ODT) files',
    license='Trac license',
    url='https://trac-hacks.org/wiki/OdtExportPlugin',
    entry_points={'trac.plugins': ['odtexport.odtexport=odtexport.odtexport',
                                   'odtexport.OdtTemplate=odtexport.OdtTemplate']},
    package_data={'odtexport': [
        'xsl/*.xsl',
        'xsl/document-content/*.xsl',
        'xsl/specific/*.xsl',
        'xsl/styles/*.xsl',
        'templates/*.odt',
        'templates/*.txt',
    ]},
    install_requires=['Trac', 'lxml', 'pillow', 'pytidylib'],
)
