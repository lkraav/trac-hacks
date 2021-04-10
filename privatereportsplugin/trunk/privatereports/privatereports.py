# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Michael Henke <michael.henke@she.net>
# Copyright 2021 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#

from trac.admin import IAdminPanelProvider
from trac.core import Component, ExtensionPoint, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Table
from trac.env import IEnvironmentSetupParticipant
from trac.perm import (
    IPermissionGroupProvider, IPermissionPolicy, IPermissionRequestor,
    PermissionSystem)
from trac.ticket.model import Report
from trac.util.translation import _
from trac.web.chrome import Chrome, ITemplateProvider, add_warning


if not hasattr(PermissionSystem, 'get_permission_groups'):

    PermissionSystem.group_providers = ExtensionPoint(IPermissionGroupProvider)

    def get_permission_groups(self, user):
        groups = set([user])
        for provider in self.group_providers:
            for group in provider.get_permission_groups(user):
                groups.add(group)

        perms = PermissionSystem(self.env).get_all_permissions()
        repeat = True
        while repeat:
            repeat = False
            for subject, action in perms:
                if subject in groups and not action.isupper() and \
                        action not in groups:
                    groups.add(action)
                    repeat = True
        return groups

    PermissionSystem.get_permission_groups = get_permission_groups


class PrivateReports(Component):

    implements(IAdminPanelProvider, IEnvironmentSetupParticipant,
               IPermissionRequestor, ITemplateProvider)

    db_version = 1
    db_name = 'private_reports_version'
    db_schema = [
        Table('private_report')[
            Column('report_id', type='int'),
            Column('permission')
        ]
    ]

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('ticket', _("Ticket-System"),
                   'privatereports', _("Private Reports"))

    def render_admin_panel(self, req, cat, page, path_info):
        reports = list(Report.select(self.env))
        report_id = req.args.getint('report_id',
                                    reports[0].id if reports else None)
        report_permissions = self._get_report_permissions(report_id)
        if req.method == 'POST':
            if 'add' in req.args:
                new_permission = req.args.get('newpermission')
                if new_permission and new_permission.isupper() \
                        and new_permission not in report_permissions:
                    self._insert_report_permission(report_id, new_permission)
                elif not new_permission.isupper():
                    add_warning(req, _("Permissions must use all upper-case "
                                       "characters"))
            elif 'remove' in req.args:
                report_permissions = req.args.getlist('report_permissions')
                self._delete_report_permissions(report_id, report_permissions)
            req.redirect(req.href.admin('ticket/privatereports',
                         report_id=report_id))
        data = {
            'reports': reports,
            'report_permissions': report_permissions,
            'show_report': report_id,
        }

        if hasattr(Chrome(self.env), 'jenv'):
            return 'admin_privatereports_jinja.html', data
        else:
            return 'admin_privatereports.html', data

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(self.db_version, self.db_name)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        if 'private_report' not in dbm.get_table_names():
            dbm.create_tables(self.db_schema)
        dbm.set_database_version(self.db_version, self.db_name)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        report_perms = set()
        for permission, in self.env.db_query("""
                SELECT permission FROM private_report GROUP BY permission
                """):
            report_perms.add(permission)
        return tuple(report_perms)

    # Internal methods

    def _insert_report_permission(self, report_id, permission):
        self.env.db_transaction("""
            INSERT INTO private_report(report_id, permission)
            VALUES(%s, %s)
            """, (report_id, permission))

    def _delete_report_permissions(self, report_id, permissions):
        with self.env.db_transaction as db:
            for permission in permissions:
                db("""
                    DELETE FROM private_report
                    WHERE report_id=%s AND permission=%s
                    """, (report_id, permission))

    def _get_report_permissions(self, report_id):
        return [perm for perm, in self.env.db_query("""
                    SELECT permission FROM private_report
                    WHERE report_id=%s
                    """, (report_id,))]


class PrivateReportsPolicy(Component):

    implements(IPermissionPolicy)

    def check_permission(self, action, username, resource, perm):
        if resource and resource.realm == 'report' and \
                resource.id not in (None, -1):
            return self._has_permission(username, resource.id)

    def _has_permission(self, user, report_id):
        report_permissions = \
            PrivateReports(self.env)._get_report_permissions(report_id)
        if not report_permissions:
            return True
        ps = PermissionSystem(self.env)
        groups = set(ps.get_permission_groups(user))
        groups.add(user)
        user_perms = set()
        for group in groups:
            user_perms.update(ps.get_user_permissions(group))
        return bool(set(report_permissions) & user_perms)
