from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, add_script_data, add_stylesheet
from trac.ticket.api import ITicketManipulator
from trac.config import Option, IntOption, BoolOption, ListOption

from genshi.builder import tag
from genshi.filters.transform import Transformer

import time
from traceback import format_exc
import re

class MultiSelectFieldModule(Component):
    """A trac plugin implementing a custom ticket field that can hold multiple predefined values."""

    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider)

    option_simple_selection = BoolOption('multiselectfield', 'simple_selection', False,
        doc="Force using a simple standard html multiselect box.")

    option_delimiter = Option('multiselectfield', 'data_delimiter', ' ',
        doc="The delimiter that is used when storing the data (as the selected options are appended to a "
            "single custom text field). Space is used by default as values separated by space will be "
            "recognized by the custom text field as separate values. "
            "NOTE: changing this option when there is already data saved with other options value is probably not good idea")

    option_strip_whitespace = BoolOption('multiselectfield', 'strip_whitespace', True,
        doc="Defined whether whitespace in the names of the predefined selectable values is removed before saving the data. "
            "This should be enabled when using white space as data delimiter. "
            "NOTE: changing this option when there is already data saved with other options value is probably not good idea")

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        mine = ['/newticket', '/ticket', '/simpleticket']

        match = False
        for target in mine:
            if req.path_info.startswith(target):
                match = True
                break

        if match:
            add_script_data(req, {'multiselectfieldDelimiter': self.option_delimiter or ' '})
            add_script_data(req, {'multiselectfieldSimple': self.option_simple_selection})

            if not self.option_simple_selection:
                add_script(req, 'multiselectfield/chosen.jquery.min.js')
                add_stylesheet(req, 'multiselectfield/chosen.min.css')

            add_script(req, 'multiselectfield/multiselectfield.js')

        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):

        if filename == 'ticket.html':
            for field in list(self._multi_select_fields()):
                #
                # For all multiselect fields:
                #   The actual data is a standard custom text field containing something like "value1 value2 value3".
                #   This custom field uses the "list" type so each value separated by whitespace is treated as
                #   a separate value. We hide that field from the user and and another "select" element after it with
                #   multiple selection enabled.

                options = self.config.get('ticket-custom', field + '.options').split('|')
                options_html = tag()
                for option in options:
                    if self.option_strip_whitespace:
                        option_without_white_space = "_".join(option.split())
                        options_html(tag.option(option, value=option_without_white_space))
                    else:
                        options_html(tag.option(option, value=option))

                stream = stream | Transformer('//input[@name="field_' + field + '"]') \
                                  .attr('style', 'display:none;') \
                                  .after(tag.select(multiple="multiple", class_="multiselect", style="width:100%;")(options_html))

        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('multiselectfield', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # Internal methods
    def _multi_select_fields(self):
        for key, value in self.config['ticket-custom'].options():
            if key.endswith('.multiselect') and value == "true":
                yield key.split('.', 1)[0]

