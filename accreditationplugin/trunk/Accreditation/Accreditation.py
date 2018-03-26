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
from trac.perm import IPermissionRequestor, PermissionError
from genshi.output import XHTMLSerializer
from trac.config import Option
import re

class Accreditation(Component):

    implements(IEnvironmentSetupParticipant, IRequestHandler,
               ITemplateStreamFilter, IPermissionRequestor)
    webui_wrapper_title = Option(
        'accreditation', 'webui_wrapper_title', 'Accreditation', 
        doc="Label for the wrapper frame of this plugin that will be shown in the web form of each ticket.")
    webui_topic_title = Option(
        'accreditation', 'webui_topic_title', 'Topic',
        doc="Label for the 'Topic' field of this plugin that will be shown in the web form of each ticket.")

    
    webui_wrapper = Option(
        'accreditation', 'webui_wrapper', 'accreditation_wrapper',
        doc="HTML container for the Accreditations displayed in the ticket.html page.")
    webui_table_participant_title = Option(
        'accreditation', 'webui_table_participant_title', 'Author',
        doc="Label for the 'Author' field of this plugin that will be shown in the web form of each approval of each ticket.")
    webui_table_conclusion_title = Option(
        'accreditation', 'webui_table_conclusion_title', 'Conclusion',
        doc="Label for the 'Conclusion' field of this plugin that will be shown in the web form of each approval row of each ticket.")
    webui_table_comments_title = Option(
        'accreditation', 'webui_table_comments_title', 'Comment',
        doc="Label for the 'Comment' field of this plugin that will be shown in the web form of each approval row of each ticket.")
    
    webui_participants_title = Option(
        'accreditation', 'webui_participants_title', 'Participants',
        doc="Label for the 'Participants' field of this plugin that will be shown in the web form of each ticket.")
    webui_topic_options_list = Option(
        'accreditation', 'webui_topic_options', '',
        doc="List of options to be provided to user to select for the Topic field in this plugin.")        
    webui_table_conclusion_options_list = Option(
        'accreditation', 'webui_table_conclusion_options', '',
        doc="List of options to be provided to user to select for the Conclusion field in the web form of each approval row of each ticket.")        
    created_comment_label = Option(
        'accreditation', 'created_comment_label', 'Launched New Accreditation',
        doc="Label prefixed to comment in ticket history for each new accreditation.")
    updated_comment_label = Option(
        'accreditation', 'updated_comment_label', 'Accredited',
        doc="Label prefixed to comment in ticket history for each updated accreditation.")
    deleted_comment_label = Option(
        'accreditation', 'deleted_comment_label', 'Accredited',
        doc="Label prefixed to comment in ticket history for each deleted accreditation.")

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
                req.path_info.startswith('/accreditation/comment')or
                req.path_info.startswith('/accreditation/delete'))

    def process_request(self, req):
        if req.path_info.startswith('/accreditation/new') and \
            'ACCREDITATION_CREATE' in req.perm:


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
                                "%s '''%s'''" % (self.created_comment_label,topic))

            req.redirect(req.href('ticket', id)+'#%s' % self.webui_wrapper)

        elif req.path_info.startswith('/accreditation/comment'):

            id = int(req.args['ticket'])
            author = req.args.get('author')
            if req.authname == author:
                topic = req.args.get('topic')
                conclusion = req.args.get('conclusion')
                comment = req.args.get('comment')
                if conclusion and comment:
                    ticket_comment = "%s '''%s''' for \"''%s''\".\n\n%s" \
                                     % (self.updated_comment_label, topic, conclusion, comment)
    
                    with self.env.db_transaction as db:
                        db("""
                            UPDATE accreditation SET conclusion = %s, comment = %s
                            WHERE ticket = %s AND topic = %s AND author = %s
                            """, (conclusion, comment, id, topic, author))
                        ticket = Ticket(self.env, id)
                        ticket.save_changes(req.authname, ticket_comment)

            req.redirect(req.href('ticket', id)+'#%s' % self.webui_wrapper)

        elif req.path_info.startswith('/accreditation/delete') and \
            'ACCREDITATION_DELETE' in req.perm:
            id = int(req.args['ticket'])
            topic = req.args.get('topic')
            author = req.args.get('delete-author')
            ticket_comment = "%s '''%s''' for \"''%s''\"." \
                             % (self.deleted_comment_label, topic, author)
            with self.env.db_transaction as db:
                db("""
                    DELETE from accreditation 
                    WHERE ticket = %s AND topic = %s AND author = %s
                    """, (id, topic, author))
                ticket = Ticket(self.env, id)
                ticket.save_changes(req.authname, ticket_comment)

            req.redirect(req.href('ticket', id)+'#%s' % self.webui_wrapper)

    def get_delete_btn(self, req, topic, author):
        if not 'ACCREDITATION_DELETE' in req.perm:
            return None
        return tag.div( tag.input( type_='submit', value='- Delete', 
                            title="Delete %s" % self.webui_wrapper_title, class_='trac-delete',
                            onclick=('$("#%s-author").val("%s");this.form.action="/accreditation/delete"' % ( re.sub('[^A-Za-z0-9]+', '', topic), author))),
                            class_="inlinebuttons",
                            style='bordercolor=red;height: 100%; position: absolute; right: 0; top: 0;')            

    def get_topic_submit_change_btn(self, req, accreditations):
        if not [author for author, conclusion, comment in accreditations if req.authname == author]:
            return None
        return tag.input(type_='submit', value='Submit', name='submit', style='margin-top: 5px; float: right;')   
    
    def filter_stream(self, req, method, filename, stream, data):

        if not req.path_info.startswith('/ticket') or 'ticket' not in data:
            return stream

        ticket = data['ticket']
    
        accdivheader = tag.h3(
            tag.a( self.webui_wrapper_title, href='#%s' % self.webui_wrapper),
            class_='foldable')
        webui_topic_options = self.webui_topic_options_list.split(',')
        webui_table_conclusion_options = self.webui_table_conclusion_options_list.split(',')
        conclusion_input_style = 'padding-left: 0; padding-right: 0; width:98%;'

        createacc = None
        if 'ACCREDITATION_CREATE' in req.perm:
            createacc = tag.div(
                tag.form(
                    tag.input(type_='hidden', value=str(ticket.id), name='ticket'),
                    tag.fieldset(
                        tag.table(
                            tag.tr(
                                tag.td(tag.label(self.webui_topic_title+':')),
                                tag.td(
                                   tag.input(type_='text', name='topic') if not webui_topic_options else 
                                    tag.select([tag.option(x, selected=(None)) for x in webui_topic_options], name='topic', id='topic'))
                                   ),
                            tag.tr(
                                tag.td(tag.label(self.webui_participants_title+':')),
                                tag.td(tag.input(type_='text', name='participants', id='participants')))),
                        tag.div(tag.input(type_='submit', value='Submit', name='submit'), class_='buttons')),
                    id='accreditationform', method='POST', action=req.href('accreditation', 'new')))

        acclist = tag.div(
            *[tag.div(
                tag.form(
                    tag.h2(key, style='color: #884444; margin: 0.3em 0 0.4em;'),
                    tag.input(type_='hidden', value=str(ticket.id), name='ticket'),
                    tag.input(type_='hidden', value=key, name='topic'),
                    tag.input(type_='hidden', value='=', name='delete-author', id="%s-author" % re.sub('[^A-Za-z0-9]+', '', key)),
                    tag.table(
                        tag.tr(
                            tag.th(self.webui_table_participant_title),
                            tag.th(self.webui_table_conclusion_title),
                            tag.th(self.webui_table_comments_title)),
                        *[tag.tr(
                            tag.td(author if not req.authname == author else tag.input( type_="text", name="author", value=author, readonly=True)
                                   , style='width: 150px;'),                            
                            tag.td( 
                                conclusion if not req.authname == author else
                                    tag.input(type_='text',name='conclusion', value=conclusion, style=conclusion_input_style) 
                                        if not webui_table_conclusion_options else
                                            tag.select(
                                                [tag.option( x, selected=(x == conclusion or None)) for x in webui_table_conclusion_options], 
                                                id='conclusion', name='conclusion', value=conclusion, style=conclusion_input_style)
                                , style='width: 150px;'),
                            tag.td(comment if not req.authname == author else tag.input(type_='text', name='comment', value=comment, style='padding-left: 0; padding-right: 0; width: 98%;'),
                                   self.get_delete_btn(req, key, author), style='position: relative;')
                        ) for author, conclusion, comment in value],
                        class_='wiki', style='width: 100%;'),
                    self.get_topic_submit_change_btn( req, value ),
                    tag.div(style='clear: both;'),
                    action=req.href('accreditation', 'comment'), method='POST'
                )
            ) for key, value in self._get_accreditations(ticket.id).items()]
            , class_='trac-content', style='background: none repeat scroll 0 0 #FFFFDD; border:1px solid #DDDD99;'
        )

        accdiv = tag.div(
            accdivheader, 
            tag.div(createacc, acclist, id='accreditation'), 
            id=self.webui_wrapper)

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

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['ACCREDITATION_CREATE','ACCREDITATION_DELETE']
    
