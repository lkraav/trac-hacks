from setuptools import setup

PACKAGE = 'TracSVNAuthz'
VERSION = '1.2.0.0'

setup(
    name=PACKAGE,
    version=VERSION,
    author='Ian Jones',
    author_email='ian.trachacks@shrtcww.com',
    maintainer='Robert Barsch',
    maintainer_email='barsch@lmu.de',
    description="A interface to edit Subversion authorization (authz) "
                "file via admin panel",
    license='3-Clause BSD',
    keywords='trac plugin SVN authz',
    url='https://trac-hacks.org/wiki/TracSvnAuthzPlugin',
    packages=['svnauthz'],
    entry_points={'trac.plugins': '%s = svnauthz.svnauthz' % PACKAGE},
    package_data={'svnauthz': ['templates/*.html']},
    install_requires=['Trac'],
)
