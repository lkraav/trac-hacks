# -*- encoding: UTF-8 -*-
"""
Created on 28 oct. 2010

@author: thierry
"""
###############################################################################
##
##             O U T    O F    T H E    B O X    T A S K
##
###############################################################################
from datetime import datetime, timedelta
from time import strptime, time, localtime

from trac.ticket.model import Ticket
from trac.config import BoolOption, IntOption, Option
from trac.core import Component, implements
from trac.notification import NotifyEmail
from trac.util.text import wrap
from trac.util.datefmt import utc, from_utimestamp, to_utimestamp
from trac.web.chrome import ITemplateProvider
from traccron.api import ICronTask
from traccron.core import CronConfig


class HeartBeatTask(Component, ICronTask):
    """
    This is a simple task for testing purpose.
    It only write a trace in log at debug level
    """
    implements(ICronTask)

    def wake_up(self, *args):
        if len(args) > 0:
            for arg in args:
                self.env.log.debug('Heart beat: %s' % arg)
        else:
            self.env.log.debug('Heart beat: boom boom !!!')

    def getId(self):
        return 'heart_beat'

    def getDescription(self):
        return self.__doc__


class SleepingTicketNotification(NotifyEmail):

    template_name = 'sleeping_ticket_template.txt'

    def __init__(self, env):
        NotifyEmail.__init__(self, env)

    def get_recipients(self, owner):
        return ([owner], [])

    def remind(self, tiketsByOwner, delay):
        """
        Send a digest mail to ticket owner to remind him of those
        sleeping tickets
        """
        for owner in tiketsByOwner:
            # prepare the data for the email content generation
            self.data.update({
                'ticket_count': len(tiketsByOwner[owner]),
                'delay': delay
            })
            NotifyEmail.notify(self, owner, 'Sleeping ticket notification')

    def send(self, torcpts, ccrcpts):
        return NotifyEmail.send(self, torcpts, ccrcpts)


class OrphanedTicketNotification(NotifyEmail):

    template_name = 'orphaned_ticket_template.txt'

    def __init__(self, env):
        NotifyEmail.__init__(self, env)

    def get_recipients(self, reporter):
        return ([reporter], [])

    def remind(self, tiketsByReporter, delay):
        """
        Send a digest mail to the reporter to remind them
        of those orphaned tickets
        """
        for reporter in tiketsByReporter:
            # prepare the data for the email content generation
            self.data.update({
                'ticket_count': len(tiketsByReporter[reporter]),
                'delay': delay
            })
            NotifyEmail.notify(self, reporter, 'orphaned ticket notification')

    def send(self, torcpts, ccrcpts):
        return NotifyEmail.send(self, torcpts, ccrcpts)


class SleepingTicketReminderTask(Component, ICronTask, ITemplateProvider):
    """
    Remind user about sleeping ticket they are assigned to.
    """
    implements(ICronTask, ITemplateProvider)

    delay_days = 3

    select_assigned_ticket = """
        SELECT t.id , t.owner
        FROM ticket t, ticket_change tc
        WHERE t.id = tc.ticket
        AND t.status in ('new','assigned','accepted')
        AND (SELECT MAX(tc2.time)
             FROM ticket_change tc2
             WHERE tc2.ticket=tc.ticket) < %s
        GROUP BY t.id
    """

    select_orphaned_ticket = """
       SELECT t.id, t.reporter
       FROM ticket t
       WHERE t.id not in (SELECT tc.ticket
                          FROM ticket_change tc
                          WHERE tc.ticket=t.id)
       AND t.time < %s
       AND t.status = 'new'
    """

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def _find_sleeping_ticket(self, sql, delay, dico, msg):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        delay_time = datetime.now(utc) - timedelta(days=delay)
        cursor.execute(sql, (to_utimestamp(delay_time),))
        for ticket, recipient in cursor:
            self.env.log.info(msg % (ticket, recipient, delay))
            if recipient in dico:
                dico[recipient].append(ticket)
            else:
                dico[recipient] = [ticket]

    def remind_assigned_ticket(self, delay):
        dico = {}
        msg = 'warning sleeping ticket %d assigned to %s ' \
              'but is inactive since more than %d day'
        self._find_sleeping_ticket(self.select_assigned_ticket,
                                   delay, dico, msg)
        SleepingTicketNotification(self.env).remind(dico, delay)

    def remind_orphaned_ticket(self, delay):
        dico = {}
        msg = 'warning ticket %d is new but orphaned: %s, %d'
        self._find_sleeping_ticket(self.select_orphaned_ticket,
                                   delay, dico, msg)
        OrphanedTicketNotification(self.env).remind(dico, delay)

    def wake_up(self, *args):
        delay = SleepingTicketReminderTask.delay_days
        if len(args) > 0:
            delay = int(args[0])

        # look for ticket assigned but not touched since more that the delay
        self.remind_assigned_ticket(delay)
        self.remind_orphaned_ticket(delay)

    def getId(self):
        return 'sleeping_ticket'

    def getDescription(self):
        return self.__doc__


