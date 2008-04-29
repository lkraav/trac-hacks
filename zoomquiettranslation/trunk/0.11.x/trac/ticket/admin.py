# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/.

from datetime import datetime

from trac.admin import IAdminPanelProvider
from trac.core import *
from trac.perm import PermissionSystem
from trac.ticket import model
from trac.util.datefmt import utc, parse_date, get_date_format_hint, \
                              get_datetime_format_hint
from trac.util.translation import _
from trac.web.chrome import add_link, add_script


class TicketAdminPage(Component):

    implements(IAdminPanelProvider)

    abstract = True

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', self._type, self._label[1])

    def render_admin_panel(self, req, cat, page, version):
        req.perm.require('TICKET_ADMIN')
        # Trap AssertionErrors and convert them to TracErrors
        try:
            return self._render_admin_panel(req, cat, page, version)
        except AssertionError, e:
            raise TracError(e)


class ComponentAdminPage(TicketAdminPage):

    _type = 'components'
    _label = ('Component', 'Components')

    # TicketAdminPage methods

    def _render_admin_panel(self, req, cat, page, component):
        # Detail view?
        if component:
            comp = model.Component(self.env, component)
            if req.method == 'POST':
                if req.args.get('save'):
                    comp.name = req.args.get('name')
                    comp.owner = req.args.get('owner')
                    comp.description = req.args.get('description')
                    comp.update()
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            add_script(req, 'common/js/wikitoolbar.js')
            data = {'view': 'detail', 'component': comp}

        else:
            if req.method == 'POST':
                # Add Component
                if req.args.get('add') and req.args.get('name'):
                    comp = model.Component(self.env)
                    comp.name = req.args.get('name')
                    if req.args.get('owner'):
                        comp.owner = req.args.get('owner')
                    comp.insert()
                    req.redirect(req.href.admin(cat, page))

                # Remove components
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError(_('No component selected'))
                    db = self.env.get_db_cnx()
                    for name in sel:
                        comp = model.Component(self.env, name, db=db)
                        comp.delete(db=db)
                    db.commit()
                    req.redirect(req.href.admin(cat, page))

                # Set default component
                elif req.args.get('apply'):
                    if req.args.get('default'):
                        name = req.args.get('default')
                        self.log.info('Setting default component to %s', name)
                        self.config.set('ticket', 'default_component', name)
                        self.config.save()
                        req.redirect(req.href.admin(cat, page))

            default = self.config.get('ticket', 'default_component')
            data = {'view': 'list',
                    'components': model.Component.select(self.env),
                    'default': default}

        if self.config.getbool('ticket', 'restrict_owner'):
            perm = PermissionSystem(self.env)
            def valid_owner(username):
                return perm.get_user_permissions(username).get('TICKET_MODIFY')
            data['owners'] = [username for username, name, email
                              in self.env.get_known_users()
                              if valid_owner(username)]
            data['owners'].insert(0, '')
            data['owners'].sort()
        else:
            data['owners'] = None

        return 'admin_components.html', data


class MilestoneAdminPage(TicketAdminPage):

    _type = 'milestones'
    _label = ('Milestone', 'Milestones')

    # TicketAdminPage methods

    def _render_admin_panel(self, req, cat, page, milestone):
        req.perm.require('TICKET_ADMIN')

        # Detail view?
        if milestone:
            mil = model.Milestone(self.env, milestone)
            if req.method == 'POST':
                if req.args.get('save'):
                    mil.name = req.args.get('name')
                    mil.due = mil.completed = None
                    due = req.args.get('duedate', '')
                    if due:
                        mil.due = parse_date(due)
                    completed = req.args.get('completeddate', '')
                    if completed:
                        mil.completed = parse_date(completed)
                        if mil.completed > datetime.now(utc):
                            raise TracError(_('Completion date may not be in '
                                              'the future',
                                              'Invalid Completion Date'))
                    mil.description = req.args.get('description', '')
                    mil.update()
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            add_script(req, 'common/js/wikitoolbar.js')
            data = {'view': 'detail', 'milestone': mil}

        else:
            if req.method == 'POST':
                # Add Milestone
                if req.args.get('add') and req.args.get('name'):
                    mil = model.Milestone(self.env)
                    mil.name = req.args.get('name')
                    if req.args.get('duedate'):
                        mil.due = parse_date(req.args.get('duedate'))
                    mil.insert()
                    req.redirect(req.href.admin(cat, page))

                # Remove milestone
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError(_('No milestone selected'))
                    db = self.env.get_db_cnx()
                    for name in sel:
                        mil = model.Milestone(self.env, name, db=db)
                        mil.delete(db=db)
                    db.commit()
                    req.redirect(req.href.admin(cat, page))

                # Set default milestone
                elif req.args.get('apply'):
                    if req.args.get('default'):
                        name = req.args.get('default')
                        self.log.info('Setting default milestone to %s', name)
                        self.config.set('ticket', 'default_milestone', name)
                        self.config.save()
                        req.redirect(req.href.admin(cat, page))

            data = {
                'view': 'list',
                'milestones': model.Milestone.select(self.env),
                'default': self.config.get('ticket', 'default_milestone'),
            }

        data.update({
            'date_hint': get_date_format_hint(),
            'datetime_hint': get_datetime_format_hint()
        })
        return 'admin_milestones.html', data


