from setuptools import setup

PACKAGE = 'TracSVNAuthz'
VERSION = '0.10.5'

setup(
    name = PACKAGE,
    version = VERSION,
    author = "Robert Barsch",
    author_email = "barsch@lmu.de",
    description = "A interface to edit Subversion authorization (authz) file via admin panel",
    license = "BSD",
    keywords = "trac plugin SVN authz",
    url = "http://svn.geophysik.uni-muenchen.de/trac/tracmods/",
    classifiers = ['Framework :: Trac',],
    install_requires = ['TracWebAdmin'],
    packages = ['svnauthz'],
    entry_points = {'trac.plugins': '%s = svnauthz' % PACKAGE},
    package_data = {'svnauthz': ['templates/*.cs']},
)
