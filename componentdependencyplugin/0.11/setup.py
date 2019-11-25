#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


setup(name='TracComponentDependency',
      version='0.2',
      description="allows plugins to depend on other components being enabled",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='https://trac-hacks.org/wiki/ComponentDependencyPlugin',
      keywords='trac plugin',
      license="BSD 3-Clause",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'componentdependencyplugin': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      componentdependencyplugin = componentdependencies
      """,
      )

