#!/usr/bin/python3
# -*- coding: utf-8 -*-

from setuptools import setup

extra = {}

PACKAGE = 'cc_selector'
VERSION = '0.3'

extra = {}
try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
except ImportError:
    pass

setup(
    name='TracCcSelector',
    version=VERSION,
    description='Visual Cc ticket field editor for Trac',
    keywords='trac cc ticket editor',
    url='https://trac-hacks.org/wiki/CcSelectorPlugin',
    author='Vladislav Naumov',
    license='GPL',
    maintainer='Dirk Stöcker',
    maintainer_email='trachacks@dstoecker.de',
    packages=[PACKAGE],
    package_data={PACKAGE: [
        'htdocs/*.js', 'htdocs/*.css', 'locale/*/LC_MESSAGES/*.mo', 'templates/*.html'
        ]},
    zip_safe=True,
    entry_points={
        'trac.plugins': [
            'cc_selector.cc_selector=cc_selector.cc_selector'
        ]},
    install_requires=['Trac'],
    extras_require={'Babel': 'Babel>=0.9.5'},
    **extra
)
