# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.config import BoolOption, Option
from trac.util import lazy
from trac.util.html import html as tag
from trac.web.api import IRequestFilter
from trac.web.chrome import (
    ITemplateProvider, add_script, add_script_data, add_stylesheet)


class MultiSelectFieldModule(Component):
    """A trac plugin implementing a custom ticket field that can hold
    multiple predefined values.
    """

    implements(IRequestFilter, ITemplateProvider)

    option_simple_selection = BoolOption(
        'multiselectfield', 'simple_selection', False,
        doc="Force using a simple standard html multiselect box.")

    option_delimiter = Option(
        'multiselectfield', 'data_delimiter', ' ',
        doc="""The delimiter that is used when storing the data (as the
        selected options are appended to a single custom text field).
        Space is used by default as values separated by space will be
        recognized by the custom text field as separate values.
        NOTE: changing this option when there is already data saved
        with other options value is probably not good idea
        """)

    option_strip_whitespace = BoolOption(
        'multiselectfield', 'strip_whitespace', True,
        doc="""Defined whether whitespace in the names of the predefined
        selectable values is removed before saving the data. This should
        be enabled when using white space as data delimiter. NOTE: changing
        this option when there is already data saved with other options
        value is probably not good idea
        """)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            add_script_data(req, {
                'multiselectfieldDelimiter': self.option_delimiter or ' ',
                'multiselectfieldSimple': self.option_simple_selection,
                'multiselectFields': self._multi_select_fields,
            })

            if not self.option_simple_selection:
                add_script(req, 'multiselectfield/chosen.jquery.min.js')
                add_stylesheet(req, 'multiselectfield/chosen.min.css')

            add_script(req, 'multiselectfield/multiselectfield.js')

        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('multiselectfield', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # Internal methods

    @lazy
    def _multi_select_fields(self):
        def opt_name(k):
            return k.split('.', 1)[0]

        def opts(k):
            n = opt_name(k)
            opts = self.config.getlist('ticket-custom', n + '.options', sep='|')
            if self.option_strip_whitespace:
                opts = ['_'.join(e.split()) for e in opts]
            return opts

        return {
            opt_name(k): opts(k)
            for k, v in self.config['ticket-custom'].options()
            if k.endswith('.multiselect') and v == 'true'
        }
