# -*- coding: utf-8 -*-

from itertools import groupby

from genshi.builder import tag

from trac.core import *
from trac.web.chrome import (Chrome, add_script, add_script_data,
                             add_stylesheet, ITemplateProvider)
from trac.wiki.api import parse_args
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase

from cards.model import Card

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

    def expand_macro(self, formatter, name, content):
        args, kw = parse_args(content)
        args = [arg.strip() for arg in args]

        stack_ids = kw.get('stack', '').split('|')
        if not stack_ids:
            raise TracError('Missing stack names')

        cards = Card.select_by_stacks(self.env, stack_ids)
        cards_by_stack = dict((stack, list(cards)) for stack, cards in groupby(cards, lambda c: c.stack))

        labels = [label for label in kw.get('label', '').split('|') if label]
        labels = dict(zip(stack_ids, labels + stack_ids[len(labels):]))

        width = int(kw.get('width', 400))

        req = formatter.req
        context = formatter.context

        board_data = {
            'form_token': req.form_token,
            'api_url': formatter.href('card'),
            'cards_by_id': dict((card.id, card.serialized(self.env, context)) for card in cards)
        }
        board_data_id = '%012x' % id(board_data)
        
        chrome = Chrome(self.env)
        add_stylesheet(req, 'cards/css/cards.css')
        chrome.add_jquery_ui(req)
        add_script_data(req, {'cards_%s' % board_data_id: board_data})
        add_script(req, 'cards/js/cards.js')

        def format_cards(stack):
            return [(card, format_to_html(self.env, context, card.title))
                    for card in cards_by_stack.get(stack, [])]
        
        data = {
            'board_data_id': board_data_id,
            'stack_ids': stack_ids,
            'cards_by_stack': cards_by_stack,
            'labels': labels,
            'width': width,
            'format_cards': format_cards,
        }
        return chrome.render_template(req, 'cards_macro.html', data, 'text/html', True)
        #return tag.div(class_='trac-cards-board',
        #               id='trac-cards-%s' % board_data_id,
        #               style='width:%spx' % width)(
        #        tag.div(class_='trac-cards-stack-titles')(
        #            tag.h2(labels[stack]) for stack in stack_ids
        #        ),
        #        tag.div(class_='trac-cards-stacks')(
        #            [tag.div(class_='trac-cards-stack')(
        #                [tag.div(class_='trac-card-slot')(
        #                    tag.div(class_='trac-card')(
        #                    format_to_html(self.env, context, card.title)))
        #                 for card in cards_by_stack.get(stack, [])])
        #         for stack in stack_ids]))