class BaseTicketNotification(NotifyEmail):

    def __init__(self, env, milestone):
        NotifyEmail.__init__(self, env)
        self.milestone = milestone

    def get_recipients(self, recipient):
        return ([recipient], [])

    def send(self, torcpts, ccrcpts):
        return NotifyEmail.send(self, torcpts, ccrcpts)

    def populate_unreachable_tickets_data(self, tickets):
        # we are not called if there is no tickets
        self.data['milestone'] = tickets[0]['milestone']
        due_date = from_utimestamp(tickets[0]['due'])
        self.data['due_date'] = due_date.strftime('%Y-%m-%d')

        tickets_list = ''
        for ticket in tickets:
            tickets_list += ticket['summary'] + '\n'
            tickets_list += self.env.abs_href.ticket(ticket['ticket']) + '\n'
            tickets_list += '\n'

        self.data['tickets_list'] = tickets_list

    def notify_opened_ticket(self, recipient, tickets):
        """
        Send a digest mail to recipients (e.g. ticket owner and reporter)
        about ticket still opened
        """
        self.populate_unreachable_tickets_data(tickets)
        subject = 'Milestone %s with still opened ticket' % self.milestone
        NotifyEmail.notify(self, recipient, subject)
        self.env.log.debug('notify opened ticket: %s, %s, %s' % (
                           recipient, self.milestone, self.__class__.__name__))


class ReporterOpenedTicketNotification(BaseTicketNotification):
    """
    Notify reporter about an opened ticket in a near milestone
    """
    template_name = "opened_ticket_for_reporter_template.txt"

    def __init__(self, env, milestone):
        BaseTicketNotification.__init__(self, env, milestone)


class OwnerOpenedTicketNotification(BaseTicketNotification):
    """
    Notify owner about an opened ticket in a near milestone
    """
    template_name = "opened_ticket_for_owner_template.txt"

    def __init__(self, env, milestone):
        BaseTicketNotification.__init__(self, env, milestone)


class UnreachableMilestoneNotification(BaseTicketNotification):
    """
    Notify the specified person (ex: admin, release manager) that a milestone
    is about to closed but there still are opened ticket
    """
    template_name = 'unreachable_milestone_template.txt'

    def __init__(self, env, milestone):
        BaseTicketNotification.__init__(self, env, milestone)
        self.cronconf = CronConfig(self.env)

    def get_recipients(self, milestone):
        reclist = self.cronconf.get_unreachable_milestone_task_recipient_list()
        return (reclist, [])

    def notify_unreachable_milestone(self, tickets):
        """
        Send a digest mail listing all tickets still opened in the milestone
        """
        self.populate_unreachable_tickets_data(tickets)
        subject = "Milestone %s still has opened ticket" % self.milestone
        NotifyEmail.notify(self, self.milestone, subject)
        self.env.log.debug('notify unreachable milestone: %s, %s' % (
                           self.milestone, self.__class__.__name__))


