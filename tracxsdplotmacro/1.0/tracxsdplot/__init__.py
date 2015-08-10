# -*- coding: utf-8 -*-

__revision__  = '$Revision$'
__id__        = '$Id$'
__headurl__   = '$URL$'

import pkg_resources
min_trac_version = '1.0.6'
pkg_resources.require('Trac >= %s' % min_trac_version)

from tracxsdplot import *

