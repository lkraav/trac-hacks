# -*- coding: utf-8 -*-

"""A simple captcha to allow anonymous ticket changes as long as the user
solves a math problem.

I thought that the ITicketManipulator prepare_ticket method would be the place
to add extra HTML stuff to the ticket page, but it seems to be for future use
only.  The only way I found that I could add to the HTML was by modifying the
Genshi template using the ITemplateStreamFilter.

I looked at http://trac-hacks.org/wiki/BlackMagicTicketTweaksPlugin for help
trying to understand how the Genshi transformation stuff worked.

Database setup borrowed from BSD licensed TicketModerator by John D. Siirola
at Sandia National Labs.  See http://trac-hacks.org/wiki/TicketModeratorPlugin

Author: Rob McMullen <robm@users.sourceforge.net>
License: Same as Trac itself
"""
import random
import re
import time

from genshi.filters.transform import Transformer
from trac.config import IntOption
from trac.core import Component, TracError, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Table
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.api import ITicketManipulator
from trac.util.html import html as tag
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.wiki.api import IWikiPageManipulator

schema = [
    Table('mathcaptcha_history', key='id')[
        Column('id', auto_increment=True),  # captcha ID
        Column('ip'),  # submitter IP address
        Column('submitted', type='int'),  # original submission time
        Column('left_operand', type='int'),  # left operand
        Column('operator'),  # operator (text string, "+", "-", etc)
        Column('right_operand', type='int'),  # right operand
        Column('solution', type='int'),  # solution
        Column('incorrect_solution'),  # incorrect guess
        Column('author'),  # author of incorrect guess
        Column('summary'),  # description included with failed guess
        Column('text'),  # field with any text typed by spambot
        Column('href'),  # url used in captcha
        Column('solved', type='boolean'),  # successfully solved?
    ],
]


