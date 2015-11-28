from __future__ import print_function

# -*- coding: utf-8 -*-
#
#------------------------------------------------------------------------------
# Copyright (c) Jonathan Ashley <trac@ifton.co.uk> 2015
#------------------------------------------------------------------------------
#
# This file is part of the Keep Interface Simple plugin for Trac.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import json
import re

from pkg_resources import resource_filename

from trac.core import *
from trac.config import ConfigurationError
from trac.ticket import ITicketManipulator
from trac.ticket import TicketSystem
from trac.ticket.model import Ticket
from trac.web.api import IRequestFilter, IRequestHandler, RequestDone
from trac.web.chrome import add_script, ITemplateProvider

# Change 'debug' to be either the print function or a null function, depending
# on whether debugging is required.
debug = lambda x: None
# debug = print

# Globals for lexer.

look = ['', '']
rest = ''
symbol_table = []

# The lexer function 'tokeniser' looks for tokens at the start of 'rest' and
# returns with the token text placed into 'token', and the token type into
# 'token_type'. There are three types of token, each indicated with a single
# character:
#
#    - F - means that the text in 'token' identifies a Field;
#    - O - means that the text in 'token' is an Operator;
#    - S - means that the text in 'token' is a String.
#
# The variable 'rest' is updated to remove the matched token.

def tokeniser(x):
    # Ignoring whitespace, split x on words,
    # on tokens ',', '||', '(', ')', '&&', '!', '==', '!=', '~=', 'in' or
    # 'has_role',
    # or on strings delimited by single quotes.

    m = re.search('^(\w+) *(.*)', x)
    if m:
        return 'F', m.group(1), m.group(2)

    m = re.search('^(in|==|\(|\)|&&|\|\||!=|~=|!|,|has_role) *(.*)', x)
    if m:
        return 'O', m.group(1), m.group(2)

    m = re.search("^'([^']*)' *(.*)", x)
    if m:
        return 'S', m.group(1), m.group(2)

    if not x:
        return None, '', 'EOF'

    return None, 'ERR', x

def match(m):
    global look, rest
    if look[1] == m:
        debug('--> %s' % m)
        look[0], look[1], rest = tokeniser(rest)
    else:
        raise ConfigurationError('Syntax error: %s; expected %s' % (look[1], m))

def term():
    global look

    debug('^ term()')

    if look[1] == '(':
        match('(')
        v, text = expression()
        match(')')
        debug('TERM expression (%s) --> %s' % (v, '(%s)' % text))
        return v, '(%s)' % text

    if look[0] == 'S':
        v = look[1]
        match(v)
        debug("TERM literal ('%s') --> '%s'" % (v, v))
        return v, "'%s'" % v

    if look[0] == 'F':
        sym = look[1]
        try:
            v = symbol_table[sym]
        except KeyError:
            v = 'Undefined'
        match(look[1])
        debug("TERM symbol ('%s') --> %s" % (v, sym))
        return v, sym

    raise ConfigurationError('Unexpected terminal %s' % look,
                             title='Syntax error in trac.ini [kis_warden]',
                             show_traceback=True)

def cmp_list(t):
    global look

    debug('^ cmp_list(%s)' % t)

    if look[1] == '(':
        match('(')
        v, text = cmp_list(t)
        match(')')
        debug('CMP_LIST cmp_list (%s) --> %s' % (v, "'%s' in (%s)" % (t, text)))
        return v, '(%s)' % text

    v, text = term()
    if look[1] == ',':
        match(',')
        tmp, text2 = cmp_list(t)
        debug('CMP_LIST comma (%s) --> %s' %
            ((t == v) or tmp, "'%s' in %s, %s" % (t, text, text2)))
        return (t == v) or tmp, '%s, %s' % (text, text2)

    debug('CMP_LIST (%s) --> %s' % (t == v, "'%s' in %s" % (t, text)))
    return t == v, text

