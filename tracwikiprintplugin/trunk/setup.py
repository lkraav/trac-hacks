# -*- coding: utf-8 -*-
# Copyright (c) 2021 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='TracWikiPrint',
    version='4.0.0',
    packages=['tracpdf'],
    package_data={
        'tracpdf': ['templates/*.html', 'htdocs/css/*.css'],
    },
    install_requires=['pdfkit', 'trac'],
    author='Cinc-th',
    author_email='',
    maintainer="Cinc-th",
    license='BSD',
    url="http://trac-hacks.org/wiki/TracWikiPrintPlugin",
    description='Create PDF files from Tracs wiki pages',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='PDF wiki trac plugin',
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Plugins',
                 'Environment :: Web Environment',
                 'Framework :: Trac',
                 'Intended Audience :: End Users/Desktop',
                 'License :: OSI Approved :: BSD License',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 ],
    entry_points={'trac.plugins': [
        'tracpdf.wikiprint = tracpdf.wikiprint',
        'tracpdf.admin = tracpdf.admin',
        'tracpdf.pdfbook = tracpdf.pdfbook',
    ]},
    test_suite='tests'
)
