#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'TracAsciidoctorPlugin'
VERSION = '0.1'

setup(  name=PACKAGE, version=VERSION,
        author = "Sergio Talens-Oliag",
        author_email = 'sto@iti.es',
        url = 'http://trac-hacks.org/wiki/TracAsciidoctorPlugin',
        description = 'Renders Asciidoc pages to HTML using Asciidoctor',
        license='BSD',
       	packages=['tracasciidoctor'],
        package_data={'tracasciidoctor': ['htdocs/css/*.css',], },
        entry_points = """
          [trac.plugins]
          tracasciidoctor.tracasciidoctor = tracasciidoctor.tracasciidoctor
        """,
)

