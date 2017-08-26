# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.config import *
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer


class ForcePreview(Component):
    """Force the user to preview changes before being able to modify/create
    tickets or submit Wiki changes."""
    implements(ITemplateStreamFilter)

    # TODO Finish implementing this.
#    diff_threshold = IntOption('force_ticket_preview', 'diff_threshold', 3,
#        doc='Maximum number of changed lines allowed before preview is forced.')

    def filter_stream(self, req, method, filename, stream, data):
        transform = None
        if filename == 'ticket.html' and 'preview' not in req.args:
            stream |= Transformer('//input[@value="Create ticket" or @value="Submit changes"]').attr('disabled', True)
        elif filename == 'wiki_edit.html' and 'preview' not in req.args and 'diff' not in req.args and 'merge' not in req.args:
            stream |= Transformer('//input[@id="save"]').attr('disabled', True)
        return stream
