from setuptools import find_packages, setup

setup(name='TracNeverNotifyUpdater',
      version='1.0',
      packages=find_packages(exclude=['*.tests']),
      url='https://www.trac-hacks.org/wiki/NeverNotifyUpdaterPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
      Never send emails to the person who made the change.
      Presumably they already know they made that change.
      """,
      entry_points={
          'trac.plugins': [
              'tracnevernotifyupdater=tracnevernotifyupdater.api'
          ]
      },
      install_requires=['Trac'],
      )
