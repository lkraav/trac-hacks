#!/usr/bin/env python
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
VERSION = '1.2.0-trac0.12'

setup(
      name=PACKAGE,
      description='Gives a whiteboard view of active tickets',
      keywords='trac plugin tickets whiteboard ticketsboard',
      version=VERSION,
      url='http://www.trac-hacks.org/wiki/TicketsBoardPlugin',
      license=read_file('LICENSE'),
      author='Jean-Philippe Save',
      author_email='jp.save@gmail.com',
      long_description=read_file('README'),
      packages=[PACKAGE],
      package_data={
          PACKAGE : [
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


#### INSPIRATIONS ####
## Based on Whiteboard project from:
## Brian Meeker
## meeker.brian@gmail.com
## http://trac-hacks.org/wiki/WhiteboardPlugin

#### AUTHORS ####
## Primary Author:
## Jean-Philippe Save
## jp.save@gmail.com
