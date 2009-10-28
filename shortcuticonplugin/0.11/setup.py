#!/usr/bin/env python

from setuptools import setup
from tracshortcuticon.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracShortcutIconPlugin',
    version = '0.1.' + rev,
    packages = ['tracshortcuticon'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Configurables shortcut icons for Trac.",
    url = 'http://www.trac-hacks.org/wiki/ShortcutIconPlugin',
    license = 'GPLv3',
    keywords = 'trac plugin favicon shortcuticon',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracshortcuticon.plugin = tracshortcuticon.plugin']}
)
