# -*- coding: utf8 -*-

'''
Created on 2014-03-17

@author: cauly
'''

from trac.core import Component, implements, TracError
from trac.ticket import Ticket
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer, StreamBuffer
from genshi.builder import tag
import time

class CatagorizedFields(Component):
    implements(ITemplateStreamFilter)

    ## ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):

        if filename != "ticket.html" and filename != 'ticket_preview.html':
            return stream

        if 'ticket' in data:

            t = time.time()

            ticket = data['ticket']

            self.fields = ['reporter', 'summary', 'owner', 'priority', 'component', 'milestone', 'severity',
                           'keywords', 'cc', 'description']

            self.catagories = self.build_catagory()

            self.map_fields_to_catagory(self.fields, self.catagories)

            view_buffer, edit_buffer, edit_buffer2, stream = self.buffer_stream_content(self.fields, stream)

            stream = self.catagorize_ticket_view(stream, ticket, view_buffer)

            self.map_fields_to_catagory(self.fields, self.catagories)

            stream = self.catagorize_ticket_edit(stream, ticket, edit_buffer, edit_buffer2)

            print "Catagorized Fields used time: " + str(time.time() - t)

        return stream

    ## ITemplateProvider

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return []

    def build_catagory(self):
        '''
            build catagories from config

            e.g.
            [catagroy-fields]
            cat1 = catagory1
            cat1.hide_when_type = bug
            cat1.hide_when_status = new, closed 
        '''

        catagories = {"_uncatagorized": Catagory('_uncatagorized', '')}

        for opt_name, opt_value in self.config.options('catagorized-fields'):

            if not '.' in opt_name:

                catagories[opt_name] = Catagory(opt_name, opt_value)

            elif opt_name.split('.')[-1].startswith('hide_when_'):

                catagory_name, hide_condition = opt_name.split('.')

                catagories[catagory_name].hide_condition.setdefault(hide_condition[len('hide_when_'):], []) \
                    .extend(filter(lambda x: x != '', opt_value.strip().split(',')))

        return catagories

    def map_fields_to_catagory(self, fields, catagories):
        '''
            let's collect all custom fields and findout which fields do we have
        
            something like:
        
            [ticket-custom]
            test = text
            test.label = Test
            test.catagory = cat1
        '''

        catagorized = []

        for opt_name, opt_value in self.config.options('ticket-custom'):

            if not '.' in opt_name and not opt_name in fields:

                fields.append(opt_name)

            elif opt_name.split('.')[-1] == 'catagory' and opt_value.strip() in catagories.keys():

                if not opt_name.split('.')[0] in catagories[opt_value].fields:

                    catagories[opt_value].fields.append(opt_name.split('.')[0])

                catagorized.append(opt_name.split('.')[0])

        for item in fields:

            if not item in catagorized and not item in catagories['_uncatagorized'].fields:

                catagories['_uncatagorized'].fields.append(item)

    def buffer_stream_content(self, fields, stream):

        view_buffer = dict([[field, StreamBuffer()] for field in fields])
        edit_buffer = dict([[field, StreamBuffer()] for field in fields])
        edit_buffer2 = dict([[field, StreamBuffer()] for field in fields])

        vb = StreamBuffer()
        eb = StreamBuffer()

        stream |= Transformer('//div[@id="ticket"]/table[@class="properties"]').cut(vb).buffer()
        stream |= Transformer('//div[@id="modify"]/fieldset/table').cut(eb).buffer()

        for field in fields:

            vb |= Transformer('//th[@id="h_%s"]' % field).cut(view_buffer[field]).buffer()
            vb |= Transformer('//td[@headers="h_%s"]' % field).cut(view_buffer[field], True).buffer()

            eb |= Transformer('//label[@for="field-%s"]' % field).cut(edit_buffer[field]).buffer()
            eb |= Transformer('//*[@id="field-%s"]' % field).cut(edit_buffer2[field], True).buffer()

            if field == 'description':
                edit_buffer[field] = tag.span('')

        return view_buffer, edit_buffer, edit_buffer2, stream

    def catagory_is_hidden(self, catagory, ticket):

        for cond, list in catagory.hide_condition.items():

            if len(filter(lambda x: x['name'] == cond, ticket.fields)) == 1 and ticket[cond] in list:

                return True

        return False

    def catagorize_ticket_view(self, stream, ticket, view_buffer):

        last_id = '//h1[@id="trac-ticket-title"]'

        for catagory in self.catagories.values():

            if self.catagory_is_hidden(catagory, ticket):

                continue

            content = tag.table(class_='properties')

            if catagory.name == '_uncatagorized':

                wrapper = tag.div(content, id='cat__uncatagorized', style='margin-bottom: 1em;')

            else:

                wrapper = tag.div(tag.span(catagory.display_name), content,
                                  id='cat_%s' % catagory.name, style='margin: 5px 0 1em 0;')

            return_line = True
            line_number = 1
            last_line = StreamBuffer()

            for field in catagory.fields:

                if len(filter(lambda x: x['name'] == field, ticket.fields)) == 1:

                    if filter(lambda x: x['name'] == field, ticket.fields)[0]['type'] == 'textarea':

                        line_number += 1

                        content.append(tag.tr(view_buffer[field], id='tr_%s_%s' % (catagory.name, str(line_number))))

                        line_number += 1
                        return_line = True

                    else:

                        if return_line:

                            line_number += 1

                            last_line = tag.tr(view_buffer[field], id='tr_%s_%s' % (catagory.name, str(line_number)))

                            content.append(last_line)

                            return_line = False

                        else:

                            last_line.append(view_buffer[field])

                            return_line = True

            stream |= Transformer(last_id).after(wrapper)

            last_id = '//div[@id="cat_%s"]' % catagory.name

        return stream

    def catagorize_ticket_edit(self, stream, ticket, edit_buffer, edit_buffer2):

        for catagory in self.catagories.values():

            if catagory.name == '_uncatagorized':

                content = tag.table(id='edit_%s' % catagory.name, style='margin-bottom: 5px;')
                wrapper = content

            else:

                content = tag.table(id='edit_%s' % catagory.name, style='border-top: solid 1px darkgray; margin-bottom: 5px;')

                wrapper = tag.div(tag.span(catagory.display_name, content, style='margin-left: 5px; %s' \
                                  % ('display: none;' if self.catagory_is_hidden(catagory, ticket) else '')))

            return_line = True
            line_number = 1

            for field in catagory.fields:

                if len(filter(lambda x: x['name'] == field, ticket.fields)) == 1:

                    if field == 'summary' or field == 'reporter' or \
                        filter(lambda x: x['name'] == field, ticket.fields)[0]['type'] == 'textarea':

                        line_number += 1

                        tr = tag.tr(tag.th(edit_buffer[field], class_='col1'),
                                    tag.td(edit_buffer2[field], class_='col1', colspan='3'),
                                    id='edit_tr_%s_%s' % (catagory.name, str(line_number)))

                        content.append(tr)

                        line_number += 1
                        return_line = True
                        last_line = StreamBuffer()

                    else:

                        if return_line:

                            line_number += 1

                            last_line = tag.tr(tag.th(edit_buffer[field], class_='col1'),
                                        tag.td(edit_buffer2[field], class_='col1'),
                                        id='edit_tr_%s_%s' % (catagory.name, str(line_number)))

                            content.append(last_line)

                            return_line = False

                        else:

                            last_line.append(tag.th(edit_buffer[field], class_='col2'))

                            last_line.append(tag.td(edit_buffer2[field], class_='col2'))

                            return_line = True

            stream |= Transformer('//div[@id="modify"]/fieldset[@id="properties"]').append(wrapper)

        return stream

class Catagory(object):

    def __init__(self, name, display_name):

        self.name = name
        self.display_name = display_name
        self.hide_condition = {}
        self.fields = []

