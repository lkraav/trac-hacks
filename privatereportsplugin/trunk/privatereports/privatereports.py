# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Michael Henke <michael.henke@she.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#

from types import ListType, StringTypes

from trac.admin import IAdminPanelProvider
from trac.core import Component, ExtensionPoint, implements
from trac.env import IEnvironmentSetupParticipant
from trac.perm import (
    IPermissionGroupProvider, IPermissionPolicy, IPermissionRequestor,
    PermissionSystem
)
from trac.web.chrome import ITemplateProvider


class PrivateReports(Component):

    implements(IAdminPanelProvider, IEnvironmentSetupParticipant,
               IPermissionRequestor, ITemplateProvider)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('reports', 'Reports',
                   'privatereports', 'Private Reports')

    def render_admin_panel(self, req, cat, page, path_info):
        if page == 'privatereports':
            reports = self._get_reports()
            data = {
                'reports': reports
            }
            if req.method == 'POST':
                report_id = req.args.get('report_id')
                try:
                    report_id = int(report_id)
                except ValueError:
                    req.redirect(self.env.href.admin.reports('privatereports'))
                if req.args.get('add'):
                    new_permission = req.args.get('newpermission')
                    if new_permission is None or \
                            new_permission.isupper() is False:
                        req.redirect(
                            self.env.href.admin.reports('privatereports'))
                    self._insert_report_permission(report_id, new_permission)
                    data['report_permissions'] = \
                        self._get_report_permissions(report_id) or ''
                    data['show_report'] = report_id
                elif req.args.get('remove'):
                    arg_report_permissions = req.args.get('report_permissions')
                    if arg_report_permissions is None:
                        req.redirect(
                            self.env.href.admin.reports('privatereports'))
                    report_permissions = \
                        self._get_report_permissions(report_id)
                    report_permissions = set(report_permissions)
                    to_remove = set()
                    if type(arg_report_permissions) in StringTypes:
                        to_remove.update([arg_report_permissions])
                    elif type(arg_report_permissions) == ListType:
                        to_remove.update(arg_report_permissions)
                    else:
                        req.redirect(
                            self.env.href.admin.reports('privatereports'))
                    report_permissions = report_permissions - to_remove
                    self._alter_report_permissions(report_id,
                                                   report_permissions)
                    data['report_permissions'] = report_permissions or ''
                    data['show_report'] = report_id
                elif req.args.get('show'):
                    report_permissions = \
                        self._get_report_permissions(report_id)
                    data['report_permissions'] = report_permissions or ''
                    data['show_report'] = report_id
            else:
                report_permissions = \
                    self._get_report_permissions(reports[0][1])
                data['report_permissions'] = report_permissions or ''
            return 'admin_privatereports.html', data

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        db = self.env.get_db_cnx()
        if self.environment_needs_upgrade(db):
            self.upgrade_environment(db)

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT report_id, permission FROM private_report")
            return False
        except:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS private_report")
            db.commit()
        except:
            cursor.connection.rollback()
        try:
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE private_report(report_id integer,
                  permission text)""")
            db.commit()
        except:
            cursor.connection.rollback()

    # IPermissionRequestor methods

    def get_permission_actions(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT permission FROM private_report GROUP BY permission""")
        report_perms = []
        try:
            for permission in cursor.fetchall():
                report_perms.append(permission[0])
        except:
            pass
        return tuple(report_perms)

    # Internal methods

    def _get_reports(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT title, id FROM report")
        reports = cursor.fetchall()
        return reports

    def _insert_report_permission(self, report_id, permission):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO private_report(report_id, permission)
            VALUES(%s, %s)""", (int(report_id), str(permission)))
        db.commit()

    def _alter_report_permissions(self, report_id, permissions):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            DELETE FROM private_report WHERE report_id=%s
            """, (int(report_id),))
        db.commit()
        for permission in permissions:
            self._insert_report_permission(report_id, permission)

    def _get_report_permissions(self, report_id):
        report_perms = []
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT permission FROM private_report
            WHERE report_id=%s GROUP BY permission""", (int(report_id),))
        for perm in cursor.fetchall():
            report_perms.append(perm[0])
        return report_perms


class PrivateReportsPolicy(Component):

    group_providers = ExtensionPoint(IPermissionGroupProvider)

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
        perms = PermissionSystem(self.env)
        report_permissions = set(report_permissions)
        user_perm = set(perms.get_user_permissions(user))
        groups = set(self._get_user_groups(user))
        user_perm.update(groups)
        if report_permissions.intersection(user_perm) != set([]):
            return True
        return False

    def _get_user_groups(self, user):
        subjects = set([user])
        for provider in self.group_providers:
            subjects.update(provider.get_permission_groups(user) or [])
        groups = []
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT action FROM permission WHERE username = %s""", (user,))
        rows = cursor.fetchall()
        for action in rows:
            if action[0].isupper():
                groups.append(action[0])
        return groups
