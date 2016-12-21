# -*- coding: utf-8 -*-

from itertools import groupby

from genshi.builder import tag

from trac.config import BoolOption, IntOption
from trac.core import *
from trac.web.chrome import (Chrome, add_script, add_script_data,
                             add_stylesheet, ITemplateProvider)
from trac.wiki.api import parse_args
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase

from cards.model import Card, CardStack
from cards.core import serialized_cards_by_id, serialized_stacks_by_name


class CardsMacro(WikiMacroBase):
    """Show kanban-style stacks of cards.
   
    The arguments are:
    * `stack`: `|`-separated list of stack names. (required)
    * `width`: Width of the stacks. (Defaults to 400.)
    * `label`: `|`-separated list of labels shown instead of the stack names. (Defaults to the stack names.)
    Example:
    {{{
        [[Cards(stack=todo|active|done)]]
    }}}
    """


    auto_refresh = BoolOption('cards', 'auto_refresh', 'True',
        """Automatically poll the server to refresh all cards periodically.""")

    auto_refresh_interval = IntOption('cards', 'auto_refresh_interval', 10,
        """Interval between automatic refresh requests in seconds.""")


    def expand_macro(self, formatter, name, content):
        args, kw = parse_args(content)
        args = [arg.strip() for arg in args]

        stack_names = kw.get('stack', '').split('|')
        if not stack_names:
            raise TracError('Missing stack names')

        stacks = CardStack.select_by_names(self.env, stack_names)

        cards = Card.select_by_stacks(self.env, stack_names)

        labels = [label for label in kw.get('label', '').split('|') if label]
        labels = dict(zip(stack_names, labels + stack_names[len(labels):]))

        width = int(kw.get('width', 400))

        req = formatter.req
        context = formatter.context

        board_data = {
            'form_token': req.form_token,
            'api_url': formatter.href('card'),
            'cards_by_id': serialized_cards_by_id(cards, self.env, context),
            'stacks_by_name': serialized_stacks_by_name(stacks, stack_names),
            'auto_refresh': self.auto_refresh,
            'auto_refresh_interval': self.auto_refresh_interval,
        }
        board_data_id = '%012x' % id(board_data)
        
        chrome = Chrome(self.env)
        add_stylesheet(req, 'cards/css/cards.css')
        chrome.add_jquery_ui(req)
        add_script_data(req, {'cards_%s' % board_data_id: board_data})
        add_script(req, 'cards/js/cards.js')

        data = {
            'board_data_id': board_data_id,
            'stack_names': stack_names,
            'labels': labels,
            'width': width,
        }
        return chrome.render_template(req, 'cards_macro.html', data, 'text/html', True)
