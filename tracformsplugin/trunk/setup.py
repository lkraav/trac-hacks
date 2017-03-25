#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

extra = {}

try:
    from trac.util.dist import get_l10n_cmdclass

    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'genshi', None),
        ]
        extra['message_extractors'] = {
            'tracforms': extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass

VERSION = '0.5'

setup(
    name='TracForms',
    description='Universal form provider for tickets and wiki',
    version=VERSION,
    author='Rich Harkins',
    author_email='rich@worldsinfinite.com',
    maintainer='Steffen Hoffmann',
    maintainer_email='hoff.st@web.de',
    url='https://trac-hacks.org/wiki/TracFormsPlugin',
    license='GPL',
    packages=['tracforms'],
    package_data={
        'tracforms': [
            'htdocs/*', 'locale/*/LC_MESSAGES/*.mo', 'locale/.placeholder',
            'templates/*.html',
        ]
    },
    zip_safe=True,
    install_requires=['Trac'],
    extras_require={'Babel': 'Babel>= 0.9.5'},
    entry_points={
        'trac.plugins': [
            'tracforms.api = tracforms.api',
            'tracforms.formdb = tracforms.formdb',
            'tracforms.macros = tracforms.macros',
            'tracforms.web_ui = tracforms.web_ui',
        ]
    },
    **extra
)