class MathCaptchaPlugin(Component):

    implements(IEnvironmentSetupParticipant, IRequestHandler,
               ITemplateStreamFilter, ITicketManipulator,
               IWikiPageManipulator)

    timeout = 600  # limit of 10 minutes to process the page

    # The captcha history will be cleared after this number of days to allow
    # some postmortem as spam harvesters start to evolve
    clearout_days = 30

    # Database setup from http://trac-hacks.org/wiki/TicketModeratorPlugin
    # The current version for our portion of the database
    db_version = 2

    db_version_key = 'mathcaptcha_version'

    # Offset value for database id.  This is a large integer that is used to
    # modify the database row id so that the real database id is not stored
    # raw in the HTML.  Because the database ids may be small numbers, I don't
    # want the spam harvesters to simply copy fields from this hidden item
    # into the solution.
    id_offset = 5830285

    ban_after_failed_attempts = IntOption(
        'mathcaptcha', 'ban_after_failed_attempts', default=4,
        doc="""Number of invalid captchas before the IP is blocked. Set
        to `0` disable banning.
        """)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(self.db_version, self.db_version_key)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        ver = dbm.get_database_version(self.db_version_key)

        with self.env.db_transaction as db:
            if ver == 0:
                dbm.create_tables(schema)

            if ver == 1:
                db("""
                    ALTER TABLE mathcaptcha_history RENAME TO
                    mathcaptcha_history_temp
                    """)
                dbm.create_tables(schema)
                old_fields = [col.name for col in schema[0].columns]
                new_fields = old_fields[:]
                old_fields[old_fields.index('author')] = 'incorrect_author'
                old_fields[old_fields.index('summary')] = 'incorrect_summary'
                old_fields[old_fields.index('text')] = 'incorrect_text'
                db("""
                    INSERT INTO mathcaptcha_history (%s)
                    SELECT %s FROM mathcaptcha_history_temp
                    """ % (new_fields, old_fields))
                dbm.drop_tables('mathcaptcha_history_temp')

            # Record the current version of the db environment
            dbm.set_database_version(self.db_version, self.db_version_key)

    def create_math_problem(self, values):
        """Hook for generation of the math problem.

        As a side effect, should populate the values dict with the
        'left_operand', 'operator', 'right_operand' and 'solution' keys that
        will be placed in the database.

        Returns a text version of the math problem that is presented to the
        user.
        """
        values['left_operand'] = random.randint(1, 10)
        values['operator'] = "add"
        values['right_operand'] = random.randint(1, 10)
        values['solution'] = values['left_operand'] + values['right_operand']
        return "adding %d and %d" \
               % (values['left_operand'], values['right_operand'])

    def get_content(self, req):
        """Returns the Genshi tags for the new HTML elements representing the
        Captcha.
        """
        values = {'ip': req.remote_addr, 'submitted': int(time.time())}
        math_problem_text = self.create_math_problem(values)
        values['author'] = req.args.get('author')
        values['summary'] = req.args.get('field_summary')
        values['text'] = self.get_failed_attempt_text(req)
        values['href'] = req.path_info

        # Save the problem so that the post request of the web server knows
        # which request to process.  This is required on FCGI and mod_python
        # web servers, because there may be many different processes handling
        # the request and there's no guarantee that the same web server will
        # handle both the form display and the form submit.
        fields = values.keys()
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO mathcaptcha_history (%s) VALUES (%s)
                """ % (','.join(fields), ','.join(['%s'] * len(fields))),
                [values[name] for name in fields])
            id_ = db.get_last_id(cursor, 'mathcaptcha_history')
        self.log.debug(
            "%s %s %s%s: generating math solution: id=%d, %d %s %d = %d",
            req.remote_addr, req.remote_user, req.base_path, req.path_info,
            id_, values['left_operand'], values['operator'],
            values['right_operand'], values['solution'])

        # Obfuscating the names of input variables to trick spam harvesters
        # to put other data in the solutions field.  The math solution is
        # named "email" in the hopes that it will attract email addresses
        # instead of numbers.  The database key is named "url" to try to
        # attract non-numbers
        content = tag.div()(
            tag.label("Anonymous users are allowed to post by %s "
                      % math_problem_text) +
            tag.input(type='text', name='email', class_='textwidget',
                      size='5') +
            tag.input(type='hidden', name='url',
                      value=str(id_ + self.id_offset))
        )
        return content

    def is_validation_needed(self, req):
        """Hook to determine whether or not the math captcha should be shown.

        Currently, only anonymous users get shown the captcha, but this could
        be modified for local purposes.
        """
        return req.authname == 'anonymous'

    def is_banned(self, req):
        if self.ban_after_failed_attempts:
            failed = 0
            for solved, in self.env.db_query("""
                    SELECT solved FROM mathcaptcha_history WHERE ip=%s
                    """, (req.remote_addr,)):
                if solved == 0:
                    failed += 1
            return failed >= self.ban_after_failed_attempts

    def validate_mathcaptcha(self, req):
        """Validates the user (or spammer) input

        Uses the database storage to compare the user input with the correct
        solution.
        """
        # The database key is named 'url' as described in get_content
        id = int(req.args.get('url')) - self.id_offset

        # Look up previously stored data to compare the solution
        fields = ['ip', 'submitted', 'left_operand', 'operator',
                  'right_operand', 'solution']
        values = {}
        for row in self.env.db_query("""
                SELECT %s FROM mathcaptcha_history WHERE id=%%s
                """ % ','.join(fields), (id,)):
            if not row:
                self.log.error("id=%d not found in mathcaptcha_history", id)
                return [(None, "Invalid key in HTML")]
            for i in range(len(fields)):
                values[fields[i]] = row[i]

        if values['submitted'] + self.timeout < time.time():
            return [
                (None, "Took too long to submit page.  Please submit again.")]

        # The solution is named 'email' in the form submission as described
        # in get_content
        user_solution = req.args.get('email')
        error = self.verify_solution(req, values, user_solution)

        if error:
            self.store_failed_attempt(req, id, user_solution)

            # Only take the time to clean out history of a failed solution,
            # because we don't care how long we take on a failure.  Success
            # should be quick, and it's not important that the history be
            # cleaned out exactly on time.
            self.clean_history()
        else:
            self.store_successful_attempt(req, id)

        # Ban IP addresses after repeated failures
        if self.is_banned(req):
            self.log.error(
                "%s %s %s%s: Banned after %d failed attempts",
                req.remote_addr, req.remote_user, req.base_path,
                req.path_info, self.ban_after_failed_attempts)
            self.store_failed_attempt(req, id, "IP IS NOW BANNED!")
            raise TracError("Too many failed attempts")

        return error

    def verify_solution(self, req, values, user_solution):
        try:
            solution = int(user_solution)
            if values['solution'] == solution:
                self.log.debug(
                    "%s %s %s%s: Solution: '%s' author=%s comment:\n%s",
                    req.remote_addr, req.remote_user, req.base_path,
                    req.path_info, user_solution, req.args.get('author'),
                    self.get_failed_attempt_text(req))
                error = []
            else:
                self.log.error(
                    "%s %s %s%s: Error in math solution: %d %s %d != %s "
                    "author=%s comment:\n%s", req.remote_addr,
                    req.remote_user, req.base_path, req.path_info,
                    values['left_operand'], values['operator'],
                    values['right_operand'], user_solution,
                    req.args.get('author'),
                    self.get_failed_attempt_text(req))
                error = [(None, "Incorrect solution -- try solving the "
                                "equation again!")]
        except:
            self.log.error(
                "%s %s %s%s: Bad digits: '%s' author=%s comment:\n%s",
                req.remote_addr, req.remote_user, req.base_path,
                req.path_info, user_solution, req.args.get('author'),
                self.get_failed_attempt_text(req))
            error = [(None,
                      "Anonymous users are only allowed to post by solving "
                      "the math problem at the bottom of the page.")]
        return error

    def store_failed_attempt(self, req, id, user_solution):
        self.env.db_transaction("""
            UPDATE mathcaptcha_history
            SET incorrect_solution=%s,author=%s,summary=%s,TEXT=%s,solved=%s
            WHERE id=%s
            """, (user_solution, req.args.get('author'),
                  req.args.get('field_summary'),
                  self.get_failed_attempt_text(req),
                  False, id))

    def store_successful_attempt(self, req, id):
        self.env.db_transaction("""
            UPDATE mathcaptcha_history SET solved=%s WHERE id=%s
            """, (True, id))

    def get_failed_attempt_text(self, req):
        text = ""
        field = req.args.get('field_description')
        if field:
            text += field
        field = req.args.get('comment')
        if field:
            text += field
        return text

    def clean_history(self, days=None):
        # History after a certain number of days is cleared out
        if days is None:
            days = self.clearout_days
        older_than = time.time() - (days * 24 * 60 * 60)

        self.env.db_transaction("""
            DELETE FROM mathcaptcha_history WHERE submitted<%s
            """, (older_than,))

    def show_banned(self, req):
        raise TracError("Too many failed attempts")

    # ITemplateStreamFilter interface

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the
        template to be rendered, `stream` is the event stream and `data` is
        the data for the current template.

        See the Genshi documentation for more information.
        """

        add_captcha = False
        if data['authname'] == 'anonymous':
            if self.is_banned(req):
                self.log.debug("%s %s %s%s: IP banned as spammer",
                               req.remote_addr, req.remote_user,
                               req.base_path, req.path_info)
                stream = tag.label("System offline.")
                return stream

            if filename == 'ticket.html':
                tid = data['ticket'].id
                if tid is None:  # New ticket
                    add_captcha = 'TICKET_CREATE' in req.perm
                else:
                    add_captcha = 'TICKET_MODIFY' in req.perm or \
                                  'TICKET_APPEND' in req.perm
            elif filename == 'wiki_edit.html':
                add_captcha = 'WIKI_MODIFY' in req.perm

        if add_captcha:
            # Insert the math question right before the submit buttons
            stream = stream | Transformer('//div[@class="buttons"]').before(
                self.get_content(req))
        return stream

    # ITicketManipulator interface

    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.

        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with
        the ticket. Therefore, a return value of `[]` means everything is OK.
        """
        if self.is_validation_needed(req):
            return self.validate_mathcaptcha(req)
        return []

    # IWikiPageManipulator interface

    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        """Validate a wiki page after it's been populated from user input.

        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with
        the ticket. Therefore, a return value of `[]` means everything is OK.
        """
        if self.is_validation_needed(req):
            return self.validate_mathcaptcha(req)
        return []

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(
            r'/mathcaptcha-(attempts|clear|successful)(?:_trac)?(?:/.*)?$',
            req.path_info)

    def process_request(self, req):
        req.perm.require('TRAC_ADMIN')

        matches = re.match(r'/mathcaptcha-clear(?:_trac)?(?:/.*)?$',
                           req.path_info)
        if matches:
            self.process_clear(req)
        else:
            matches = re.match(r'/mathcaptcha-successful(?:_trac)?(?:/.*)?$',
                               req.path_info)
            if matches:
                self.process_successful(req)
                return
        self.process_attempts(req)

    def process_clear(self, req):
        self.clean_history(0)

    def process_attempts(self, req):
        req.send_response(200)
        req.send_header('Content-Type', 'text/html')

        fields = ['ip', 'submitted', 'href', 'incorrect_solution', 'author',
                  'summary', 'text', 'solved']
        html = "<table border><tr><th>%s</th></tr>\n" \
               % "</th><th>".join(fields)
        lines = []
        for row in self.env.db_query("""
                SELECT %s FROM mathcaptcha_history ORDER BY submitted
                """ % ','.join(fields)):
            if row[-1] is not None and not row[-1]:
                lines.append("<tr><td>%s</td></tr>\n" % "</td><td>".join(
                    [str(i) for i in row]))
        html += "\n".join(lines) + "</table>"
        req.send_header('Content-length', str(len(html)))
        req.end_headers()
        req.write(html)

    def process_successful(self, req):
        req.send_response(200)
        req.send_header('Content-Type', 'text/html')

        fields = ['ip', 'submitted', 'href', 'solution', 'author', 'summary',
                  'text', 'solved']
        html = "<table border><tr><th>%s</th></tr>\n" \
               % "</th><th>".join(fields[:-1])
        lines = []
        for row in self.env.db_query("""
                SELECT %s FROM mathcaptcha_history ORDER BY submitted
                """ % ','.join(fields)):
            if row[-1]:
                values = list(row[:-1])
                values[1] = time.asctime(time.localtime(values[1]))
                lines.append("<tr><td>%s</td></tr>\n" % "</td><td>".join(
                    [str(i) for i in values]))
        html += "\n".join(lines) + "</table>"
        req.send_header('Content-length', str(len(html)))
        req.end_headers()
        req.write(html)