def comparison():
    global look

    debug('^ comparison()')

    if look[1] == '!':
        match('!')
        v, text = comparison()
        v = not v
        debug('EXPR not (%s) --> %s' % (v, '!%s' % text))
        return v, '!%s' % text

    v, text = term()
    if look[1] in ('==', '!=', '~=', 'has_role'):
        op = look[1]
        match(op)
        e, text2 = term()
        if op == '==':
            debug('CMP compare_equal (%s) --> %s' %
                ((v == e), '%s == %s' % (text, text2)))
            return v == e, '%s == %s' % (text, text2)
        if op == '!=':
            debug('CMP compare_unequal (%s) --> %s' %
                ((v != e), '%s != %s' % (text, text2)))
            return v != e, '%s != %s' % (text, text2)
        if op == '~=':
            debug('CMP compare_match (%s) --> %s' %
                (bool(re.search(e, v)), '%s ~= %s' % (text, text2)))
            return bool(re.search(e, v)), '%s ~= %s' % (text, text2)
        if op == 'has_role':
            debug('HAS_ROLE (%s) --> %s' % (v in symbol_table.get_role(e),
                '%s has_role %s' % (text, text2)))
            return v in symbol_table.get_role(e), \
                '%s has_role %s' % (text, text2)
    if look[1] == 'in':
        match('in')
        e, text2 = cmp_list(v)
        debug('IN (%s) --> %s' % (e, '%s in %s' % (text, text2)))
        return e, '%s in %s' % (text, text2)

    return v, text

def and_expression():
    global look

    debug('^ and_expression()')

    v, text = comparison()
    if look[1] == '&&':
        match('&&')
        e, text2 = and_expression()
        debug('AND_EXPR and (%s) --> %s' % ((v and e),
                                            '%s && %s' % (text, text2)))
        return v and e, '%s && %s' % (text, text2)
    debug('AND_EXPR (%s) --> %s' % (v, text))
    return v, text

def expression():
    global look

    debug('^ expression()')

    v, text = and_expression()
    if look[1] == '||':
        match('||')
        e, text2 = expression()
        debug('EXPR or (%s) --> %s' % ((v or e), '%s || %s' % (text, text2)))
        return v or e, '%s || %s' % (text, text2)
    debug('EXPR (%s) --> %s' % (v, text))
    return v, text


# The following docstring appears on the Trac plugin administration page.

