# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import pkg_resources
pkg_resources.require('Trac>=0.12,<1.3')
del pkg_resources

from talm_importer.importer import *
