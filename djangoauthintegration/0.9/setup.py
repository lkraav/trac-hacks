from setuptools import setup

PACKAGE = 'TracDjangoAuth'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['djangoauth'],
      entry_points={'trac.plugins': '%s = djangoauth' % PACKAGE},
)

