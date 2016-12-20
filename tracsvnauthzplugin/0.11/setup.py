from setuptools import setup

PACKAGE = 'TracSVNAuthz'
VERSION = '0.11.1.1'

setup(
    name = PACKAGE,
    version = VERSION,
    author = "Ian Jones",
    author_email = "ian.trachacks@shrtcww.com",
    maintainer = "Robert Barsch",
    maintainer_email = "barsch@lmu.de",
    description = "A interface to edit Subversion authorization (authz) file via admin panel",
    license = "BSD",
    keywords = "trac plugin SVN authz",
    url = "http://trac-hacks.org/wiki/TracSvnAuthzPlugin",
    packages=['svnauthz'],
    entry_points={'trac.plugins': '%s = svnauthz' % PACKAGE},
    package_data={'svnauthz': ['templates/*.html']},
)