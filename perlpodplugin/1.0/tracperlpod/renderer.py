# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os
from subprocess import Popen, PIPE

from pod2html import Pod2Html
from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer
from trac.util.html import escape


class PerlPodRenderer(Component):
    """HTML renderer for Plain Old Document. Add application/x-perlpod:pod to mime_map in trac.ini"""
    implements(IHTMLPreviewRenderer)

    def __init__(self):
        self.pod2html = Pod2Html()
        self.cachedir = os.path.join(os.path.abspath(self.env.path), 'cache/perlpod')
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)

    # IHTMLPreviewRenderer methods

    def get_quality_ratio(self, mimetype):
        # Since there is no official or de facto standard MIME type for POD,
        # we define tentative ones here
        if mimetype in ['application/x-perlpod', 'text/x-perlpod']:
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, rev=None):
        pod = content.read()
        html = self.pod2html.render(pod, self.cachedir)
        return html
