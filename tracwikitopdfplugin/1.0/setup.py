"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from setuptools import setup

setup(
    name='TracWikiToPdfPlugin',
    version='3.0.0',
    packages=['wikitopdf'],
    package_data={'wikitopdf': ['templates/*.html', 'htdocs/js/*.js']},
    author="Diorgenes Felipe Grzesiuk",
    author_email="diorgenes@prognus.com.br",
    description="Generating PDF files from Wiki pages",
    long_description="Setup a template file for generating the PDF file "
                     "with a cover and a licence page. ",
    license="GPL",
    keywords="trac plugin wiki pdf",
    url="https://trac-hacks.org/wiki/TracWikiToPdfPlugin",
    install_requires=['Trac'],

    entry_points={
        'trac.plugins': [
            'wikitopdf.formats   = wikitopdf.formats',
            'wikitopdf.web_ui    = wikitopdf.web_ui',
            'wikitopdf.wikitopdf = wikitopdf.wikitopdf',
        ],
    },
)
