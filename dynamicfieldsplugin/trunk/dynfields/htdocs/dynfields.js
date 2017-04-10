jQuery(document).ready(function ($) {

  window.get_selector = function (field_name) {
    var selector = '#field-' + field_name;
    if (field_name == 'owner' && $(selector).length != 1) {
      selector = '[id$="_reassign_owner"]'
    } else if (field_name == 'resolution' && $(selector).length != 1) {
      selector = '#action_resolve_resolve_resolution';
    }
    return selector;
  };

  window.apply_rules = function () {
    var input = $(this);
    setup_triggers();

    // execute the rule lifecycle...

    // setup each rule
    $.each(triggers, function (trigger, specs) {
      $.each(specs, function (i, spec) {
        spec.rule.setup(input, spec);
      });
    });

    // apply each rule
    $.each(triggers, function (trigger, specs) {
      $.each(specs, function (i, spec) {
        spec.rule.apply(input, spec);
      });
    });

    // complete each rule
    $.each(triggers, function (trigger, specs) {
      $.each(specs, function (i, spec) {
        spec.rule.complete(input, spec);
      });
    });
  };

  window.setup_triggers = function () {
    if (window.dynfields_rules == undefined)
      window.dynfields_rules = {};

    for (var prop in triggers) {
      triggers[prop].selector = get_selector(prop);
      triggers[prop].forEach(function (spec) {
        spec.rule = window.dynfields_rules[spec.rule_name];
      });
    }
  };

  setup_triggers(); // trigger fields

  if (window.location.pathname.match(/\/query$/)) {
    // hide all "hide_always" fields
    $.each(triggers, function (trigger, specs) {
      $.each(specs, function (i, spec) {
        spec.rule.query(spec);
      });
    });
  } else {
    var inputs = [];

    // collect all input fields that trigger rules
    $.each(triggers, function (trigger, specs) {
      var input = $(specs.selector).get();
      inputs.push(input);
    });
    inputs = $.unique(inputs);

    // attach change event to each input and trigger first change
    $.each(inputs, function (obj) {
      $(this).change(apply_rules).change();
    });

  }
});
