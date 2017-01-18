#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Jean-Philippe Save
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# INSPIRATIONS #
# Based on Whiteboard project from:
# Brian Meeker
# meeker.brian@gmail.com
# http://trac-hacks.org/wiki/WhiteboardPlugin

import sys
import os
from setuptools import setup


def read_file(file_name):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path) as fo:
        return fo.read()

min_python = (2, 6)
if sys.version_info < min_python:
    print "Ticketsboard requires Python %d.%d or later" % min_python
    sys.exit(1)
if sys.version_info >= (3,):
    print "Ticketsboard doesn't support Python 3"
    sys.exit(1)


PACKAGE = 'ticketsboardplugin'
VERSION = '1.2.3-trac0.12'

setup(
      name=PACKAGE,
      description='Gives a whiteboard view of active tickets',
      keywords='trac plugin tickets whiteboard ticketsboard',
      version=VERSION,
      url='https://www.trac-hacks.org/wiki/TicketsBoardPlugin',
      license=read_file('LICENSE'),
      author='Jean-Philippe Save',
      author_email='jp.save@gmail.com',
      long_description=read_file('README'),
      packages=[PACKAGE],
      package_data={
          PACKAGE: [
               'templates/*.html',
               'htdocs/css/*.css',
               'htdocs/js/*.js'
              ]
          },
      entry_points={
          'trac.plugins': [
              '%s.web_ui = %s.web_ui' % (PACKAGE, PACKAGE),
              '%s.assignreviewer = %s.assignreviewer' % (PACKAGE, PACKAGE)
           ]
      }
)