class UnreachableMilestoneTask(Component, ICronTask, ITemplateProvider):
    """
    Send notification about near milestone with opened ticked
    """
    implements(ICronTask, ITemplateProvider)

    ahead_days = 3

    select_near_milestone_ticket = """
        SELECT t.id , t.owner, t.reporter, t.milestone, t.summary, m.due
        FROM ticket t, milestone m
        WHERE t.milestone = m.name
        AND m.due < %s
    """

    def __init__(self):
        self.cronconf = CronConfig(self.env)

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def _set_recipient_data(self, dico, recipient, milestone, ticket_data):
        dico.setdefault(recipient, {}).__setitem__(milestone, [ticket_data])
        dico[recipient].setdefault(milestone, []).append(ticket_data)

    def remind_unreachable_recipients(self, dico):
        """
        Send notification for each milestone
        """
        for milestone in dico:
            notifier = UnreachableMilestoneNotification(self.env, milestone)
            notifier.notify_unreachable_milestone(dico[milestone])

    def remind_recipient(self, dico, klass):
        """
        Send notification for owner or reporter
        """
        for recipient in dico:
            _dico = dico[recipient]
            for milestone in _dico:
                notifier = klass(self.env, milestone)
                notifier.notify_opened_ticket(recipient, _dico[milestone])

    def wake_up(self, *args):
        ahead = UnreachableMilestoneTask.ahead_days
        if len(args) > 0:
            ahead = int(args[0])

        # look opened ticket in near milestone
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        # select ticket whom milestone are due in less than some days ahead
        ahead_time = datetime.now(utc) + timedelta(days=ahead)
        cursor.execute(self.select_near_milestone_ticket,
                       (to_utimestamp(ahead_time),))

        dico, dico_owner, dico_reporter = {}, {}, {}
        for ticket, owner, reporter, milestone, summary, due in cursor:
            msg = 'warning ticket %d will probably miss its milestone %s' % (
                  ticket, milestone)
            self.env.log.info(msg)
            ticket_data = {
                'ticket': ticket,
                'owner': owner,
                'reporter': reporter,
                'milestone': milestone,
                'summary': summary,
                'due': due
            }
            dico.setdefault(milestone, []).append(ticket_data)
            self._set_recipient_data(dico_owner, owner, milestone, ticket_data)
            self._set_recipient_data(dico_reporter, reporter, milestone,
                                     ticket_data)

        self.remind_unreachable_recipients(dico)
        self.remind_recipient(dico_owner, OwnerOpenedTicketNotification)
        self.remind_recipient(dico_reporter, ReporterOpenedTicketNotification)

    def getId(self):
        return self.cronconf.UNREACHABLE_MILESTONE_TASK_BASEKEY

    def getDescription(self):
        return self.__doc__


class AutoPostponeTask(Component, ICronTask):
    """
    Scan closed milestone for still opened ticket then posptone those tickets
    to the next milestone
    """
    implements(ICronTask)

    select_next_milestone = """
        SELECT m.name, m.completed, m.due
        FROM milestone m
        WHERE (m.completed is NULL OR m.completed = 0)
        AND m.due is not NULL
        AND m.due > 0
        ORDER BY m.due ASC LIMIT 1
    """

    select_closed_milestone_ticket = """
        SELECT t.id , t.milestone
        FROM ticket t, milestone m
        WHERE t.status != 'closed'
        AND t.milestone = m.name
        AND m.completed is not NULL and m.completed > 0
    """

    def wake_up(self, *args):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        # find still opened more recent milestone
        # select ticket whom milestone are due in less than specified delay
        next_milestone = None
        cursor.execute(self.select_next_milestone)
        for name, completed, due in cursor:
            next_milestone = name

        if not next_milestone:
            msg = 'No opened milestone found. Cannot postpone tickets'
            self.env.log.debug(msg)
            return

        # select ticket whom milestone are due in less than specified delay
        cursor.execute(self.select_closed_milestone_ticket)
        for ticket_id, milestone in cursor:
            msg = 'Ticket %s is opened in closed milestone %s. ' \
                  'Should postpone this ticket to %s' % (
                  ticket_id, milestone, next_milestone)
            self.env.log.debug(msg)
            ticket = Ticket(self.env, ticket_id)
            ticket.populate({'milestone': next_milestone})
            ticket.save_changes(self.getId(), msg)

    def getId(self):
        return 'auto_postpone'

    def getDescription(self):
        return self.__doc__


