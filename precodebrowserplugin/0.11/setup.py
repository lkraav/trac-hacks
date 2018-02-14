# $Id$

from setuptools import setup

PACKAGE = 'PreCodeBrowserPlugin'
VERSION = '1.0'

setup(
    name=PACKAGE,
    version=VERSION,
    author='Katherine Flavel',
    author_email='kate@elide.org',
    description='Replace tables output in the source browser with simple <pre> file listings',
    url='https://trac-hacks.org/wiki/%s' % PACKAGE,

    license='Public Domain',
    packages=['precodebrowser'],
    entry_points={'trac.plugins': '%s = precodebrowser' % PACKAGE}
)
