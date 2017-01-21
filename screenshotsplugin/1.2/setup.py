#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

from trac.util.dist import get_l10n_cmdclass

# Configure l18n message extractor.
extra = {}
cmdclass = get_l10n_cmdclass()
if cmdclass:
    extractors = [('**.py', 'python', None),
                  ('**/templates/**.html', 'genshi',
                   None)]
    extra['cmdclass'] = cmdclass
    extra['message_extractors'] = {'tracscreenshots': extractors}

setup(
    name='TracScreenshots',
    version='1.2',
    keywords='trac screenshots',
    author='Radek Bartoň',
    author_email='blackhex@post.cz',
    url='https://trac-hacks.org/wiki/ScreenshotsPlugin',
    description='Project screenshots plugin for Trac',
    license='GPL',
    packages=['tracscreenshots', 'tracscreenshots.db'],
    package_data={'tracscreenshots': [
        'templates/*.html',
        'htdocs/css/*.css',
        'htdocs/js/*.js',
        'locale/*/LC_MESSAGES/*.mo'
    ]},
    entry_points={
        'trac.plugins': [
            'TracScreenshots.api = tracscreenshots.api',
            'TracScreenshots.core = tracscreenshots.core',
            'TracScreenshots.init = tracscreenshots.init',
            'TracScreenshots.matrix_view = tracscreenshots.matrix_view',
            'TracScreenshots.wiki = tracscreenshots.wiki',
            'TracScreenshots.timeline = tracscreenshots.timeline',
            'TracScreenshots.tags = tracscreenshots.tags [Tags]'
        ]},
    install_requires=['Babel >= 0.9.6', 'Trac', 'pillow>=2'],
    extras_require={'Tags': ['TracTags']},
    **extra
)
