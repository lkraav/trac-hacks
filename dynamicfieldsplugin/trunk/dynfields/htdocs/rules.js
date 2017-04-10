/*
 * Rule 'class'
 */
var Rule = function (name) {
  var noop = function (input, spec) {};
  this.setup = noop;
  this.apply = noop;
  this.complete = noop;
  this.query = function (spec) {}; // for query page

  // register this rule by adding to global variable
  if (window.dynfields_rules == undefined)
    window.dynfields_rules = {};
  window.dynfields_rules[name] = this;
};


/*
 * ClearRule implementation
 */
var clearrule = new Rule('ClearRule'); // must match python class name exactly

// apply
clearrule.apply = function (input, spec) {
  if (input.attr('id').slice(6) !== spec.trigger)
    return;

  var target = spec.target;

  if (spec.clear_on_change == undefined)
    return;

  var field = jQuery('#field-' + target);
  if (field.hasClass('clearable')) {
    // only cascade rules if value changes
    var oldval = field.val();
    var newval = field.val('').val();
    if (oldval != newval)
      field.change(); // cascade rules
  } else {
    field.addClass('clearable');
  }
};


/*
 * CopyRule implementation
 */
var copyrule = new Rule('CopyRule'); // must match python class name exactly

// apply
copyrule.apply = function (input, spec) {
  var id = input.attr('id');
  if (spec.value === undefined ||
      !((id.endsWith('_reassign_owner') && spec.trigger == 'owner') ||
        id.slice(6) === spec.trigger))
    return;

  var $field = jQuery(get_selector(spec.target));
  if (spec.overwrite.toLowerCase() == 'false' && $field.val() != '')
    return;

  if ($field.hasClass('copyable')) {
    // only do effect if value is changing
    var doit = true;
    if ($field.is('select')) {
      var opts = [];
      $field.find('option').each(function (i, e) {
        opts.push(jQuery(e).text());
      });
      if (jQuery.inArray(input.val(), opts) == -1) {
        doit = false;
      }
    }
    if (doit && $field.val() != input.val()) {
      if (spec.target == 'owner' && !jQuery('#field-owner').length)
        jQuery('#action_reassign').click();
      $field.hide().removeAttr('disabled');
      $field.val(input.val()).change();
      $field.fadeIn('slow');
    }
  } else {
    $field.addClass('copyable');
  }
};


/*
 * DefaultRule implementation
 */
var defaultrule = new Rule('DefaultRule'); // must match python class name exactly

// apply
defaultrule.apply = function (input, spec) {
  if (input.attr('id').slice(6) !== spec.trigger)
    return;

  var $field = jQuery(get_selector(spec.target));

  if (!$field.hasClass('defaulted')) {
    $field.addClass('defaulted');
    var doit = true;
    var value = spec.value;

    // skip if field is hidden
    if ($field.is(":hidden"))
      return;

    // ensure default value is in list of select options
    if ($field.is('select')) {
      var opts = [];
      $field.find('option').each(function (i, e) {
        opts.push(jQuery(e).text());
      });
      if (jQuery.inArray(value, opts) == -1)
        doit = false;
    }

    // ensure an 'empty' option value for existing tickets (unless appending)
    if ($field.val().length > 1 &&
      window.location.pathname.indexOf('/ticket') > -1) {
      doit = spec.append.toLowerCase() == 'true';
      if (doit) {
        // append preference to text field's value
        var values = [];
        jQuery($field.val().split(',')).each(function (i, v) {
          values.push(jQuery.trim(v));
        });
        // the preference value could be comma-delimited list itself
        jQuery(value.split(',')).each(function (i, v) {
          v = jQuery.trim(v);
          if (jQuery.inArray(v, values) == -1) {
            values.push(v);
          }
        });
        value = values.join(', ');
      }
    }

    if (doit)
      $field.val(value).change(); // cascade rules
  }
};


/*
 * HideRule implementation
 */
