# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

DEFAULT_TEMPLATES = [
("defect", """= bug description =

= bug analysis =

= fix recommendation ="""),
("enhancement", """= problem =

= analysis =

= enhancement recommendation ="""),
("task", """= phenomenon =

= background analysis =

= implementation recommendation ="""),
("default", """= phenomenon =

= reason =

= recommendation ="""),
]
