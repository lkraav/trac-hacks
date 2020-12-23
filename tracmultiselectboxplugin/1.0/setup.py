#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

VERSION = '0.5.2'

try:
    import pypandoc  
    LONG_DESCRIPTION = '\n'.join([
        pypandoc.convert('README.md', 'rst'),
        pypandoc.convert('CHANGELOG.md', 'rst'),
    ])
except (IOError, ImportError):
    LONG_DESCRIPTION = ''

REQUIRES = [
    'Trac >= 1.0.0',
]

CLASSIFIERS = [
    'Framework :: Trac',
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'License :: OSI Approved :: Apache Software License',
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development',
]

EXTRA_PARAMETER = {}
try:
    # Adding i18n/l10n to Trac plugins (Trac >= 0.12)
    # see also: http://trac.edgewall.org/wiki/CookBook/PluginL10N
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:  # Yay, Babel is there, we've got something to do!
        EXTRA_PARAMETER['cmdclass'] = cmdclass
        EXTRA_PARAMETER['message_extractors'] = {
            'multiselectbox': [
                ('**.py', 'python', None),
            ]
        }
except ImportError:
    pass

setup(
    name='TracMultiSelectBoxPlugin',
    version=VERSION,
    description='Provide simple multiple select values field',
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    keywords=['trac', 'plugin', 'ticket', 'multiselect'],
    author='Tetsuya Morimoto',
    author_email='tetsuya dot morimoto at gmail dot com',
    url='http://trac-hacks.org/wiki/TracMultiSelectBoxPlugin',
    license='Apache License 2.0',
    packages=['multiselectbox'],
    package_data={
        'multiselectbox': [
            'htdocs/*.js',
            'htdocs/*.css',
            'locale/*/LC_MESSAGES/*.po',
            'locale/*/LC_MESSAGES/*.mo',
        ],
        'patch': [
            '*.patch',
        ],
    },
    include_package_data=True,
    install_requires=REQUIRES,
    entry_points={
        'trac.plugins': [
            'multiselectbox.filter = multiselectbox.filter',
        ]
    },
    **EXTRA_PARAMETER
)
