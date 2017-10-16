#!/usr/bin/env python

from setuptools import find_packages, setup

setup(name='sensitivetickets',
      version='0.24',
      description="A trac plugin that lets you mark tickets as 'sensitive' "
                  "with a check box.  Those tickets can only be seen with "
                  "permission.",
      author='Jeff Hammel',
      maintainer='Daniel Kahn Gillmor',
      maintainer_email='dkg@fifthhorseman.net',
      url='https://trac-hacks.org/wiki/SensitiveTicketsPlugin',
      keywords='trac plugin security',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points="""
      [trac.plugins]
      sensitivetickets = sensitivetickets
      """,
      )
