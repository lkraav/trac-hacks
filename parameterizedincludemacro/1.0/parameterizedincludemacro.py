# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 Zaber Technologies Inc. <http://zaber.com>.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. The name of the author may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Signed-Off-By: Christopher Head <chead@zaber.com>
#

import trac.mimeview.api
import trac.wiki.formatter
import trac.wiki.macros
import trac.wiki.model

author = "Christopher Head"
version = "1.0 ($Rev$)"
license = "BSD"
url = "https://trac-hacks.org/wiki/ParameterizedIncludeMacro"


class ParameterizedIncludeMacro(trac.wiki.macros.WikiMacroBase):
    """
    Includes one wiki page in another, with parameter substitution.

    Use as follows:
    {{{
    [[ParameterizedInclude(PageName,Arg1,Arg2,Arg3,…)]]
    }}}

    Within the included page, {{1}}, {{2}}, {{3}}, … are replaced with the
    values passed as Arg1, Arg2, Arg3, and so on.
    """

    def expand_macro(self, formatter, name, content):
        args = [x.strip() for x in content.split(",")]
        if len(args) < 1:
            return trac.wiki.formatter.system_message("No page specified")
        page_name = args[0]
        page = trac.wiki.model.WikiPage(self.env, page_name, None)
        if "WIKI_VIEW" not in formatter.perm(page.resource):
            return ""
        if not page.exists:
            return trac.wiki.formatter.system_message("Wiki page \"%s\" does not exist" % page_name)
        text = page.text
        for i in range(1, len(args)):
            text = text.replace("{{%d}}" % i, args[i])
        return trac.mimeview.api.Mimeview(self.env).render(trac.mimeview.api.Context.from_request(formatter.req, "wiki", page_name), "text/x-trac-wiki", text)
