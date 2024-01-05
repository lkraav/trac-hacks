# -*- coding: utf-8 -*-
# Copyright (c) 2021 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import io
import os
from imp import find_module

try:
    FileNotFoundError
except NameError:
    # py2.X
    FileNotFoundError = (IOError, OSError)


def get_trac_css(env, css_file):
    """Get the contents of the given CSS file from the trac installation.

    :param env: Trac Environment object. Will be used when using local env styles.
    :param css_file: name of one of Trac CSS files, e.g. 'trac.css'
    :return content of the file as a string

    Note that the file is not taken from the current environment for now.
    """

    mod = find_module('trac')

    # TODO: check for environment CSS files first to account for local
    #       styles.
    path = os.path.join(mod[1], 'htdocs', 'css', css_file)
    try:
        with io.open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except FileNotFoundError:
        return u''


def writeResponse(req, data, httperror=200, content_type='text/plain; charset=utf-8'):
    data = data.encode('utf-8')
    req.send_response(httperror)
    req.send_header('Content-Type', content_type)
    req.send_header('Content-Length', len(data))
    req.end_headers()
    req.write(data)
