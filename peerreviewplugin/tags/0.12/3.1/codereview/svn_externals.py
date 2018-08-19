# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Itamar Ostricher <itamarost@gmail.com>
# Copyright (C) 2016 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Itamar Ostricher <itamarost@gmail.com>


def parse_externals(prop_str):
    """Parse svn:externals property string and generate external references dictionaries from the valid lines
    (skip invalid).
    """
    for prop_line in prop_str.splitlines():
        prop_line = prop_line.strip().replace('\\', '/')
        if not prop_line or prop_line.startswith('#'):
            continue
        elements = prop_line.split()
        if len(elements) < 2:
            continue

        ext_dict = {}
        ext_dict['rev'] = rev_str = None
        if '://' in elements[-1]:
            # Old-style syntax
            ext_dict['dir'] = elements[0]
            ext_dict['url'] = elements[-1]
            if len(elements) >= 3:
                rev_str = ''.join(elements[1:(len(elements) == 4 and 3 or 2)])
        else:
            # New-style syntax svn >= 1.5
            ext_dict['dir'] = elements[-1]
            ext_dict['url'] = elements[-2]
            if len(elements) >= 3:
                rev_str = ''.join(elements[0:(len(elements) == 4 and 2 or 1)])
            elif '@' in ext_dict['url']:
                ext_dict['url'], rev_str = ext_dict['url'].split('@')
                rev_str = '-r%s' % (rev_str)
        if rev_str:
            if not rev_str.startswith('-r'):
                continue
            if not rev_str[2:].isdigit():
                continue
            ext_dict['rev'] = int(rev_str[2:])
        if ext_dict:
            yield ext_dict
