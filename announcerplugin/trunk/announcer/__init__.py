# -*- coding: utf-8 -*-
#
# Copyright (c) 2008, Stephen Hansen
# Copyright (c) 2009, Robert Corsaro
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import pkg_resources
pkg_resources.require('Trac >= 1.0')

__version__ = __import__('pkg_resources').get_distribution('TracAnnouncer').version
