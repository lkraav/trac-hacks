# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Jun Omae <jun66j5@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

try:
    from trac.util.datefmt import user_time
except ImportError:
    def user_time(req, func, *args, **kwargs):
        if 'tzinfo' not in kwargs:
            kwargs['tzinfo'] = getattr(req, 'tz', None)
        return func(*args, **kwargs)
