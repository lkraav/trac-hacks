# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martin Aspeli <optilude@gmail.com>
# Copyright (C) 2012 Chris Nelson <Chris.Nelson@SIXNET.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
from datetime import datetime, timedelta
from pkg_resources import resource_filename

import teamcalendar.compat
from trac.config import IntOption, ListOption
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Table
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.core import Component, implements
from trac.util.datefmt import from_utimestamp, parse_date, to_utimestamp, \
                              user_time, utc
from trac.util.html import html
from trac.web.api import IRequestHandler
from trac.web.chrome import Chrome, INavigationContributor, \
                            ITemplateProvider, add_stylesheet


schema_name = 'teamcalendar_version'
schema_version = 2
schema = [
    Table('team_calendar', key=('username', 'time'))[
        Column('username'),
        Column('time', type='int64'),
        Column('availability', type='int')]
]


class TeamCalendar(Component):

    implements(IEnvironmentSetupParticipant, INavigationContributor,
               IPermissionRequestor, IRequestHandler, ITemplateProvider)

    weeks_prior = IntOption('team-calendar', 'weeks_prior', '1',
                            doc="Number of weeks before the current week to "
                                "show by default.")

    weeks_after = IntOption('team-calendar', 'weeks_after', '3',
                            doc="Number of weeks after the current week to "
                                "show by default.")

    work_days = ListOption('team-calendar', 'work_days', [0, 1, 2, 3, 4],
                           doc="Days of week that are worked. Defaults to "
                               "Monday through Friday. 0 is Monday.")

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        with self.env.db_transaction as db:
            self.upgrade_environment(db)

    def environment_needs_upgrade(self, db):
        return DatabaseManager(self.env).needs_upgrade(schema_version,
                                                       schema_name)

    def upgrade_environment(self, db):
        dbm = DatabaseManager(self.env)
        dbm.create_tables(schema)
        dbm.set_database_version(schema_version, schema_name)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'teamcalendar'

    def get_navigation_items(self, req):
        if 'TEAMCALENDAR_VIEW' in req.perm:
            yield ('mainnav', 'teamcalendar',
                   html.a("Team Calendar", href=req.href.teamcalendar()))

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TEAMCALENDAR_VIEW', 'TEAMCALENDAR_UPDATE_OTHERS',
                'TEAMCALENDAR_UPDATE_OWN']

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('teamcalendar', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/teamcalendar(?:_trac)?(?:/.*)?$', req.path_info)

    def process_request(self, req):
        req.perm.require('TEAMCALENDAR_VIEW')

        def parse_date_str(date_str, default):
            if not date_str:
                return default
            return user_time(req, parse_date, date_str)

        today = datetime_as_date(datetime.now(req.tz))
        offset = today.isoweekday() - 1 + 7 * self.weeks_prior - 1
        default_start = today - timedelta(offset)
        offset = 7 - today.isoweekday() + 7 * self.weeks_after
        default_end = today + timedelta(offset)

        from_date = parse_date_str(req.args.get('from_date'), default_start)
        to_date = parse_date_str(req.args.get('to_date'), default_end)

        data = {'authname': req.authname}

        # Can we update?
        data['can_update_own'] = can_update_own = \
            'TEAMCALENDAR_UPDATE_OWN' in req.perm
        data['can_update_others'] = can_update_others = \
            'TEAMCALENDAR_UPDATE_OTHERS' in req.perm
        data['can_update'] = can_update_own or can_update_others

        # Get all people
        data['people'] = people = self.get_people()

        num_days = (to_date - from_date).days + 1
        date_range = [from_date + timedelta(days=d)
                      for d in range(0, num_days)]

        # Store dates
        data['today'] = today
        data['from_date'] = date_range[0]
        data['to_date'] = date_range[-1]

        # Update timetable if required
        if 'update_calendar' in req.args:
            req.perm.require('TEAMCALENDAR_UPDATE_OWN')

            # deliberately override dates: want to show result of update
            from_date = parse_date_str(req.args['orig_from_date'],
                                       default_start)
            to_date = parse_date_str(req.args['orig_to_date'],
                                     default_end)
            tuples = []
            for date in date_range:
                if can_update_others:
                    for person in people:
                        status = bool(req.args.get('%s.%s' % (date, person), 0))
                        tuples.append((date_at_utc(date), person, status))
                elif can_update_own:
                    authname = req.authname
                    status = bool(req.args.get('%s.%s' % (date, authname), 0))
                    tuples.append((date_at_utc(date), authname, status))

            self.update_timetable(tuples)

        data['timetable'] = self.get_timetable(from_date, to_date, people)
        data['dates'] = date_range
        data['date_at_utc'] = date_at_utc

        Chrome(self.env).add_jquery_ui(req)
        add_stylesheet(req, 'teamcalendar/css/calendar.css')
        return 'teamcalendar.html', data, None

    # Internal methods

    def get_people(self):
        perm = PermissionSystem(self.env)
        people = \
            set(perm.get_users_with_permission('TEAMCALENDAR_UPDATE_OWN'))
        return sorted(people)

    def get_timetable(self, from_date, to_date, people):
        timetable = {}
        for row in self.env.db_query("""
                SELECT time, username, availability
                FROM team_calendar
                WHERE time >= %s AND time <= %s
                ORDER BY time ASC, username ASC
                """, (to_utc_utimestamp(from_date),
                      to_utc_utimestamp(to_date))):
            if row[1] in people:
                date = from_utimestamp(row[0])
                timetable.setdefault(date, {})
                timetable[date].update({row[1]: row[2]})

        return timetable

    # tuples is a list of arrays.
    # each array is (datetime, user, true/false).  For example:
    #  [(datetime.date(2011, 11, 28), u'admin', False),
    #   (datetime.date(2011, 11, 28), u'chrisn', True),
    #   (datetime.date(2011, 11, 29), u'admin', False),
    #   (datetime.date(2011, 11, 29), u'chrisn', True)]
    # Note that the date and user are keys to the DB.
    #
    # It appears -- though I don't know that it is guaranteed -- that
    # the items are in date order and there are no gaps in the dates.
    def update_timetable(self, tuples):
        # See what's already in the database for the same date range.
        print(tuples)
        from_date = tuples[1][0]
        to_date = tuples[-1][0]
        users = []
        for date_, user, avail in tuples:
            if user not in users:
                users.append(user)

        updates = []
        keys = [(t[0], t[1]) for t in tuples]
        with self.env.db_transaction as db:
            in_clause = "username IN (%s)" \
                        % ','.join("'%s'" % u for u in users)
            for row in db("""
                    SELECT time, username, availability
                    FROM team_calendar
                    WHERE time >= %%s AND time <= %%s AND %s
                    ORDER BY time
                    """ % in_clause, (to_utc_utimestamp(from_date),
                                      to_utc_utimestamp(to_date))):
                item = from_utimestamp(row[0]), row[1], bool(row[2])
                key = item[0], item[1]
                # If the whole db row is in tuples (date, person, and
                # availability match) take it out of tuples, we don't need
                # to do anything to the db
                if item in tuples:
                    tuples.remove(item)
                    keys.remove(key)
                # If the db key in this row has a value in tuples, we need
                # to update availability
                elif key in keys:
                    index = keys.index(key)
                    updates.append(tuples.pop(index))
                    keys.pop(index)
                # The query results should cover the same date range as
                # tuples.  We might get here if tuples has more users than
                # the db.  We fall through and add any tuples that don't
                # match the DB so this is OK
                else:
                    self.env.log.info("UI and db inconsistent.")

        # Duplicates and updates have been removed from tuples so
        # what's left is things to insert.
        inserts = tuples

        with self.env.db_transaction as db:
            if len(inserts):
                db.executemany("""
                    INSERT INTO team_calendar (time,username,availability)
                    VALUES (%s,%s,%s)
                    """, [(to_utc_utimestamp(t[0]), t[1], t[2] and 1 or 0)
                          for t in inserts])
            if len(updates):
                for t in updates:
                    db("""UPDATE team_calendar SET availability=%s
                        WHERE time=%s AND username=%s
                        """, (t[2] and 1 or 0, to_utc_utimestamp(t[0]), t[1]))


def datetime_as_date(dt):
    """Return datetime with truncated time."""
    return datetime(year=dt.year, month=dt.month, day=dt.day,
                    tzinfo=dt.tzinfo)


def date_at_utc(dt):
    """Return current date in UTC from datetime."""
    utc_dt = dt.astimezone(utc)
    return datetime_as_date(utc_dt)


def to_utc_utimestamp(dt):
    """Return timestamp representing current date in UTC from datetime."""
    return to_utimestamp(date_at_utc(dt))
