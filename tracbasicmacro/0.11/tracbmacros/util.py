
# Copyright 2009-2011 Olemis Lang <olemis at gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


r"""Helper classes and functions

Copyright 2009-2011 Olemis Lang <olemis at gmail.com>
Licensed under the Apache License
"""
__author__ = 'Olemis Lang'

from trac.core import TracError, Interface

from pkg_resources import EntryPoint

def load_object(objpath):
    r"""Dynamically load an object at a given global object path
    following `pkg_resources` syntax.
    """
    ep = EntryPoint.parse("x=" + objpath)
    return ep.load(require=False)

def load_interface(objpath):
    r"""Dynamically load a Trac interface. Raise `TracError` if path 
    leads to an invalid object.
    """
    intf = load_object(objpath)
    if not isinstance(intf, Interface):
        raise TracError('Trac interface expected at `%s`' % (objpath,), 
                        'Invalid object')
    else :
        return intf
