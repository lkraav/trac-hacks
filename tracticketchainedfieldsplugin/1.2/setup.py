#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='TracTicketChainedFields',
    version='1.2',
    author="Richard Liao",
    author_email='richard.liao.i@gmail.com',
    maintainer='Richard Liao',
    maintainer_email="richard.liao.i@gmail.com",
    description="Trac Ticket Chained Fields plugin for Trac.",
    license="BSD",
    keywords="trac ticket chained fields",
    url="https://trac-hacks.org/wiki/TracTicketChainedFieldsPlugin",
    packages=['tcf'],
    package_data={
        'tcf': [
            '*.txt',
            'templates/*.*',
            'htdocs/*.*',
            'tests/*.*'
        ]
    },
    classifiers=[
        'Framework :: Trac',
    ],
    entry_points={'trac.plugins': ['tcf=tcf.web_ui']},
)
