#!/usr/bin/env python

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, macrorev, __revision__ ) )

setup(
    name         = 'TracExtractUrl',
    version      = '0.3',
    packages     = ['tracextracturl'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = 'Provides `extract_url` method to extract the URL from TracWiki links.',
    url          = 'http://www.trac-hacks.org/wiki/ExtractUrlPlugin',
    download_url = 'http://trac-hacks.org/svn/extracturlplugin/releases/',
    license      = 'GPLv3',
    keywords     = 'trac plugin extract url',
    classifiers  = ['Framework :: Trac'],
    zip_safe     = False,
    entry_points = {'trac.plugins': [
        'tracextracturl.extracturl = tracextracturl.extracturl',
        'tracextracturl.macro      = tracextracturl.macro',
      ]}
)

