# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from subprocess import Popen, PIPE

class Pod2Html:
    def render(self, pod, cachedir='/tmp'):
        p = Popen(["pod2html", "--cachedir=%s" % cachedir], stdin=PIPE, stdout=PIPE)
        stdout, stderr = p.communicate(pod)
        return stdout