var hiderule = new Rule('HideRule'); // must match python class name exactly

// setup
hiderule.setup = function (input, spec) {
  var id = input.attr('id');
  if (id) { // no input fields when on /query page
    // show and reset elements controlled by this input field
    var trigger = id.substring(6); // ids start with 'field-'
    jQuery('.dynfields-' + trigger)
      .removeClass('dynfields-hide dynfields-' + trigger)
      .show();
  }
};

// apply
hiderule.apply = function (input, spec) {
  var trigger = spec.trigger;
  var target = spec.target;

  // hide field in the header if cleared or always hidden
  var clear_on_hide = spec.clear_on_hide.toLowerCase() == 'true';
  var hide_always = spec.hide_always.toLowerCase() == 'true'
  if (clear_on_hide || hide_always) {
    th = jQuery('#h_' + spec.target);
    td = th.next('td');
    td.addClass('dynfields-hide dynfields-' + trigger);
    th.addClass('dynfields-hide dynfields-' + trigger);
  }

  if (input.attr('id').slice(6) !== spec.trigger)
    return;

  // process hide rule
  var v;
  if (input.attr('type') == 'checkbox')
    v = (input.is(':checked')) ? "1" : "0";
  else
    v = input.val();
  var l = spec.trigger_value.split('|'); // supports list of trigger values
  if ((jQuery.inArray(v, l) != -1 && spec.op == 'hide') ||
    (jQuery.inArray(v, l) == -1 && spec.op == 'show')) {

    // we want to hide the input fields's td and related th
    var field = jQuery('#field-' + target + ',input[name="field_' + target + '"]');
    var td = field.closest('td');
    var th = td.prev('th');
    var cls = 'dynfields-hide dynfields-' + trigger;
    if (spec.link_to_show.toLowerCase() == 'true')
      cls += ' dynfields-link';
    td.addClass(cls);
    th.addClass(cls);

    // let's also clear out the field's value to avoid confusion
    if (spec.clear_on_hide.toLowerCase() == 'true' &&
      field.val() && field.val().length) { // Chrome fix - see #8654
      if (field.attr('type') == 'checkbox') {
        if (field.is(':checked')) {
          field.removeAttr('checked').change();
        }
      } else {
        // only cascade rules if value changes
        var oldval = field.val();
        var newval = field.val('').val();
        if (oldval != newval)
          field.change(); // cascade rules
      }
    }
  }
};

// complete
hiderule.complete = function (input, spec) {
  jQuery('.dynfields-hide').hide();

  // update layout (see layout.js)
  inputs_layout.update(spec);
  header_layout.update(spec);

  // add link to show hidden fields (that are enabled to be shown)
  if (spec.link_to_show.toLowerCase() == 'true') {
    if (jQuery('#dynfields-show-link').length == 0) {
      var html = '<tr id="dynfields-show-link">' +
        '  <th></th><td></td><th></th><td>' +
        '    <a href="#no3" onClick="jQuery(\'.dynfields-link\').show(); jQuery(\'#dynfields-show-link\').remove();">Show hidden fields</a>' +
        '  </td>' +
        '</tr>';
      jQuery('.dynfields-link:last').parents('tbody:first').append(html);
    }
  }
};

// query
hiderule.query = function (spec) {
  // hide hide_always fields on /query page
  if (spec.hide_always.toLowerCase() == 'true') {
    // hide from columns section
    var query_form = jQuery('form#query')
    var filters_fieldset = query_form.find('fieldset#filters');
    filters_fieldset.find('input[value="' + spec.target + '"]')
      .prop('checked', false)
      .parent().hide();
    // hide from and/or column filters/dropdowns
    filters_fieldset.find('#add_filter option[value="' + spec.target + '"]') // trac <= 0.12.1
      .hide();
    filters_fieldset.find('.actions option[value="' + spec.target + '"]') // trac 0.12.2
      .hide();
    var columns_fieldset = query_form.find('fieldset#columns');
    columns_fieldset.find('input[value="' + spec.target + '"]')
      .prop('checked', false)
      .parent().hide();
    // Hide from "Group results by" dropdown.
    var group_select = query_form.find('#group');
    group_select.find('option[value="' + spec.target + '"]')
      .hide();
  }
};


