'use strict';

// ----------------------------------------------------------------------------
// Copyright (c) Jonathan Ashley <trac@ifton.co.uk> 2015
// ----------------------------------------------------------------------------
//
// This file is part of the Keep Interfaces Simple plugin for Trac.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

// Configuration file structure is
//
// [kis_interface]
// <field_name>.visible = <predicate>
// <field_name>.available.<option_set_name> = <predicate>
// <field_name>.options.<option_set_name> = <option list>
// <field_name>.available.<template_name> = <predicate>
// <field_name>.template.<template_name> = <template_text>
//
// In predicates, field names evaluate to the current value of the
// corresponding field, except for the special names 'status', which evaluates
// to the ticket status, 'authname', which evaluates to the current username,
// 'true' which evaluates true and 'false', which evaluates false. If the
// field name is prefixed with an underscore, it evaluates to the value of the
// field at the time the page was loaded.
//
// Text-type fields evaluate to their contents, checkboxes evaluate to true if
// checked or false if not, and radio buttons evaluate to the selected item if
// an item is selected or undefined if no item is selected.

// TracInterface
//
// Field operations that depend on the structure of the Trac page are wrapped
// in methods of this facade object, for easier maintenance.
//
// Methods in the public interface:
//  attach_change_handler(trigger, callback)
//      - add function callback() to be called when trigger field is changed;
//  first_available_item()
//      - return value of first available item in a select-one or radio field;
//  initial_val()
//      - return the value of the field at the first point it was evaluated;
//  is_visible(name)
//      - return a boolean indicating whether the named item is visible;
//  select(name)
//      - select the named item and fire its 'change' trigger;
//        return true if the item exists, false otherwise;
//  selected_item()
//      - return name of the currently selected item;
//  show_field(bool)
//      - hide the field if the parameter is false, show if true;
//  show_item(name, bool)
//      - hide the named item if the boolean parameter is false, show if true;
//        return true if the item exists, false otherwise;
//  trigger(event, additional_arguments?)
//      - fire the named event trigger;
//  val(new_value?)
//      - return the current value, set a new value if one is provided.
var TracInterface = function(field_name) {
    // Caches values of fields at the point they're first queried.
    if (typeof TracInterface.cache == 'undefined') {
        TracInterface.cache = {};
    }

    this.field_name = field_name;

    if (field_name == 'action') {
        // The 'action' field is a special case.
        this.select_field = $('[name=action][type=radio]');
        this.show_field = function (show) {
            return this.select_field.closest('fieldset').
                css('display', show ? '' : 'none');
        };
    } else {
        this.select_field = $('#field-' + field_name);
        if (this.select_field.length == 0) {
            // Radio button set.
            this.select_field = $('[name=field_' + field_name + ']');
        }
    }
};

TracInterface.prototype._item = function (name) {
    if (this.select_field.prop('type') == 'radio') {
        var result = this.select_field.filter('[value="' + name + '"]');
    } else {
        result = $('option[value="' + name + '"]', this.select_field);
    }
    return result;
};

TracInterface.prototype.attach_change_handler = function (trigger, callback) {
    var triggering_field = new TracInterface(trigger);

    return triggering_field.select_field.on('change', callback);
};

TracInterface.prototype.first_available_item = function () {
    var is_visible = function () { return this.style['display'] != 'none'; };

    if (this.select_field.prop('type') == 'radio') {
        var result = $('input', this.select_field.parent().
            filter(is_visible)).first();
    } else {
        result = this.select_field.children().filter(is_visible).first();
    }
    return result.val();
};

TracInterface.prototype.initial_val = function () {
    if (this.field_name in TracInterface.cache) {
        return TracInterface.cache[this.field_name];
    }
    return this.val();
};

TracInterface.prototype.is_visible = function (name) {
    var item = this._item(name);

    if (this.select_field.prop('type') == 'radio') {
        var result = item.parent().css('display');
    } else {
        result = item.css('display');
    }
    return result && (result != 'none');
};

TracInterface.prototype.select = function (name) {
    var item = this._item(name);

    if (this.select_field.prop('type') == 'radio') {
        item.checked(true);
    } else {
        item.prop('selected', true);
    }
    item.trigger('change');

    return item.length > 0;
};

TracInterface.prototype.selected_item = function () {
    if (this.select_field.prop('type') == 'radio') {
        var result = this.select_field.filter(':checked');
    } else {
        result = $(':checked', this.select_field);
    }
    return result.val();
};

TracInterface.prototype.show_field = function (show) {
    return this.select_field.closest('td').prev().andSelf().
        css('display', show ? '' : 'none');
};

