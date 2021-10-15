#!/usr/bin/env python

from setuptools import setup

from trac.dist import get_l10n_cmdclass


extra = {}
cmdclass = get_l10n_cmdclass()
if cmdclass:
    extra['cmdclass'] = cmdclass


setup(name='TracCustomFieldAdmin',
      version='0.4.0',
      packages=['customfieldadmin'],
      author='CodeResort.com & Optaros.com',
      description='Admin panel for managing Trac ticket custom fields.',
      url='https://trac-hacks.org/wiki/CustomFieldAdminPlugin',
      license='BSD',
      classifiers=[
          'Framework :: Trac',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
      ],
      entry_points={
          'trac.plugins': [
              'customfieldadmin.api = customfieldadmin.api',
              'customfieldadmin.admin = customfieldadmin.admin',
          ]
      },
      exclude_package_data={'': ['tests/*']},
      test_suite = 'customfieldadmin.tests.test_suite',
      tests_require = [],
      package_data={
          'customfieldadmin' : [
              'htdocs/css/*.css',
              'htdocs/js/*.js',
              'templates/*.html',
              'locale/*/LC_MESSAGES/*.mo'
          ]
      },
      extras_require = {'Babel': 'Babel>=0.9.6'},
      **extra
 )
