from trac.core import Component, implements, TracError
from trac.ticket import Ticket
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer, StreamBuffer
from genshi.builder import tag


class CatagorizedFields(Component):
    implements(ITemplateStreamFilter)

    ## ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):

        if filename != "ticket.html" and filename != 'ticket_preview.html':
            return stream

        if 'ticket' in data:
            ticket = data['ticket']

            self.fields = ['reporter', 'summary', 'owner', 'priority', 'component', 'milestone', 'serverity',
                           'keywords', 'cc', 'description']

            self.catagories = self.build_catagory()

            self.map_fields_to_catagory(self.fields, self.catagories)

            view_buffer, edit_buffer, edit_buffer2, stream = self.buffer_stream_content(self.fields, stream)

            stream = self.catagorize_ticket_view(stream, ticket, view_buffer)

            self.map_fields_to_catagory(self.fields, self.catagories)

            stream = self.catagorize_ticket_edit(stream, ticket, edit_buffer, edit_buffer2)

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

        for field in fields:

            stream |= Transformer('//th[@id="h_%s"]' % field).cut(view_buffer[field]).buffer()
            stream |= Transformer('//td[@headers="h_%s"]' % field).cut(view_buffer[field], True).buffer()

            stream |= Transformer('//label[@for="field-%s"]' % field).cut(edit_buffer[field]).buffer()
            stream |= Transformer('//*[@id="field-%s"]' % field).cut(edit_buffer2[field], True).buffer()

            if field == 'description':
                edit_buffer[field] = tag.span('')

        stream |= Transformer('//div[@id="ticket"]/table[@class="properties"]').remove()
        stream |= Transformer('//div[@id="modify"]/fieldset/table').remove()

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

            if catagory.name == '_uncatagorized':

                wrapper = tag.div(tag.table(class_='properties'), id='cat__uncatagorized', style='margin-bottom: 1em;')

            else:

                wrapper = tag.div(tag.span(catagory.display_name), tag.table(class_='properties'),
                                  id='cat_%s' % catagory.name, style='margin: 5px 0 1em 0;')

            stream |= Transformer(last_id).after(wrapper)

            return_line = True
            line_number = 1

            for field in catagory.fields:

                if len(filter(lambda x: x['name'] == field, ticket.fields)) == 1:

                    if filter(lambda x: x['name'] == field, ticket.fields)[0]['type'] == 'textarea':

                        line_number += 1

                        stream |= Transformer('//div[@id="cat_%s"]/table[@class="properties"]' % catagory.name) \
                            .append(tag.tr(view_buffer[field], id='tr_%s_%s' % (catagory.name, str(line_number))))

                        line_number += 1
                        return_line = True

                    else:

                        if return_line:

                            line_number += 1

                            stream |= Transformer('//div[@id="cat_%s"]/table[@class="properties"]' % catagory.name) \
                                .append(tag.tr(view_buffer[field], id='tr_%s_%s' % (catagory.name, str(line_number))))

                            return_line = False

                        else:

                            stream |= Transformer('//tr[@id="tr_%s_%s"]' % (catagory.name, str(line_number))) \
                                .append(view_buffer[field])

                            return_line = True

            last_id = '//div[@id="cat_%s"]' % catagory.name

        return stream

    def catagorize_ticket_edit(self, stream, ticket, edit_buffer, edit_buffer2):

        for catagory in self.catagories.values():

            if catagory.name == '_uncatagorized':

                stream |= Transformer('//div[@id="modify"]/fieldset[@id="properties"]').\
                    append(tag.table(id='edit_%s' % catagory.name, style='margin-bottom: 5px;'))

            else:

                stream |= Transformer('//div[@id="modify"]/fieldset[@id="properties"]')\
                    .append(tag.span(catagory.display_name, style='margin-left: 5px;'))

                stream |= Transformer('//div[@id="modify"]/fieldset[@id="properties"]').append(
                    tag.table(id='edit_%s' % catagory.name, style='border-top: solid 1px darkgray; margin-bottom: 5px; %s' \
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

                        stream |= Transformer('//table[@id="edit_%s"]' % catagory.name).append(tr)

                        line_number += 1
                        return_line = True

                    else:

                        if return_line:

                            line_number += 1

                            tr = tag.tr(tag.th(edit_buffer[field], class_='col1'),
                                        tag.td(edit_buffer2[field], class_='col1'),
                                        id='edit_tr_%s_%s' % (catagory.name, str(line_number)))

                            stream |= Transformer('//table[@id="edit_%s"]' % catagory.name).append(tr)

                            return_line = False

                        else:

                            stream |= Transformer('//tr[@id="edit_tr_%s_%s"]' % (catagory.name, str(line_number))) \
                                .append(tag.th(edit_buffer[field], class_='col2'))

                            stream |= Transformer('//tr[@id="edit_tr_%s_%s"]' % (catagory.name, str(line_number))) \
                                .append(tag.td(edit_buffer2[field], class_='col2'))

                            return_line = True

        return stream

class Catagory(object):

    def __init__(self, name, display_name):

        self.name = name
        self.display_name = display_name
        self.hide_condition = {}
        self.fields = []