class KisWarden(Component):
    ''' Prevents a commit from being accepted if certain conditions are not met, as described in the configuration file.

    The configuration file structure is
{{{
[kis_warden]
<rule name> = <predicate>
}}}
    Predicates describe the state of the ticket after a change has been submitted. If the predicate for any rule evaluates to 'true', then the change is blocked.

    The grammar of the predicates is the same as defined for the '!KisAssistant' component, except that the regular expression syntax is Python rather than Javascript.

    For example, take the rules:
{{{
approval required to close = status == 'closed' && approval != 'Approved'

only designated approver can approve = !authname has_role 'approver' && approval != _approval && approval == 'Approved'
}}}
    The first rule means that the ticket cannot be closed if the 'approval' field has not been set to the value 'Approved'. The second rule means that only a user who is a member of the group 'approver' can change the 'approval' field to that value.

    implements(ITicketManipulator)

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        """ Not currently called, but should be provided for future
            compatibility.
        """
        pass

    def validate_ticket(self, req, ticket):
        """ Make sure required fields for the next state have been the ticket
            will be in have been entered.
        """

        global symbol_table, look, rest

        class Symbol_Table(object):
            def __init__(self, env, req, ticket):
                self.env = env
                self.req = req
                self.ticket = ticket

            def _get_action_controllers(self, action):
                ''' Function modified from 'ticketvalidatorplugin',
                    copyright (C) 2008 Max Stewart <max.e.stewart@gmail.com>
                    and licensed under 3-clause BSD licence.
                '''
                for controller in TicketSystem(self.env).action_controllers:
                    actions = [action for weight, action in
                               controller.get_ticket_actions(self.req,
                                                             self.ticket)]
                    if action in actions:
                        yield controller

            def _get_next_state(self):
                ''' Get the state this ticket is going to be in.
                    Function modified from 'ticketvalidatorplugin',
                    copyright (C) 2008 Max Stewart <max.e.stewart@gmail.com>
                    and licensed under 3-clause BSD licence.
                '''
                if 'action' not in self.req.args:
                    return 'new'

                action = self.req.args['action']
                action_changes = {}

                for controller in \
                        self._get_action_controllers(action):
                    action_changes.update(
                        controller.get_ticket_changes(self.req,
                                                      self.ticket,
                                                      action))

                return 'status' in action_changes and action_changes['status'] \
                    or self.ticket['status']

            def __getitem__(self, key):
                ''' Look up the value of a field. The field name 'authname' is
                    a special case, returning the name of the user attempting
                    the transition.
                    If the field name is prefixed by '_', this indicates that
                    the original value of a field that is being changed in the
                    current transition should be provided.
                '''

                if key == 'authname':
                    return self.req.authname
                elif key == 'true':
                     return True
                elif key == 'false':
                     return False
                elif key.startswith('_'):
                     key = key[1:]
                     if key in self.ticket._old:
                        return self.ticket._old[key]
                if key == 'status':
                    # This is handled specially, as there may be action
                    # controllers that change or restrict the next status.
                    return self._get_next_state()
                return self.ticket.get_value_or_default(key)

            def get_role(self, group):
                ''' Recursive look-up returning a list of names that are
                    members of the given permissions group. Duplicates are not
                    eliminated.
                '''
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute('SELECT DISTINCT username FROM permission '
                    'WHERE action = "%s"' % group)
                result = []
                for username in cursor:
                    inner_cursor = db.cursor()
                    inner_cursor.execute('SELECT COUNT(*) FROM permission '
                        'WHERE action = "%s"' % username[0])
                    if inner_cursor.fetchone()[0]:
                        # 'username' was actually a group; consider it as a
                        # role and expand it again.
                        result = result + self.get_role(username[0])
                    else:
                        # 'username' was not a group, so just return it.
                        result.append(username[0])
                return result

        symbol_table = Symbol_Table(self.env, req, ticket)
        errors = []

        for rule, predicate in self.config.options('kis_warden'):
            look[0], look[1], rest = tokeniser(predicate)
            e, text = expression()
            if e:
                errors.append((None, "Check '%s' failed: %s" % (rule, text)))
        return errors

#------------------------------------------------------------
class KisAssistant(Component):
    ''' Controls which fields, actions and options are available in the user interface.
    
    Also allows templates to be defined for initialising text fields.

    The configuration file structure is:
{{{
[kis_assistant]
<field_or_action_name>.visible = <predicate>
<field_name>.available.<option_set_name> = <predicate>
<field_name>.options.<option_set_name> = <option list>
<field_name>.available.<template_name> = <predicate>
<field_name>.template.<template_name> = <template_text>
}}}

    The rule attribute 'visible' defines when the associate field will be visible in the interface. Dropdown fields and radio button fields also have attributes 'options' and 'available'. The 'options' attribute is used to assign a name to a group of options, then the matching 'available' attribute for that name defines when those options are available.

    The ticket actions are accessed with a pre-defined field named 'action'. The available values for the ticket actions are the transition names defined in the configuration file.

    If no visibility rule is defined for a field, the field is visible by default. Similarly, if no availability rule is defined for an option, the option is available by default.

    In predicates, field names evaluate to the current value of the corresponding field, except for the special names 'status', which evaluates to the ticket status, 'authname', which evaluates to the current username, 'true' which evaluates True and 'false', which evaluates False. If the field name is prefixed with an underscore, it evaluates to the value of the field at the time the page was loaded.

    Text-type fields evaluate to their contents, checkboxes evaluate to true if checked or false if not, and radio buttons evaluate to the selected item if an item is selected or undefined if no item is selected.

    The grammar of the predicates is:
{{{
                expression ::= and_expression
                             | and_expression '||' expression
            and_expression ::= comparison
                             | comparison '&&' and_expression
                comparison ::= '!' comparison
                             | term
                             | term equ_op term
                             | term 'in' cmp_list
                     eq_op ::= '=='
                             | '!='
                             | '~='
                             | 'has_role'
                  cmp_list ::= '(' cmp_list ')'
                             | term
                             | term ',' cmp_list
                      term ::= '(' expression ')'
                             | <field_name>
                             | '"' <string> '"'
}}}
    `~=` is an operator that returns True only if the value on the left is matched by the Javascript regular expression on the right. `has_role` is an operator that returns True only if the value on the left is a member of the permissions group named on the right. `in` is an operator that returns True only if the value on the left appears in the list on the right. The operators `!`, `==`, `!=`, `||` and `&&` are negation, equality, inequality, OR and AND respectively.

    The field name 'authname' is a special case that evaluates to the name of the user attempting the transition.

    For example, take the rules:
{{{
approval.visible = !status in 'new', 'closed'
approval.options.basic_set = Not assessed, Denied
approval.available.basic_set = true
approval.options.full_set = Approved
approval.available.full_set = authname has_role 'approver' || _approval == 'Approved'
}}}
    This requires that a custom field named 'approval' is defined (either a Select or a Radio field) with options 'Not assessed', 'Denied' and 'Approved'. These rules state that the field only appears when the ticket status is other than 'new' or 'closed'. The options 'Not assessed' or 'Denied' are always available, but the option 'Approved' is only available if the user is a member of the 'approver' group or if the field already had the value 'Approved' when the page was loaded.

    Note that options defined in the Trac administration interface will appear by default unless specifically hidden by a rule. It isn't therefore strictly necessary to specify 'Not assessed' and 'Denied' here, but it can be clearer to do so.

    These restrictions are in the user interface only; none of the constraints are enforced. Define matching rules using the '!KisWarden' component if it's necessary to enforce the restrictions.

    The 'template' options work in a similar manner. For example:
{{{
evaluation.template.change = === Description ===\\nDescribe the change fully...
evaluation.available.change = evaluation_template == 'Change'
evaluation.template.fault = === Description ===\\nDescribe the fault fully...
evaluation.available.fault = evaluation_template == 'Fault'
evaluation.template.none =
evaluation.available.none = evaluation_template == 'None'
}}}
    This requires that a custom field named 'evaluation_template' is defined (either a Select or a Radio field) with options 'None', 'Change' and 'Fault'. Another custom Textarea field named 'evaluation' is defined. When 'evaluation_template' is set to 'Change', the 'evaluation' field will be initialised with the value of the `evaluation.template.change` option (shown here in a cut-down form; it would normally contain template entries for all the items of information that might be wanted in a Change evaluation). Similarly for 'evaluation_template' values of 'Fault' or 'None'. The 'evaluation' field will only be initialised if it is currently either empty or unchanged from one of the alternative template values.
    '''

    implements(IRequestFilter,
               IRequestHandler,
               ITemplateProvider)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('kis', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/newticket') or \
                req.path_info.startswith('/ticket/'):
            add_script(req, 'kis/kis.js')
        return template, data, content_type

    # IRequestHandler
    def match_request(self, req):
        return req.path_info.startswith('/ticket/kis') or \
            req.path_info.startswith('/kis')

    def process_request(self, req):
        def get_role(group):
            # Returns all the roles held by a given user.
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute('SELECT DISTINCT username FROM permission '
                'WHERE action = "%s"' % group)
            result = []
            for username in cursor:
                inner_cursor = db.cursor()
                inner_cursor.execute('SELECT COUNT(*) FROM permission '
                    'WHERE action = "%s"' % username[0])
                if inner_cursor.fetchone()[0]:
                    # 'username' was actually a group; consider it as a role
                    # and expand it again.
                    result = result + get_role(username[0])
                else:
                    # 'username' was not a group, so just return it.
                    result.append(username[0])
            return result

        if req.args['op'] == 'get_role':
            # We don't put this information in the initial data dump, as there
            # are any number of possible combinations of username and role.
            roles = get_role(req.args['role'])
            # req.send() method raises trac.web.api.RequestDone when complete.
            req.send(str(req.args['authname'] in roles).lower().
                     encode('utf-8'), 'text/plain')

        elif req.args['op'] == 'get_ini':
            # Create and send the initial data dump.
            items = self.config.parser.items('kis_assistant')
            config = {}
            for dotted_name, value in items:
                config_traverse = config
                for component in dotted_name.split('.'):
                    if not component in config_traverse:
                        if component.startswith('#'):
                            continue
                        config_traverse[component] = {}
                    config_traverse = config_traverse[component]
                config_traverse['#'] = \
                    re.sub("\s*,\s*", ",", value.strip()).split(",")

            if req.args['id']:
                ticket = Ticket(self.env, req.args['id'].lstrip('#'))
                status = ticket.get_value_or_default('status')
            else:
                status = 'new'
            page_data = { 'trac_ini' : config,
                          'status'   : status,
                          'authname' : req.authname }
            # req.send() method raises trac.web.api.RequestDone when complete.
            req.send(json.dumps(page_data).encode('utf-8'), 'text/plain')
