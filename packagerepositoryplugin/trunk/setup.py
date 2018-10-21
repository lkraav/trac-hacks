#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'PackageRepository',
    version = '1.0',
    author = 'Peter Suter',
    author_email = 'petsuter@gmail.com',
    description = 'Package Repository',
    packages = ['packagerepository', 'packagerepository.upgrades'],
    package_data = {'packagerepository': [
            'templates/*.html',
        ]
    },
    entry_points = {'trac.plugins': [
            'packagerepository.core = packagerepository.core',
            'packagerepository.admin = packagerepository.admin',
            'packagerepository.repopy = packagerepository.repopy',
            'packagerepository.repojs = packagerepository.repojs',
        ]
    },
)
