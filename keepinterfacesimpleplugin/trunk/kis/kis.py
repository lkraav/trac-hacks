from __future__ import print_function

# -*- coding: utf-8 -*-
#
#------------------------------------------------------------------------------
# Copyright (c) Jonathan Ashley <trac@ifton.co.uk> 2015-2016
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

###############################################################################

class IConfigFunction(Interface):
    pass

# The following docstring appears on the Trac plugin administration page.

class BuiltInConfigFunctions(Component):
    """ BuiltInConfigFunctions

=== Built-in functions ===
        - `has_role(<group_name> [, <user_name>])` - Returns True if the named user is a member of the named permissions group. If no user name is supplied, defaults to the user viewing the page. Returns False otherwise.
        - `is_parent([<ticket>]) - Returns True if any ticket has a field named "parent" that contains "#<n>" where <n> is the number of the given ticket. If no ticket number is given, defaults to the current ticket. Returns False otherwise.

=== Implementing user-defined functions ===
User-defined functions that can be called from the configuration file can be implemented by adding a Python file to the Trac plugins folder that implements the `IConfigFunction` interface. For example:
{{{
from trac.core import *
from kis import IConfigFunction

class MyConfigFunctions(Component):
    ''' Local functions for use by 'kisplugin' configuration files.
    '''
    implements(IConfigFunction)

    # Example: implement named string constants
    def safety(self, req, safety_enum):
        if safety_enum == 'YES':
            return 'Safety related'
        if safety_enum == 'OK':
            return 'Safety related - OK to close'
        if safety_enum == 'NO':
            return 'Not safety related'
}}}
This example would allow `safety('OK')` to return the string `Safety related - OK to close`.
    """
    implements(IConfigFunction)

    def has_role(self, req, *args):
        # Returns whether a user is a member of a permissions group.
        # If there is only one argument, the current user is assumed.
        # The optional second argument specifies a particular user.
        def expand(group, expanded=set()):
            expanded.add(group)
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute('SELECT DISTINCT username FROM permission '
                'WHERE action = "%s"' % group)
            for username in cursor:
                inner_cursor = db.cursor()
                inner_cursor.execute('SELECT COUNT(*) FROM permission '
                    'WHERE action = "%s"' % username[0])
                if inner_cursor.fetchone()[0]:
                    if username[0] not in expanded:
                        for user in expand(username[0], expanded):
                            yield user
                else:
                    yield username[0]

        if len(args) < 1 or len(args) > 2:
            raise ConfigurationError('has_role() called with %s arguments' %
                len(args))
        role = args[0]
        if len(args) == 2:
            user = args[1]
        else:
            user = req.authname.encode('utf-8')
        return user in expand(role)

    def is_parent(self, req, *args):
        # Returns True if another ticket has a field named 'parent' that
        # contains '#<n>', where <n> is the number of the current ticket.
        # Returns False otherwise.
        if len(args) > 1:
            raise ConfigurationError('is_parent() called with %s arguments' %
                len(args))

        if req.path_info.startswith('/newticket'):
            return False

        if len(args) == 1:
            ticket = args[0].lstrip('#')
        else:
            ticket = req.args['id']
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM ticket_custom WHERE '
            'name="parent" AND value = "#%s"' % ticket)
        return cursor.fetchone()[0] > 0

###############################################################################

