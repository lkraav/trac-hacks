# -*- coding: utf8 -*-
#
# Copyright (C) Cauly Kan, mail: cauliflower.kan@gmail.com
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

'''
Created on 2014-03-19

@author: cauly
'''

from genshi.filters.transform import Transformer

from trac.core import Component, TracError, implements
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.model import Ticket
from trac.util import to_list
from trac.util.html import html as tag
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateStreamFilter
from trac.db import DatabaseManager
import db_default

class Accreditation(Component):

    implements(IEnvironmentSetupParticipant, IRequestHandler,
               ITemplateStreamFilter)

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):

        dburi = self.config.get('trac', 'database')
        cursor = db.cursor()
        tables = self._get_tables(dburi, cursor)
        if 'accreditation' in tables:
            return False
        else:
            return True

    def upgrade_environment(self, db=None):
        db_manager, _ = DatabaseManager(self.env)._get_connector()
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in db_default.tables:
                for sql in db_manager.to_sql(table):
                    cursor.execute(sql)

    def match_request(self, req):
        return (req.path_info.startswith('/accreditation/new') or
                req.path_info.startswith('/accreditation/comment'))

    def process_request(self, req):
        if req.path_info.startswith('/accreditation/new'):

            id = int(req.args['ticket'])
            topic = req.args['topic']
            participants = to_list(req.args.get('participants'))

            with self.env.db_transaction as db:
                for item in participants:
                    db("""
                        INSERT INTO accreditation VALUES(%s, %s, '', '', %s)
                        """, (id, topic, item))

            ticket = Ticket(self.env, id)

            ticket['cc'] += ',' + ','.join(participants)

            ticket.save_changes(req.authname,
                                "Launched New Accreditation '''%s'''" % topic)

            req.redirect(req.href('ticket', id))

        elif req.path_info.startswith('/accreditation/comment'):

            id = int(req.args['ticket'])
            topic = req.args.get('topic')
            author = req.authname
            conclusion = req.args.get('conclusion')
            comment = req.args.get('comment')
            if conclusion and comment:
                ticket_comment = "Accredited '''%s''' for \"''%s''\".\n\n%s" \
                                 % (topic, conclusion, comment)

                with self.env.db_transaction as db:
                    db("""
                        UPDATE accreditation SET conclusion = %s, comment = %s
                        WHERE ticket = %s AND topic = %s AND author = %s
                        """, (conclusion, comment, id, topic, author))
                    ticket = Ticket(self.env, id)
                    ticket.save_changes(req.authname, ticket_comment)

            req.redirect(req.href('ticket', id))

    def filter_stream(self, req, method, filename, stream, data):

        if not req.path_info.startswith('/ticket') or 'ticket' not in data:
            return stream

        ticket = data['ticket']

        accdivheader = tag.h3(
            tag.a('Accreditation', href='#accreditation_wrapper'),
            class_='foldable')

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
                id='accreditationform', method='POST', action=req.href('accreditation', 'new')))

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
                    action=req.href('accreditation', 'comment'), method='POST'
                )
            ) for key, value in self._get_accreditations(ticket.id).items()]
            , class_='trac-content', style='background: none repeat scroll 0 0 #FFFFDD; border:1px solid #DDDD99;'
        )

        accdiv = tag.div(
            accdivheader,
            tag.div(createacc, acclist, id='accreditation'),
            id='accreditation_wrapper')

        stream |= Transformer('//div[@id="ticket"]').after(accdiv)
        return stream

    def _get_accreditations(self, id):

        result = {}
        for ticket, topic, conclusion, comment, author in self.env.db_query("""
            SELECT * FROM accreditation WHERE ticket = %s
            """, (id,) ):
            result.setdefault(topic, []).append((author, conclusion, comment))
        return result

    def _get_tables(self, dburi, cursor):
        """Code from TracMigratePlugin by Jun Omae (see tracmigrate.admin)."""
        if dburi.startswith('sqlite:'):
            sql = """
                SELECT name
                  FROM sqlite_master
                 WHERE type='table'
                   AND NOT name='sqlite_sequence'
            """
        elif dburi.startswith('postgres:'):
            sql = """
                SELECT tablename
                  FROM pg_tables
                 WHERE schemaname = ANY (current_schemas(false))
            """
        elif dburi.startswith('mysql:'):
            sql = "SHOW TABLES"
        else:
            raise TracError('Unsupported database type "%s"'
                            % dburi.split(':')[0])
        cursor.execute(sql)
        return sorted([row[0] for row in cursor])
