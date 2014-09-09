#!/usr/bin/env python

from setuptools import find_packages, setup

version='0.2.0'

setup(name='LogWatcherPlugin',
      version=version,
      description="View any log file from disk via web UI",
      long_description="This plugin allows you to view your trac.log logfile without shell access, just via the Web-UI Admin interface. You can select to only display messages from a specified log level (e.g. only warnings), optionally including higher levels. Moreover, you may restrict the output to the latest N lines, and even filter for lines containing a specified string or even matching a regular expression.",
      author='Franz Mayer',
      author_email='franz.mayer@gefasoft.de',
      url='http://trac-hacks.org/wiki/LogWatcherPlugin',
      keywords='trac plugin log',
      license="BSD",
      install_requires = [ 'Trac>=1.0' ],
      packages=find_packages(exclude=['ez_setup', 'examples', '*tests*']),
      include_package_data=True,
      package_data={ 'logwatcher': [
          'templates/*.html',
          'htdocs/css/*.css',
          ] },
      zip_safe=True,
      entry_points={'trac.plugins': [
            'logwatcher.api = logwatcher.api',
            'logwatcher.web_ui = logwatcher.web_ui',
            'logwatcher.app_versions = logwatcher.app_versions'
            ]}
#      classifiers=[
#          'Development Status :: 4 - Beta',
#          'Environment :: Web Environment',
#          'Framework :: Trac',
#          'Intended Audience :: Developers',
#          'Intended Audience :: System Administrators',
#          'License :: OSI Approved :: GNU General Public License (GPL)',
#          'Natural Language :: English',
#          'Operating System :: OS Independent',
#          'Programming Language :: Python',
#          'Topic :: Software Development :: Bug Tracking',
#          'Topic :: System :: Logging',
#          'Topic :: System :: Systems Administration',
#          ]
      )
