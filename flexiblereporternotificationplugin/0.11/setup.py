# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='FlexibleReporterNotification',
      version='0.1',
      packages=['flexiblereporternotification'],
      url='http://trac-hacks.org/wiki/FlexibleReporterNotificationPlugin',
      author='Satyam',
      entry_points={
          'trac.plugins': 'flexiblereporternotification=flexiblereporternotification.api'
      }
)
