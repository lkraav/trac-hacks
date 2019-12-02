# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 ERCIM
# Copyright (C) 2009 Jean-Guilhem Rouel <jean-guilhem.rouel@ercim.org>
# Copyright (C) 2009 Vivien Lacourba <vivien.lacourba@ercim.org>
# Copyright (C) 2012-2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Component, implements
from trac.db import Column, DatabaseManager, Index, Table
from trac.env import IEnvironmentSetupParticipant
from trac.resource import ResourceNotFound
from trac.ticket import model
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_script_data

from defaultcc.model import DefaultCC


class DefaultCCAdmin(Component):
    """Allows to setup a default CC list per component through the component
    admin UI.
    """

    implements(IEnvironmentSetupParticipant, IRequestFilter, ITemplateProvider)

    SCHEMA = [
        Table('component_default_cc', key='name')[
            Column('name'),
            Column('cc'),
            Index(['name']),
        ]
    ]

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        return 'component_default_cc' not in self._get_tables()

    def upgrade_environment(self, db=None):
        self._upgrade_db()

    def _upgrade_db(self):
        db_backend = DatabaseManager(self.env).get_connector()[0]
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    cursor.execute(stmt)

    def _get_tables(self):
        dburi = self.config.get('trac', 'database')
        if dburi.startswith('sqlite:'):
            query = "SELECT name FROM sqlite_master" \
                    " WHERE type='table' AND NOT name='sqlite_sequence'"
        elif dburi.startswith('postgres:'):
            query = "SELECT tablename FROM pg_tables" \
                    " WHERE schemaname = ANY (current_schemas(false))"
        elif dburi.startswith('mysql:'):
            query = "SHOW TABLES"
        else:
            raise TracError('Unsupported %s database' % dburi.split(':')[0])
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute(query)
            return sorted(row[0] for row in cursor)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if 'TICKET_ADMIN' in req.perm and req.method == 'POST' \
                and req.path_info.startswith('/admin/ticket/components'):
            if req.args.get('save') and req.args.get('name'):
                old_name = req.args.get('path_info')
                new_name = req.args.get('name')
                old_cc = DefaultCC(self.env, old_name)
                new_cc = DefaultCC(self.env, new_name)
                new_cc.cc = req.args.get('defaultcc', '')
                if old_name == new_name:
                    old_cc.delete()
                    if new_cc.cc:
                        new_cc.insert()
                else:
                    try:
                        model.Component(self.env, new_name)
                    except ResourceNotFound:
                        old_cc.delete()
                        if new_cc.cc:
                            new_cc.insert()
            elif req.args.get('add') and req.args.get('name'):
                name = req.args.get('name')
                try:
                    model.Component(self.env, name)
                except ResourceNotFound:
                    cc = DefaultCC(self.env, name)
                    cc.name = name
                    cc.cc = req.args.get('defaultcc', '')
                    cc.insert()
            elif req.args.get('remove'):
                if req.args.get('sel'):
                    # If only one component is selected, we don't receive
                    # an array, but a string preventing us from looping in
                    # that case.
                    if isinstance(req.args.get('sel'), basestring):
                        cc = DefaultCC(self.env, req.args.get('sel'))
                        cc.delete()
                    else:
                        for name in req.args.get('sel'):
                            cc = DefaultCC(self.env, name)
                            cc.delete()
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'admin_components.html':
            add_script(req, 'defaultcc/defaultcc.js')
            if data.get('component'):
                model = DefaultCC(self.env, data.get('component').name)
                add_script_data(req, {'component_cc': model.cc})
            elif data.get('components'):
                # Prior to Trac 1.0.2-r11919, components was a generator and
                # expanding the generator causes the table to not be rendered
                data['components'] = list(data['components'])
                ccs = DefaultCC.select(self.env)
                add_script_data(req, {'component_ccs': ccs})
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('defaultcc', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        pass