class Lexer():
    def __init__(self, symbol_table, config_functions, req):
        # Initialise state required for lexer.
        self.symbol_table = symbol_table
        self.config_functions = config_functions
        self.req = req
        self.look = ['', '']

    # 'tokeniser' looks for tokens at the start of 'rest' and returns with the
    # token text placed into 'token', and the token type into 'token_type'.
    # There are three types of token, each indicated with a single character:
    #
    #    - F - means that the text in 'token' identifies a Field;
    #    - O - means that the text in 'token' is an Operator;
    #    - S - means that the text in 'token' is a String.
    #
    # The variable 'rest' is updated to remove the matched token.

    def tokeniser(self, x):
        # Ignoring whitespace, split x on words,
        # on tokens ',', '||', '(', ')', '&&', '!', '==', '!=', '~=' or 'in',
        # or on strings delimited by single quotes.

        m = re.search('^(\w+) *(.*)', x)
        if m:
            return 'F', m.group(1), m.group(2)

        m = re.search('^(in|==|\(|\)|&&|\|\||!=|~=|!|,) *(.*)', x)
        if m:
            return 'O', m.group(1), m.group(2)

        m = re.search("^'([^']*)' *(.*)", x)
        if m:
            return 'S', m.group(1), m.group(2)

        if not x:
            return None, '', 'EOF'

        return None, 'ERR', x

    def match(self, m):
        if self.look[1] == m:
            debug('--> %s' % m)
            self.look[0], self.look[1], self.rest = self.tokeniser(self.rest)
        else:
            raise ConfigurationError('Syntax error: %s; expected %s' %
                                     (self.look[1], m))

    def term(self):
        debug('^ term()')

        if self.look[1] == '(':
            self.match('(')
            v, text = self.expression()
            self.match(')')
            debug('TERM expression (%s) --> %s' % (v, '(%s)' % text))
            return v, '(%s)' % text

        if self.look[0] == 'S':
            v = self.look[1]
            self.match(v)
            debug("TERM literal ('%s') --> '%s'" % (v, v))
            return v, "'%s'" % v

        if self.look[0] == 'F':
            sym = self.look[1]
            # Look ahead. If next token is '(', this is a function call.
            self.match(self.look[1])
            if self.look[1] == '(':
                self.match(self.look[1])
                args, text = self.param_list()
                v = None
                for provider in self.config_functions:
                    funcs = provider.__class__.__dict__
                    if sym in funcs:
                        v = funcs[sym].__get__(provider)(self.req, *args)
                        if v != None:
                            break
                self.match(')')
                sym = '%s(%s)' % (sym, text)
                debug("TERM function ('%s') --> %s" % (v, sym))
            else:
                v = self.symbol_table[sym]
                if v == None:
                    raise ConfigurationError(
                        "No field named '%s' is defined" % sym)
                debug("TERM symbol ('%s') --> %s" % (v, sym))
            return v, sym

        raise ConfigurationError('Unexpected terminal %s' % self.look[1],
                                 title='Syntax error in trac.ini [kis_warden]',
                                 show_traceback=True)

    def param_list(self):
        if self.look[1] == ')':
            v_list = []
            sym = ''
        else:
            v, sym = self.term()
            v_list = [v]
            if self.look[1] == ',':
                self.match(',')
                v, text = self.param_list()
                v_list = v_list + v
                sym = sym + ', %s' % text
        return v_list, sym

    def cmp_list(self, t):
        debug('^ cmp_list(%s)' % t)

        if self.look[1] == '(':
            self.match('(')
            v, text = self.cmp_list(t)
            self.match(')')
            debug('CMP_LIST cmp_list (%s) --> %s' %
                    (v, "'%s' in (%s)" % (t, text)))
            return v, '(%s)' % text

        v, text = self.term()
        if self.look[1] == ',':
            self.match(',')
            tmp, text2 = self.cmp_list(t)
            debug('CMP_LIST comma (%s) --> %s' %
                ((t == v) or tmp, "'%s' in %s, %s" % (t, text, text2)))
            return (t == v) or tmp, '%s, %s' % (text, text2)

        debug('CMP_LIST (%s) --> %s' % (t == v, "'%s' in %s" % (t, text)))
        return t == v, text

    def comparison(self):
        debug('^ comparison()')

        if self.look[1] == '!':
            self.match('!')
            v, text = self.comparison()
            v = not v
            debug('EXPR not (%s) --> %s' % (v, '!%s' % text))
            return v, '!%s' % text

        v, text = self.term()
        if self.look[1] in ('==', '!=', '~='):
            op = self.look[1]
            self.match(op)
            e, text2 = self.term()
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
        if self.look[1] == 'in':
            self.match('in')
            e, text2 = self.cmp_list(v)
            debug('IN (%s) --> %s' % (e, '%s in %s' % (text, text2)))
            return e, '%s in %s' % (text, text2)

        return v, text

    def and_expression(self):
        debug('^ and_expression()')

        v, text = self.comparison()
        if self.look[1] == '&&':
            self.match('&&')
            e, text2 = self.and_expression()
            debug('AND_EXPR and (%s) --> %s' % ((v and e),
                                                '%s && %s' % (text, text2)))
            return v and e, '%s && %s' % (text, text2)
        debug('AND_EXPR (%s) --> %s' % (v, text))
        return v, text

    def expression(self):
        debug('^ expression()')

        v, text = self.and_expression()
        if self.look[1] == '||':
            self.match('||')
            e, text2 = self.expression()
            debug('EXPR or (%s) --> %s' %
                    ((v or e), '%s || %s' % (text, text2)))
            return v or e, '%s || %s' % (text, text2)
        debug('EXPR (%s) --> %s' % (v, text))
        return v, text

    def evaluate(self, predicate):
        self.look[0], self.look[1], self.rest = self.tokeniser(predicate)
        return self.expression()

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

