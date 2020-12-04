from setuptools import setup

PACKAGE = 'TracNeverNotifyUpdater'

setup(name=PACKAGE,
      version='1.0',
      packages=[PACKAGE],
      url='https://www.trac-hacks.org/wiki/NeverNotifyUpdaterPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
      Never send emails to the person who made the change.
      Presumably they already know they made that change.
      """,
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
      install_requires=['Trac'],
)