TracInterface.prototype.show_item = function (name, show) {
    var item = this._item(name);

    if (this.select_field.prop('type') == 'radio') {
        item = item.parent();
    }
    item.css('display', show ? '' : 'none');

    return item.length > 0;
};

TracInterface.prototype.trigger = function () {
    return this.select_field.trigger.apply(this.select_field, arguments);
};

TracInterface.prototype.val = function () {
    var context = this.select_field;
    var result;

    switch (this.select_field.prop('type')) {
        case 'checkbox':
            result = context.checked.apply(context, arguments);
            break;
        case 'radio':
            context = context.filter(':checked');
            result = context.val.apply(context, arguments);
            break;
        default:
            result = context.val.apply(context, arguments);
    }

    if (!(this.field_name in TracInterface.cache)) {
        TracInterface.cache[this.field_name] = result;
    }

    return result;
};

// evaluate(predicate, depends, callback)
//
// Top-down parser to interpret the predicates used in the trac.ini file.
//
// 'predicate' parameter: The grammar for the predicates is described in the
// plugin's help documentation. The function attempts to detect syntax errors
// in the predicates and log an error message to the console.
//
// 'depends' parameter: If an array is provided for the 'depends' parameter,
// then the names of any fields required to evaluate the predicate are added
// to that array. This allows the caller to arrange for the predicate to be
// re-evaluated when necessary.
//
// 'callback' parameter: If the value of a field required to evaluate a
// predicate is not immediately available, evaluate() returns undefined. The
// 'callback' function is called once the field value is available.
//
// Return value: evaluate() either returns the value of the predicate, or
// returns undefined if the predicate cannot immediately be evaluated.

function evaluate(predicate, depends, callback) {
    var token_type = '';
    var token = '';
    var rest_of_input = predicate;

    // Results of permission queries are stored in the cache.
    if (typeof evaluate.cache == 'undefined') {
        evaluate.cache = {};
    }

    // config_error()
    //
    // Log an error detected in the configuration file.
    function config_error(type, where) {
        var chars_parsed = predicate.length - rest_of_input.length;

        if (window.console) {
            console.log(predicate);
            console.log(new Array(chars_parsed + where).join('-') + '^');
        }
        throw(type + ' error in trac.ini');
    }

    // next_token()
    //
    // Matches a token at the start of 'rest_of_input', setting 'token' to the
    // token text and 'token_type' to the token type. Token types may be field
    // names, operators or strings. The matched token is removed from
    // 'rest_of_input'.
    function next_token() {
        var m;

        // Ignoring whitespace, split the input on words...
        m = rest_of_input.match(/^(\w+)( *)(.*)/i);
        if (m) {
            token_type = 'field name'; token = m[1]; rest_of_input = m[3];
            return;
        }
        // ... or on one of the various operators...
        m = rest_of_input.match(/^(,|\|\||\(|\)|&&|==|!=|~=|in|!)( *)(.*)/i);
        if (m) {
            token_type = 'operator'; token = m[1]; rest_of_input = m[3];
            return;
        }
        // ... or on strings delimited by single quotes.
        m = rest_of_input.match(/^'([^']*)'( *)(.*)/);
        if (m) {
            token_type = 'string'; token = m[1]; rest_of_input = m[3];
            return;
        }

        if (rest_of_input) {
            config_error('lexical', 1);
        }
        token_type = 'EOF'; token = '';
    }

    function term() {
        var v;

        if (token == '(') {
            // term ::= '(' expression ')'
            next_token();
            v = expression();
            if (token != ')') {
                config_error('syntax', 1);
            }
            next_token();
        } else
        if (token_type == 'string') {
            // term ::= '"' <string> '"'
            v = token;
            next_token();
        } else
        if (token_type == 'field name') {
            // term ::= <field_name>
            if (token[0] == '_') {
                var field = new TracInterface(token.slice(1));
                v = field.initial_val();
            } else
            if (token == 'status') {
                // Can't use $('.trac-status a').text(), because that would
                // fail if previewing a transition to the next state.
                v = page_info['status'];
            } else
            if (token == 'authname') {
                v = page_info['authname'];
            } else
            if (token == 'true' || token == 'false') {
                v = eval(token);
            } else {
                // If we are looking for triggers, and the field is not yet
                // listed as a dependency for this predicate, add it now.
                if (depends && $.inArray(token, depends) == -1) {
                    depends.push(token);
                }
                var field = new TracInterface(token);
                v = field.val();
            }
            next_token();
        } else {
            config_error('syntax', -token.length);
        }
        return v;
    }

    function cmp_list(t) {
        var v;

        if (token == '(') {
            // cmp_list ::= '(' cmp_list ')'
            next_token();
            v = cmp_list(t);
            if (token != ')') {
                config_error('syntax', 1);
            }
            next_token();
        } else {
            // cmp_list ::= term
            v = (t == term());
            if (token == ',') {
                // cmp_list ::= term ',' cmp_list
                next_token();
                // Put cmp_list(t) first to ensure it gets evaluated.
                v = (cmp_list(t) || v);
            }
        }
        return v;
    }

    function comparison() {
        var v;

        if (token == '!') {
            // comparison ::= '!' comparison
            next_token();
            v = !comparison();
        } else {
            // comparison ::= term
            v = term();
            if (token == '==') {
                // comparison ::= term '==' term
                next_token();
                v = (v == term());
            } else
            if (token == '!=') {
                // comparison ::= term '!=' term
                next_token();
                v = (v != term());
            } else
            if (token == '~=') {
                // comparison ::= term '~=' term
                next_token();
                v = Boolean(v.match(term()));
            } else
            if (token == 'has_role') {
                // comparison ::= term 'has_role' term
                next_token();

                // If the answer is cached, uses that. Otherwise, makes the
                // request with a callback to cache the answer and retry, then
                // throws an error.
                var role = term();
                var cache_key = v + '/' + role;

                if (cache_key in evaluate.cache) {
                    v = evaluate.cache[cache_key];
                } else {
                    $.get('kis_get_role',
                        { op: 'get_role', authname: v, role: role },
                        function (result) {
                            evaluate.cache[cache_key] = eval(result);
                            callback();
                        }
                    );
                    throw 'retry';
                }
            } else
            if (token == 'in') {
                // comparison ::= term 'IN' cmp_list
                next_token();
                v = cmp_list(v);
            }
        }
        return v;
    }

    function and_expression() {
        var v;

        // and_expression ::= comparison
        v = comparison();
        if (token == '&&') {
            // and_expression ::= comparison '&&' and_expression
            next_token();
            // Put and_expression() first to ensure it gets evaluated.
            v = (and_expression() && v);
        }
        return v;
    }

    function expression() {
        var v;

        // expression ::= and_expression
        v = and_expression();
        if (token == '||') {
            // expression ::= and_expression '||' comparison
            next_token();
            // Put expression() first to ensure it gets evaluated.
            v = (expression() || v);
        }
        return v;
    }

    next_token();
    try {
        var result = expression();
        if (token) {
            config_error('syntax', -token.length);
        }
        return result;
    } catch (err) {
        if (err == 'retry') {
            // Predicate can't be evaluated yet; waiting for data.
            return undefined;
        } else {
            throw err;
        }
    }
}

