# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Alexander von Bremen-Kuehne
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

PACKAGE = 'TicketTeamDispatcher'
PACKAGE_SHORT = 'ttd'
VERSION = '0.3'

setup(
    name=PACKAGE,
    version=VERSION,
    packages=[PACKAGE_SHORT],
    package_data={PACKAGE_SHORT: ['templates/*.html']},
    author = 'Alexander von Bremen-Kuehne',
    url = 'http://trac-hacks.org/wiki/TicketTeamDispatcherPlugin',
    license = 'GPLv2 or later',
    description = 'Sends mails on ticket-creation to specified addresses according to the selected team.',
    install_requires = ['TracUserManagerPlugin'],
    entry_points = """
        [trac.plugins]
        %(pkg)s = %(pkg_s)s
    """ % {'pkg': PACKAGE, 'pkg_s' : PACKAGE_SHORT },
)
