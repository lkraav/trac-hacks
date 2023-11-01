#!/usr/bin/python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

NAME = 'HudsonTrac'
PACKAGE = 'HudsonTrac'
VERSION = '1.0'

extra = {}
try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
except ImportError:
    pass

setup(
    name = NAME,
    version = VERSION,
    author = "Ronald Tschalär, Dirk Stöcker",
    author_email = 'trac@dstoecker.de',
    description = "A trac plugin to add hudson build info to the trac timeline",
    license = "BSD",
    keywords = "trac plugin builds hudson",
    url = "https://trac-hacks.org/wiki/HudsonTracPlugin",
    install_requires = ['Trac>=1.6'],
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
    ],
    packages = find_packages(exclude=['*.texts*']),
    package_data = {
        'HudsonTrac' : ['htdocs/*.css', 'htdocs/*.svg', 'locale/*/LC_MESSAGES/*.mo']
    },
    entry_points = {
        'trac.plugins' : [ '%s = HudsonTrac.HudsonTracPlugin' % (PACKAGE) ]
    },
    **extra
)