// Field()
//
// Class-like object, instances of which are used to manage each field.
//
// Uses each field's settings in the trac.ini file to determine the
// conditions under which its visibility should change, or its available
// option-sets should be updated. Attaches handlers to every other field
// that has an affect on this field to re-evaluate these conditions as
// required.
function Field(field_name) {
    this.field_name = field_name;
    this.operations = page_info['trac_ini'][field_name];
    this.ui = new TracInterface(field_name);

    // The set of triggers that affect visibility of the field.
    this.visibility_triggers = [];
    // Flag to ensure visibility onchange handlers are only attached once.
    this.visibility_onchange_attached = false;

    // The set of triggers that affect the available options of the field.
    this.options_triggers = [];
    // Flag to ensure option-select onchange handlers are only attached once.
    this.options_onchange_attached = false;

    // The set of triggers that select the template for the field.
    this.template_triggers = [];
    // Flag to ensure template onchange handlers are only attached once.
    this.template_onchange_attached = false;
}

// add_one_option_set()
//
// Adds one set of options (from the trac.ini) to an option-select field.
// Called at setup time, and possibly called again shortly afterwards if a
// corresponding predicate can't be evaluated immediately. Called later by
// add_options() when that is invoked as an onchange handler.
//
// Returns 'true' for success; 'false' if the callback was scheduled.
Field.prototype.add_one_option_set = function (option_set, callback) {
    var predicate = this.operations['available'][option_set]['#'].join();
    var option_values = this.operations['options'][option_set]['#'];

    var show_set = evaluate(predicate, this.options_triggers, callback);
    if (show_set == undefined) {
        return false;
    }

    for (var value in option_values) {
        var name = option_values[value];

        if (!this.ui.show_item(name, show_set)) {
            if (this.field_name != 'action') {
                // Log a warning: that value isn't present. (This isn't true
                // for actions, which aren't always available in the
                // interface.)
                console.log("option '" + this.field_name +
                            "' value '" + name + "' not defined in trac.ini");
            }
        }
    }
    return true;
};

