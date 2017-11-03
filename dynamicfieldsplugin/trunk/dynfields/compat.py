# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2014 Rob Guttman <guttman@alum.mit.edu>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#


def to_list(splittable, sep=','):
    """Split a string at `sep` and return a list without any empty items.

    >>> to_list('1,2, 3,4 ')
    ['1', '2', '3', '4']
    >>> to_list('1;2; 3;4 ', sep=';')
    ['1', '2', '3', '4']
    >>> to_list('')
    []
    >>> to_list(None)
    []
    >>> to_list([])
    []
    """
    if not splittable:
        return []
    split = [x.strip() for x in splittable.split(sep)]
    return [item for item in split if item]
