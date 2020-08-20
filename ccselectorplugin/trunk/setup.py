#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

extra = {}

PACKAGE = 'cc_selector'

try:
    from trac.util.dist import get_l10n_js_cmdclass
    cmdclass = get_l10n_js_cmdclass()
    if cmdclass:
        # includes some 'install_lib' overrides,
        # i.e. 'compile_catalog' before 'bdist_egg'
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'genshi', None),
        ]
        extra['message_extractors'] = {
            PACKAGE: extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass


VERSION = '0.2.0'

setup(
    name='TracCcSelector',
    version=VERSION,
    description='Visual Cc ticket field editor for Trac',
    keywords='trac cc ticket editor',
    url='https://trac-hacks.org/wiki/CcSelectorPlugin',
    author='Vladislav Naumov',
    author_email='vnaum@vnaum.com',
    license='GPL',
    maintainer='Steffen Hoffmann',
    maintainer_email='hoff.st@web.de',
    packages=[PACKAGE],
    package_data={PACKAGE: [
        'htdocs/*.js', 'htdocs/lang_js/*.js', 'locale/*/LC_MESSAGES/*.mo',
        'locale/.placeholder', 'templates/*.html'
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