// add_options()
//
// Completely initialises an option-select field. Called at setup time, and
// possibly called again shortly afterwards if a predicate of an option set
// can't be evaluated immediately. Called later as an onchange handler of any
// field that might affect the contents of this field.
Field.prototype.add_options = function () {
    var callback = this.add_options.bind(this);

    for (var option_set in this.operations['available']) {
        if (this.add_one_option_set(option_set, callback) == false) {
            // This function has been rescheduled as a callback.
            return;
        }
    }

    // Ensure that a visible option is selected, if necessary and possible.
    if (!this.ui.is_visible(this.ui.selected_item())) {
        // Use the original value at page-load if available.
        if (this.ui.is_visible(this.ui.initial_val())) {
            this.ui.select(this.ui.initial_val());
        } else {
            this.ui.select(this.ui.first_available_item());
        }
    }

    if (!this.options_onchange_attached) {
        // Attach the onchange handlers.
        for (var triggers_index in this.options_triggers) {
            var trigger = this.options_triggers[triggers_index];
            this.ui.attach_change_handler(trigger, callback);
        }
        this.options_onchange_attached = true;
    }
};

Field.prototype.set_template = function () {
    var matches_a_template = function () {
        for (var template in this.operations['template']) {
            var content = this.operations['template'][template]['#'].join();
            if (this.val().replace(/[ \n]/g, '') ==
                    content.replace(/\\n/g, '\n').replace(/[ \n]/g, '')) {
                return true;
            }
        }
        return false;
    }.bind(this);

    var callback = this.set_template.bind(this);

    for (var template in this.operations['available']) {
        var predicate = this.operations['available'][template]['#'].join();
        var do_select = evaluate(predicate, this.template_triggers, callback);

        if (do_select == undefined) {
            return;
        }

        if (do_select) {
            // Apply template if field is empty or matches a template value.
            var content = this.operations['template'][template]['#'].join();
            if (this.val() == '' || matches_a_template()) {
                this.val(content.replace(/\\n/g, '\n'));
                // Notify other scripts that the field content has changed.
                this.ui.trigger('onpaste')
            }
        }
    }

    if (!this.template_onchange_attached) {
        // Attach the onchange handlers.
        for (var triggers_index in this.template_triggers) {
            var trigger = this.template_triggers[triggers_index];
            this.ui.attach_change_handler(trigger, callback);
        }
        this.template_onchange_attached = true;
    }
};

// set_visibility()
//
// Sets the visibility of a field or an action. Called at setup time, and
// possibly called again shortly afterwards if the corresponding predicate
// can't be evaluated immediately. Called later as an onchange handler of any
// field that might affect the contents of this field.
Field.prototype.set_visibility = function () {
    var predicate = this.operations['visible']['#'].join();
    var callback = this.set_visibility.bind(this);

    // Show or hide field according to the value of its visibility predicate.
    var make_visible = evaluate(predicate, this.visibility_triggers, callback);
    if (make_visible == undefined) {
        return;
    }
    this.ui.show_field(make_visible);

    if (!this.visibility_onchange_attached) {
        // Attach the onchange handlers.
        for (var triggers_index in this.visibility_triggers) {
            var trigger = this.visibility_triggers[triggers_index];
            this.ui.attach_change_handler(trigger, callback);
        }
        this.visibility_onchange_attached = true;
    }
};

// setup()
//
// Completely initialises a field; called exactly once for each field.
Field.prototype.setup = function () {
    if (this.operations['visible']) {
        this.set_visibility();
    }
    if (this.operations['options']) {
        this.add_options();
    }
    if (this.operations['template']) {
        this.set_template();
    }
};

// val()
//
// Returns or sets the Trac value of a field.
Field.prototype.val = function () {
    return this.ui.val.apply(this.ui, arguments);
};

// The page data provided by the server query.
var page_info;

// This function is called when the page has loaded. It queries the server to
// get the trac.ini data, the ticket status and the authenticated user name.
// Once the data has arrived, the fields are initialised accordingly.
$(function () {
    $.getJSON('kis_init',
        { op: 'get_ini', id: $('a.trac-id', '#ticket').text().slice(1) },
        function (data) {
            page_info = data;
            for(var field_name in page_info['trac_ini']) {
                var field = new Field(field_name);
                field.setup();
            }
        }
    );
});
