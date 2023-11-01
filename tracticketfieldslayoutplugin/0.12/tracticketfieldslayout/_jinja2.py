# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re

import jinja2.ext


_inject_re = re.compile(r'(<table\s*class="(?:trac-)?properties">)(.*?)'
                        r'</table>', re.DOTALL)


def _inject_repl(match):
    groups = match.groups()
    if 'trac-properties' in groups[0]:
        return (groups[0] +
                "{% if (can_modify or can_create) and ticketfieldslayout is "
                "not undefined %}{% include 'ticketfieldslayout_form.html' %}"
                "{% else %}" + groups[1] + "{% endif %}</table>")
    else:
        return (groups[0] +
                "{% if ticketfieldslayout is not undefined %}"
                "{% include 'ticketfieldslayout_view.html' %}{% else %}" +
                groups[1] + "{% endif %}</table>")


def make_jinja2_ext(env):

    from .web_ui import TicketFieldsLayoutModule
    mod = TicketFieldsLayoutModule(env)

    class Extension(jinja2.ext.Extension):

        def preprocess(self, source, name, filename=None):
            fields, groups = mod._fields_and_groups
            if fields is groups is None:
                return source
            if name not in mod._templates:
                return source
            return _inject_re.sub(_inject_repl, source)

    return Extension
