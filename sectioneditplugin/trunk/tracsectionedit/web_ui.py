# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Optaros, Inc
# Copyright 2021 Cinc
#

import re

from trac.core import *
from trac.config import BoolOption
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, add_script_data, Chrome, ITemplateProvider, web_context
from trac.util.html import html
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.wiki.formatter import format_to_html


class JTransformer(object):
    """Class modelled after the Genshi Transformer class. Instead of an xpath it uses a
       selector usable by jQuery.
       You may use cssify (https://github.com/santiycr/cssify) to convert a xpath to a selector."""

    def __init__(self, xpath):
        self.css = xpath  # xpath must be a css selector for jQuery

    def after(self, html):
        return {'pos': 'after', 'css': self.css, 'html': html}

    def before(self, html):
        return {'pos': 'before', 'css': self.css, 'html': html}

    def empty(self):
        return {'pos': 'empty', 'css': self.css, 'html': ''}

    def prepend(self, html):
        return {'pos': 'prepend', 'css': self.css, 'html': html}

    def append(self, html):
        return {'pos': 'append', 'css': self.css, 'html': html}

    def remove(self):
        return {'pos': 'remove', 'css': self.css, 'html': ''}

    def replace(self, html):
        return {'pos': 'replace', 'css': self.css, 'html': html}


class WikiSectionEditModule(Component):
    implements(IRequestFilter, ITemplateProvider)

    preview_whole_page = BoolOption(
        'section-edit', 'preview_whole_page', True,
        'Whether to preview the entire page or just the section.')

    edit_subsections = BoolOption(
        'section-edit', 'edit_subsections', False,
        'Whether to edit all subsections or just the section.')

    # ITemplateProvider
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracsectionedit', resource_filename(__name__, 'htdocs'))]

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if re.match(r'/wiki(?:/(.+))?$', req.path_info) and \
           'WIKI_MODIFY' in req.perm:
            if req.method == 'POST' \
                    and 'section' in req.args \
                    and 'section_pre' in req.args \
                    and 'section_post' in req.args:
                section_text = req.args.get('text')
                if len(section_text) > 0 and section_text[-1] != '\n':
                    section_text += '\n'
                if len(req.args['section_pre']) > 0 and \
                        req.args['section_pre'][-1] != '\n':
                    section_text = '\n' + section_text
                req.args['section_text'] = req.args.get('text')
                req.args['text'] = "%s%s%s" % (req.args.get('section_pre'),
                                               section_text,
                                               req.args.get('section_post'))
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template and data:
            if template == 'wiki_view.html':
                page = data.get('page')
                if page and 'WIKI_MODIFY' in req.perm(page.resource):
                    add_script(req, 'tracsectionedit/js/tracsectionedit.js')
            elif template == 'wiki_edit.html' and \
                    'section' in req.args and \
                    'merge' not in req.args:

                if 'section_text' in req.args:
                    section_pre, section_text, section_post = \
                        req.args.get('section_pre'), \
                        req.args.get('section_text'), \
                        req.args.get('section_post')
                else:
                    section_pre, section_text, section_post = \
                        self._split_page_text(data['page'].text,
                                              req.args['section'])
                    section_text = ''.join(section_text)

                section_element = html.input(
                    type='hidden', name='section', id='section',
                    value=req.args.get('section'))
                pre_element = html.input(
                    type='hidden', name='section_pre', id='section_pre',
                    value=''.join(section_pre))
                post_element = html.input(
                    type='hidden', name='section_post', id='section_post',
                    value=''.join(section_post))

                section_html = html(section_element, pre_element, post_element)

                filter_lst = []
                # Safe page data for reassembling later
                # xform: '//textarea[@name="text"]'
                xform = JTransformer('textarea[name=text]')
                filter_lst.append(xform.before(to_unicode(section_html)))
                # Empty the textfield control
                filter_lst.append(xform.empty())
                # Put current section text into textfield control
                filter_lst.append(xform.append(to_unicode(section_text)))

                # Change title
                # xform: '//div[@id="content"]//h1'
                xform = JTransformer('div#content > h1')
                filter_lst.append(xform.append(": Section %s - %s" %
                                               (req.args['section'],
                                                section_text[:section_text.find('\n')].strip(" = \r\n")
                                                )))
                # Handle preview
                if not self.preview_whole_page:

                    if hasattr(Chrome, 'jenv'):
                        xform = JTransformer('div.trac-content')
                    else:
                        # xform: '//div[@class="wikipage"]'
                        xform = JTransformer('div.wikipage')

                    # Empty the textfield control
                    filter_lst.append(xform.empty())
                    # Add section text
                    page = data.get('page')
                    filter_lst.append(xform.append(format_to_html(self.env,
                                                                  web_context(req, page.resource),
                                                                  section_text)))

                add_script_data(req, {'tracsectionedit_filter': filter_lst})
                add_script(req, 'tracsectionedit/js/tracsectionedit_transform.js')

        return template, data, content_type

    # internals
    def _split_page_text(self, page_text, section):
        """Split page_text used for paragraph_edit.
        Based on http://trac.edgewall.org/ticket/6921

        @param page_text: str
        @param section: int
        @return: tuple
        """
        count = 0
        pre = []
        target = []
        post = []
        is_code_block = False
        this_heading_level = []
        section_heading_level = []
        page_list = re.split('(\r\n|\r|\n)', page_text)

        # Split page text into lists of pre, section and post text
        for i, line in enumerate(page_list):
            if is_code_block is False and re.match(r'^\s*{{{\s*$', line):
                is_code_block = True
            elif is_code_block is True and re.match(r'^\s*}}}\s*$', line):
                is_code_block = False

            match = re.match(r'^\s*(?P<heading_markup>[=#]{1,6})\s.*?', line)
            if is_code_block is False and match:
                this_heading_level = len(match.group('heading_markup'))
                count = count + 1
                if count == int(section):
                    section_heading_level = this_heading_level

            if count < int(section):
                pre.append(line)
            elif count == int(section) or \
                    (self.edit_subsections and
                     this_heading_level > section_heading_level):
                target.append(line)
            elif count > int(section):
                post = page_list[i:]
                break

        if len(target) == 0:
            raise TracError(_('The section %(num)d that you chose could not be found.',
                              num=int(section)), _('Initialization Error'))

        return pre, target, post
