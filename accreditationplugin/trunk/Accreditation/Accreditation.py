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

import re

from trac.core import Component, implements, TracError
from trac.ticket.model import Ticket
from trac.web.api import ITemplateStreamFilter, IRequestHandler
from trac.env import IEnvironmentSetupParticipant
from genshi.filters.transform import Transformer, StreamBuffer
from genshi.builder import tag
from trac.ticket.notification import TicketNotifyEmail

class Accreditation(Component):

    implements(ITemplateStreamFilter, IEnvironmentSetupParticipant, IRequestHandler)

    def environment_created(self):

        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):

        try:

            cursor = db.cursor()

            cursor.execute('SELECT * FROM accreditation;')

            return False

        except:

            return True

    def upgrade_environment(self, db):

        cursor = db.cursor()

        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS accreditation (
                            ticket INT,
                            topic VARCHAR(100),
                            conclusion VARCHAR(50),
                            comment TEXT,
                            author TEXT);
                       """)

        cursor.execute('CREATE INDEX accreditation_ticket_index ON accreditation (ticket);')

    def match_request(self, req):

        return req.path_info.startswith('/accreditation/new') or req.path_info.startswith('/accreditation/comment')

    def process_request(self, req):

        if req.path_info.startswith('/accreditation/new') :

            id = int(req.args['ticket'])
            topic = req.args['topic']
            participants = req.args['participants'].strip().split(',')

            db = self.env.get_db_cnx()

            cursor = db.cursor()

            for item in participants:

                cursor.execute("INSERT INTO accreditation VALUES(%s, %s, '', '', %s)", (id, topic, item))

            ticket = Ticket(self.env, id)

            ticket['cc'] += ',' + ','.join(participants)

            ticket.save_changes(req.authname, "Launched New Accreditation '''%s'''" % topic)

            req.redirect('/ticket/' + str(id))

        elif req.path_info.startswith('/accreditation/comment'):

            id = int(req.args['ticket'])
            topic = req.args['topic']
            author = req.authname
            conclusion = req.args['conclusion']
            comment = req.args['comment']

            db = self.env.get_db_cnx()

            cursor = db.cursor()

            cursor.execute('UPDATE accreditation SET conclusion = %s, comment = %s WHERE ticket = %s AND topic = %s AND author = %s;',
                (conclusion, comment, id, topic, author))

            ticket = Ticket(self.env, id)

            ticket.save_changes(req.authname, "Accredited '''%s''' for \"''%s''\".\n\n%s" % (topic, conclusion, comment))

            req.redirect('/ticket/' + str(id))

    def filter_stream(self, req, method, filename, stream, data):

        if not req.path_info.startswith('/ticket') or not 'ticket' in data:
            return stream

        ticket = data['ticket']

        accdivheader = tag.h3(tag.a('Accreditation', href='#accreditation_wrapper'), class_='foldable')

        createacc = tag.div(
            tag.form(
                tag.input(type_='hidden', value=str(ticket.id), name='ticket'),
                tag.fieldset(
                    tag.table(
                        tag.tr(
                            tag.td(tag.label('Topic:')),
                            tag.td(tag.input(type_='text', name='topic'))),
                        tag.tr(
                            tag.td(tag.label('Participants:')),
                            tag.td(tag.input(type_='text', name='participants')))),
                    tag.div(tag.input(type_='submit', value='Submit', name='submit'), class_='buttons')),
                id='accreditationform', method='POST', action='/accreditation/new'))

        acclist = tag.div(
            *[tag.div(
                tag.form(
                    tag.h2(key, style='color: #884444; margin: 0.3em 0 0.4em;'),
                    tag.input(type_='hidden', value=str(ticket.id), name='ticket'),
                    tag.input(type_='hidden', value=key, name='topic'),
                    tag.table(
                        tag.tr(
                            tag.th('Author'),
                            tag.th('Conclusion'),
                            tag.th('Comment')),
                        *[tag.tr(
                            tag.td(author, style='width: 150px;'),
                            tag.td(conclusion if not req.authname == author else tag.input(type_='text', name='conclusion', value=conclusion, style='padding-left: 0; padding-right: 0; width:98%;'), style='width: 150px;'),
                            tag.td(comment if not req.authname == author else tag.input(type_='text', name='comment', value=comment, style='padding-left: 0; padding-right: 0; width: 98%;'))
                        ) for author, conclusion, comment in value],
                        class_='wiki', style='width: 100%;'),
                    tag.input(type_='submit', value='Submit', name='submit', style='margin-top: 5px; float: right;'),
                    tag.div(style='clear: both;'),
                    action='/accreditation/comment', method='POST'
                )
            ) for key, value in self._get_accreditations(ticket.id).items()]
            , class_='trac-content', style='background: none repeat scroll 0 0 #FFFFDD; border:1px solid #DDDD99;'
        )

        accdiv = tag.div(accdivheader, tag.div(createacc, acclist, id='accreditation'), id='accreditation_wrapper')

        stream |= Transformer('//div[@id="ticket"]').after(accdiv)
        return stream

    def _get_accreditations(self, id):

        db = self.env.get_db_cnx()
        result = {}

        cursor = db.cursor()

        cursor.execute('SELECT * FROM accreditation WHERE ticket = %s;', (id,))

        for ticket, topic, conclusion, comment, author in cursor:

            result.setdefault(topic, []).append((author, conclusion, comment))

        return result