/*
 * ValidateRule implementation
 */
var validaterule = new Rule('ValidateRule'); // must match python class name exactly

// setup
validaterule.setup = function (input, spec) {
  var field = jQuery('#field-' + spec.target);
  var submit = jQuery('input[name=submit]');
  var form = submit.parents('form');

  // reset "alert only once per form submission"
  submit.click(function () {
    if (jQuery(".validated").length) {
      form.removeClass('validated');
      var a = jQuery("a:contains(Modify Ticket)");
      var div = a.parent().parent();
      if (div.hasClass('collapsed'))
        a.click();
    }
  });

  // 'owner' field is special case
  if (spec.target == 'owner' &&
    input.attr('id').indexOf('assign_reassign_owner') != -1)
    field = jQuery(input);

  // proceed only if input field matches the spec's target field
  if (input.attr('id') == field.attr('id')) {

    // listen for form submission
    form.submit(function () {
      if (field.parent('td').hasClass('dynfields-hide'))
        return true;
      if ((spec.value == "" && input.val() == "") ||
        (spec.value != "" && new RegExp(spec.value).test(input.val()))) {
        var valid = false;

        // only invalid when ..?
        if (spec.when.length && jQuery(spec.when).length == 0)
          valid = true;

        // alert only once per form submission
        if (!valid && !form.hasClass('validated')) {
          form.addClass('validated');
          var msg = spec.msg;
          if (!msg.length) {
            var e;
            if (spec.value == '')
              e = 'be empty';
            else
              e = 'equal ' + spec.value;
            msg = spec.target + " must not " + e;
          }
          alert(msg);
          // Allow form to be submitted again.
          form.removeClass('trac-submit-is-disabled');
          field.focus();
        }
        return valid;
      } else {
        return true;
      }
    });
  }
};


/*
 * SetRule implementation
 */
var setrule = new Rule('SetRule'); // must match python class name exactly

// setup
setrule.setup = function (input, spec) {
  if (spec.value == undefined)
    return;

  // ensure trigger field's new value is in spec's list
  // supports list of trigger values
  if (spec.trigger_value.length != 0 &&
      jQuery.inArray(input.val(), spec.trigger_value) == -1)
    return;

  if (spec.trigger_not_value.length != 0 &&
      jQuery.inArray(input.val(), spec.trigger_not_value) > -1)
    return;

  var $field = jQuery(get_selector(spec.target));
  // The workflow can have multiple actions that assign owner. The
  // workaround is to select the first since we haven't defined what the
  // behavior should be.
  if (spec.target == 'owner' && $field.length > 1)
    $field = $field.eq(0)
  if (spec.overwrite.toLowerCase() == 'false' && $field.val() != '')
    return;

  var set_to = spec.set_to;
  if (set_to == 'invalid_value')
    set_to = spec.value; // only use pref if set_to not set in trac.ini

  // only do effect if value is changing (i.e., is a select option)
  var doit = false;
  if ($field.is('select')) {
    $field.find('option').each(function (i, e) {
      var option = jQuery(e).val().toLowerCase();
      if (set_to == '!' && option.length) // special non-empty rule
        set_to = option;
      if (option == set_to) {
        doit = true;
      }
    });
  } else {
    doit = true;
  }
  if (doit) {
    if ($field.is(':checkbox')) {
      $field.prop('checked', set_to);
    } else if ($field.val() != set_to) {
      // Select the workflow action.
      if (spec.target == 'owner' && !jQuery('#field-owner').length)
        $field.siblings('input[type="radio"]').click();
      $field.hide().removeAttr('disabled');
      $field.val(set_to).change();
      $field.fadeIn('slow');
    }
  }
};