class VersionAdminPage(TicketAdminPage):

    _type = 'versions'
    _label = ('Version', 'Versions')

    # TicketAdminPage methods

    def _render_admin_panel(self, req, cat, page, version):
        # Detail view?
        if version:
            ver = model.Version(self.env, version)
            if req.method == 'POST':
                if req.args.get('save'):
                    ver.name = req.args.get('name')
                    if req.args.get('time'):
                        ver.time = parse_date(req.args.get('time'))
                    else:
                        ver.time = None # unset
                    ver.description = req.args.get('description')
                    ver.update()
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            add_script(req, 'common/js/wikitoolbar.js')
            data = {'view': 'detail', 'version': ver}

        else:
            if req.method == 'POST':
                # Add Version
                if req.args.get('add') and req.args.get('name'):
                    ver = model.Version(self.env)
                    ver.name = req.args.get('name')
                    if req.args.get('time'):
                        ver.time = parse_date(req.args.get('time'))
                    ver.insert()
                    req.redirect(req.href.admin(cat, page))
                         
                # Remove versions
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError(_('No version selected'))
                    db = self.env.get_db_cnx()
                    for name in sel:
                        ver = model.Version(self.env, name, db=db)
                        ver.delete(db=db)
                    db.commit()
                    req.redirect(req.href.admin(cat, page))

                # Set default version
                elif req.args.get('apply'):
                    if req.args.get('default'):
                        name = req.args.get('default')
                        self.log.info('Setting default version to %s', name)
                        self.config.set('ticket', 'default_version', name)
                        self.config.save()
                        req.redirect(req.href.admin(cat, page))

            data = {
                'view': 'list',
                'versions': model.Version.select(self.env),
                'default': self.config.get('ticket', 'default_version'),
            }

        data.update({
            'datetime_hint': get_datetime_format_hint()
        })
        return 'admin_versions.html', data


class AbstractEnumAdminPage(TicketAdminPage):
    implements(IAdminPanelProvider)
    abstract = True

    _type = 'unknown'
    _enum_cls = None
    _label = ('(Undefined)', '(Undefined)')

    # TicketAdminPage methods

    def _render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TICKET_ADMIN')
        data = {'label_singular': self._label[0],
                'label_plural': self._label[1]}

        # Detail view?
        if path_info:
            enum = self._enum_cls(self.env, path_info)
            if req.method == 'POST':
                if req.args.get('save'):
                    enum.name = req.args.get('name')
                    enum.update()
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))
            data.update({'view': 'detail', 'enum': enum})

        else:
            default = self.config.get('ticket', 'default_%s' % self._type)

            if req.method == 'POST':
                # Add enum
                if req.args.get('add') and req.args.get('name'):
                    enum = self._enum_cls(self.env)
                    enum.name = req.args.get('name')
                    enum.insert()
                    req.redirect(req.href.admin(cat, page))
                         
                # Remove enums
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError(_('No enum selected'))
                    db = self.env.get_db_cnx()
                    for name in sel:
                        enum = self._enum_cls(self.env, name, db=db)
                        enum.delete(db=db)
                    db.commit()
                    req.redirect(req.href.admin(cat, page))

                # Appy changes
                elif req.args.get('apply'):
                    # Set default value
                    if req.args.get('default'):
                        name = req.args.get('default')
                        if name != default:
                            self.log.info('Setting default %s to %s',
                                          self._type, name)
                            self.config.set('ticket', 'default_%s' % self._type,
                                            name)
                            self.config.save()

                    # Change enum values
                    order = dict([(str(int(key[6:])), 
                                   str(int(req.args.get(key)))) for key
                                  in req.args.keys()
                                  if key.startswith('value_')])
                    values = dict([(val, True) for val in order.values()])
                    if len(order) != len(values):
                        raise TracError(_('Order numbers must be unique'))
                    db = self.env.get_db_cnx()
                    for enum in self._enum_cls.select(self.env, db=db):
                        new_value = order[enum.value]
                        if new_value != enum.value:
                            enum.value = new_value
                            enum.update(db=db)
                    db.commit()

                    req.redirect(req.href.admin(cat, page))

            data.update(dict(enums=list(self._enum_cls.select(self.env)),
                             default=default, view='list'))
        return 'admin_enums.html', data


class PriorityAdminPage(AbstractEnumAdminPage):
    _type = 'priority'
    _enum_cls = model.Priority
    _label = ('Priority', 'Priorities')


class ResolutionAdminPage(AbstractEnumAdminPage):
    _type = 'resolution'
    _enum_cls = model.Resolution
    _label = ('Resolution', 'Resolutions')


class SeverityAdminPage(AbstractEnumAdminPage):
    _type = 'severity'
    _enum_cls = model.Severity
    _label = ('Severity', 'Severities')


class TicketTypeAdminPage(AbstractEnumAdminPage):
    _type = 'type'
    _enum_cls = model.Type
    _label = ('Ticket Type', 'Ticket Types')
