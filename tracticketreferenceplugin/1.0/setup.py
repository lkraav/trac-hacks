#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

def _long_description(*filenames):

    def iter_content(filenames):
        for filename in filenames:
            try:
                with open(filename) as f:
                    yield f.read()
            except EnvironmentError:
                pass

    return "\n\n".join(iter_content(filenames)).rstrip()


VERSION = "0.5.2"

LONG_DESCRIPTION = _long_description("README.txt", "CHANGELOG.txt")

REQUIRES = [
    "Trac >= 0.12",
]

CLASSIFIERS = [
    "Framework :: Trac",
    "Development Status :: 4 - Beta",
    "Environment :: Web Environment",
    "License :: OSI Approved :: Apache Software License",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    "Topic :: Software Development",
]

EXTRA_PARAMETER = {}
try:
    # Adding i18n/l10n to Trac plugins (Trac >= 0.12)
    # see also: http://trac.edgewall.org/wiki/CookBook/PluginL10N
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:  # Yay, Babel is there, we"ve got something to do!
        EXTRA_PARAMETER["cmdclass"] = cmdclass
        EXTRA_PARAMETER["message_extractors"] = {
            "ticketref": [
                ("**.py", "python", None),
            ]
        }
except ImportError:
    pass

setup(
    name="TracTicketReferencePlugin",
    version=VERSION,
    description="Provides support for ticket cross reference for Trac",
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    keywords=["trac", "plugin", "ticket", "cross-reference"],
    author="Tetsuya Morimoto",
    author_email="tetsuya.morimoto@gmail.com",
    url="https://trac-hacks.org/wiki/TracTicketReferencePlugin",
    license="Apache License 2.0",
    packages=["ticketref"],
    package_data={
        "ticketref": [
            "htdocs/*.js",
            "htdocs/*.css",
            "locale/*/LC_MESSAGES/*.po",
            "locale/*/LC_MESSAGES/*.mo",
        ],
    },
    include_package_data=True,
    install_requires=REQUIRES,
    entry_points={
        "trac.plugins": [
            "ticketref.web_ui = ticketref.web_ui",
            "ticketref.api = ticketref.api",
        ]
    },
    **EXTRA_PARAMETER
)
