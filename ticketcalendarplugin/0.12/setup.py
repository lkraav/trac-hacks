#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

def main():
    from setuptools import find_packages, setup

    extra = {}
    try:
        from trac.util.dist import get_l10n_cmdclass
    except ImportError:
        pass
    else:
        cmdclass = get_l10n_cmdclass()
        if cmdclass:
            extra['cmdclass'] = cmdclass
            extractors = [
                ('**.py', 'python', None),
                ('**/templates/**.html', 'genshi', None),
            ]
            extra['message_extractors'] = {
                'ticketcalendar': extractors,
            }

    extra.setdefault('cmdclass', {})

    setup(
        name='TicketCalendarPlugin',
        version='0.12.0.4',
        author='OpenGroove,Inc.',
        author_email='trac@opengroove.com',
        maintainer='Jun Omae',
        maintainer_email='jun66j5@gmail.com',
        url='https://trac-hacks.org/wiki/TicketCalendarPlugin',
        description='Provide ticket calendar in box calendar, list and macro',
        license='BSD',  # the same as Trac
        classifiers=[
            'Framework :: Trac',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
        ],
        packages=find_packages(exclude=['*.tests*']),
        zip_safe=True,
        package_data={
            'ticketcalendar': [
                'templates/genshi/*.html',
                'templates/jinja2/*.html',
                'htdocs/js/*.js',
                'htdocs/css/*.*',
                'htdocs/css/images/*.*',
                'locale/*/LC_MESSAGES/*.mo',
                ]
            },
        entry_points={
            'trac.plugins': [
                'ticketcalendar.web_ui = ticketcalendar.web_ui',
                ],
            },
        **extra)

if __name__ == '__main__':
    main()
