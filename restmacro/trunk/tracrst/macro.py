# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2016 Philippe Normand <phil@base-art.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import inspect
import os

from trac.core import *
from trac.mimeview.rst import ReStructuredTextRenderer
from trac.util import escape
from trac.wiki.api import IWikiMacroProvider

from svn_helper import SVNHelper

__all__ = ['TracReSTMacro']

# This directory should be created on the trac instance directory
# and owned by the user running trac
RST_CACHE_DIR_NAME = 'rst_cache'


class TracReSTMacro(Component):
    """
    This Wiki macro translates ReST files hosted on the Subversion repository
    to HTML.

    Example:

    ::

      [[ReST(/trunk/README)]]

    HTML files are cached in a directory within the trac instance and kept
    up-to-date with latest corresponding ReST file revisions.

    To install:

    - install and activate this plugin
    - create a rst_cache directory owned by the user running trac in your
      trac instance
    - enjoy lazyness like a bunny on the sun :-)
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'ReST'

    def get_macro_description(self, name):
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, args):
        assert args, "Required argument: filename to dump"
        args = args.split(',')

        cache_dir = os.path.join(self.env.path, RST_CACHE_DIR_NAME)

        rst_data = ''
        try:
            for file_path in args:
                rst_data += "%s\n" % self._get_rst_data(file_path, cache_dir)

            rst_component = self.env[ReStructuredTextRenderer]
            html_data = rst_component.render(req, 'text/x-rst', rst_data)
        except:
            import cgitb, sys
            return cgitb.html(sys.exc_info())
        else:

            return html_data

    def _get_rst_data(self, file_path, cache_dir):

        repository_path = str(self.env.config.get('trac', 'repository_dir'))

        # converting out of unicode and into plain ole strings will likely cause
        # problems for someone out there, but since SVNHelper doesn't (currently)
        # accept unicode, it's not going to be any more troublesome than it
        # already is
        #file_paths = str(args)
        orig_repo = repository_path
        while not os.path.isdir(repository_path):
            # in case trac is provided with a subhiearchy of the repository
            repository_path, tail = os.path.split(repository_path)
            file_path = os.path.join(tail, file_path)
            if not repository_path:
                raise TracError("Couldn't find repository path: %s" % orig_repo)

        helper = SVNHelper(repository_path)

        if os.path.exists(cache_dir):
            rst_data = helper.cached_cat(file_path, cache_dir)
        else:
            rst_data = helper.cat(file_path)

        return rst_data