class TicketDeadlineNotification(NotifyEmail):

    template_name = 'notify_ticket_near_deadline.txt'
    column_length = 75

    def __init__(self, env):
        NotifyEmail.__init__(self, env)
        ambiguous_char_width = env.config.get('notification',
                                              'ambiguous_char_width',
                                              'single')
        self.ambiwidth = (1, 2)[ambiguous_char_width == 'double']

    def get_recipients(self, ticket):
        torcpts = ticket.values.get('owner')
        ccrcpts = set([ticket.values.get('reporter')])
        cc_users = ticket.values.get('cc')
        if cc_users is not None:
            for cc_user in cc_users.split(','):
                ccrcpts.add(cc_user.strip())
        self.env.log.debug('get_recipients: %s, %s' % (torcpts, ccrcpts))
        return [torcpts], list(ccrcpts)

    def set_template_data(self, ticket):
        ticket_values = ticket.values.copy()
        ticket_values['id'] = ticket.id
        ticket_values['link'] = self.env.abs_href.ticket(ticket.id)
        ticket_values['description'] = wrap(
            ticket_values.get('description', ''), self.column_length,
            initial_indent=' ', subsequent_indent=' ', linesep='\n',
            ambiwidth=self.ambiwidth)
        self.data.update({
            'ticket': ticket_values,
        })

    def make_subject(self, ticket):
        from genshi.template.text import NewTextTemplate
        template = self.config.get('notification', 'ticket_subject_template')
        template = NewTextTemplate(template.encode('utf8'))
        data = {
            'prefix': '[Deadline Warning]',
            'summary': ticket['summary'],
            'ticket': ticket,
            'env': self.env,
        }
        return template.generate(**data).render('text', encoding=None).strip()

    def remind(self, ticket_id):
        self.env.log.debug('remind: %s' % ticket_id)
        ticket = Ticket(self.env, ticket_id)
        self.set_template_data(ticket)
        subject = self.make_subject(ticket)
        NotifyEmail.notify(self, ticket, subject)

    def send(self, torcpts, ccrcpts):
        self.env.log.debug('send: %s, %s' % (torcpts, ccrcpts))
        return NotifyEmail.send(self, torcpts, ccrcpts)


class TicketDeadlineTask(Component):
    """
    Remind relevant users when the ticket is near deadline.
    """
    implements(ICronTask, ITemplateProvider)

    days_before = IntOption('traccron', 'days_before', 3,
        'Notify the days before the ticket deadline.')

    date_field = Option('traccron', 'date_field', None,
        'Specify the custom field name for deadline.')

    date_format = Option('traccron', 'date_format', '%Y-%m-%d',
        """Specify the date format stored in table as string
        so that it can convert string into datetime.""")

    select_ticket_near_deadline = """
        SELECT t.id, t.status, c.value
        FROM ticket t, ticket_custom c
        WHERE t.id = c.ticket
        AND t.status <> 'closed'
        AND c.name = %s
        AND c.value is not NULL AND c.value <> ''
    """

    def _get_params(self, args):
        date_field = self.date_field
        date_format = self.date_format
        days_before = self.days_before
        if len(args) == 3:  # for debug/test
            date_field, date_format, days_before = args
        _msg = 'wake_up: %s, %s, %s'
        self.env.log.debug(_msg % (date_field, date_format, days_before))
        return date_field, date_format, days_before

    def get_tickets(self, date_field):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(self.select_ticket_near_deadline, (date_field,))
        for values in cursor:
            yield values

    def need_notify(self, now, deadline, date_format, days_before):
        try:
            # don't use datetime.strptime for 2.4 compatibility
            due_date = datetime(*strptime(deadline, date_format)[:6])
            due_date = due_date - timedelta(days=int(days_before))
        except Exception, e:
            self.env.log.error('cannot convert %s: %s' % (deadline, e))
        else:
            self.env.log.debug('need_notify: %s, %s' % (now, due_date))
            return now >= due_date
        return False

    # ICronTask methods
    def wake_up(self, *args):
        date_field, date_format, days_before = self._get_params(args)
        if date_field is None:
            self.env.log.info('wake_up: date_field is not specified')
            return

        now = datetime.now()
        for ticket_id, status, deadline in self.get_tickets(date_field):
            if self.need_notify(now, deadline, date_format, days_before):
                TicketDeadlineNotification(self.env).remind(ticket_id)

    def getId(self):
        return 'ticket_deadline'

    def getDescription(self):
        return self.__doc__

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []
