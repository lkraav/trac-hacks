# -*- coding: utf8 -*-
#
# Copyright (C) Cauly Kan, mail: cauliflower.kan@gmail.com
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.


'''
Created on 2014-03-15

@author: cauly
'''

from trac.core import Component, implements, TracError
from trac.ticket import Ticket
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer, StreamBuffer
from genshi.builder import tag

class Accreditation(Component):
    implements(ITemplateStreamFilter)

    def filter_stream(self, req, method, filename, stream, data):

        if filename != "ticket.html" and filename != 'ticket_preview.html' or not 'ticket' in data:
            return stream

        ticket = data['ticket']

        accdivheader = tag.h3(tag.a('Accreditation', href='#accreditation_wrapper'), class_='foldable')
        createacc = tag.div(
            tag.form(
                tag.fieldset(
                    tag.table(
                        tag.tr(tag.td(tag.label('Accreditation Name:'), tag.input(type_='text', name='acc_name'))),
                        tag.tr(tag.td(tag.label('Participants:'), tag.input(type_='text', name='acc_person')))),
                    tag.div(tag.input(type_='submit', value='Submit', name='submit'), class_='buttons'),
                id='accreditationform', method='POST', action='/accreditation/?ticket=' + str(ticket.id))))
        acclist = tag.div()
        acccontent = tag.div(createacc, acclist, id='accreditation')
        accdiv = tag.div(accdivheader, acccontent, id='accreditation_wrapper')

        stream |= Transformer('//div[@id="ticket"]').after(accdiv)
        return stream