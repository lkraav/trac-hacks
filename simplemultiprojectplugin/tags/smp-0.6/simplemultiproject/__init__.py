# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

import pkg_resources

from model import *
from environmentSetup import *
from admin import *
from admin_command import SmpAdminCommands
from admin_filter import *
from milestone import *
from roadmap import *
from ticket import *
from timeline import *
from version import *


__version__ = __import__('pkg_resources').get_distribution('SimpleMultiProject').version

pkg_resources.require('Trac >= 1.0')