only designated approver can approve = !has_role('approver') && approval != _approval && approval == 'Approved'
}}}
    The first rule means that the ticket cannot be closed if the 'approval' field has not been set to the value 'Approved'. The second rule means that only a user who is a member of the group 'approver' can change the 'approval' field to that value.
    '''

    implements(ITicketManipulator)

    config_functions = ExtensionPoint(IConfigFunction)

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        """ Not currently called, but should be provided for future
            compatibility.
        """
        pass

    def validate_ticket(self, req, ticket):
        """ Make sure required conditions for the next state the ticket will
            be in have been met.
        """

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

                return 'status' in action_changes and \
                    action_changes['status'] or self.ticket['status']

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

        symbol_table = Symbol_Table(self.env, req, ticket)
        lexer = Lexer(symbol_table, self.config_functions, req)
        errors = []

        for rule, predicate in self.config.options('kis_warden'):
            e, text = lexer.evaluate(predicate)
            if e:
                errors.append((None, "Check '%s' failed: %s" % (rule, text)))
        return errors

###############################################################################

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
                  cmp_list ::= '(' cmp_list ')'
                             | term
                             | term ',' cmp_list
                      term ::= '(' expression ')'
                             | <field_name>
                             | <function_name> '(' param_list ')'
                             | '"' <string> '"'
                param_list ::= *empty*
                             | term
                             | term ',' param_list
}}}
    `~=` is an operator that returns True only if the value on the left is matched by the Javascript regular expression on the right. `in` is an operator that returns True only if the value on the left appears in the list on the right. The operators `!`, `==`, `!=`, `||` and `&&` are negation, equality, inequality, OR and AND respectively.

    The field name 'authname' is a special case that evaluates to the name of the user attempting the transition.

    For example, take the rules:
{{{
approval.visible = !status in 'new', 'closed'
approval.options.basic_set = Not assessed, Denied
approval.available.basic_set = true
approval.options.full_set = Approved
approval.available.full_set = has_role('approver') || _approval == 'Approved'
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

    config_functions = ExtensionPoint(IConfigFunction)

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
            if 'rv:11' in req.environ['HTTP_USER_AGENT'] \
                    or 'MSIE' in req.environ['HTTP_USER_AGENT']:
                # Provide Promise support for Internet Explorer.
                add_script(req, 'kis/bluebird.min.js')
            add_script(req, 'kis/kis.js')
        return template, data, content_type

    # IRequestHandler
    def match_request(self, req):
        return req.path_info.startswith('/ticket/kis') or \
            req.path_info.startswith('/kis')

    def process_request(self, req):
        if req.args['op'] == 'get_ini':
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
            req.send(json.dumps(page_data).encode('utf-8'), 'application/json')
        elif req.args['op'] == 'call_function':
            args = req.args.get('args[]')
            if type(args) == type(None):
                args = []
            if type(args) != type([]):
                args = [args]
            for provider in self.config_functions:
                funcs = provider.__class__.__dict__
                config_func = req.args['config_func']
                if config_func in funcs:
                    result = funcs[config_func].__get__(provider)(req, *args)
                    if result != None:
                        if type(result) == type(''):
                            result = repr(result)
                        req.send(json.dumps(result).encode('utf-8'),
                                 'application/json')
            # Send a null response if no handler responded.
            req.send(json.dumps(None).encode('utf-8'), 'application/json')
