# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name         = 'TracXsdPlot', version='0.1',
    author       = 'Theodor Norup',
    author_email = 'theodor.norup@gmail.com',
    homepage     = 'https://trac-hacks.org/wiki/TracXsdPlotMacro',
    license      = 'BSD 3-clause',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        tracxsdplot = tracxsdplot
    """,
)
