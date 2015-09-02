var get_selector = function(field_name){
    var selector = '#field-'+field_name;
    if (field_name == 'owner'){
        if (jQuery(selector).length != 1){
            if (jQuery('#action_assign_reassign_owner').length){
                selector = '#action_assign_reassign_owner';
            } else {
                selector = '#action_reassign_reassign_owner';
            }
        }
    } else if (field_name == 'resolution'){
        if (jQuery(selector).length != 1){
            selector = '#action_resolve_resolve_resolution';
        }
    }
    return selector;
};

var setup_triggers = function(){
    if (window.dynfields_rules == undefined)
        window.dynfields_rules = {};

    for (var prop in triggers) {
        triggers[prop].selector = get_selector(prop);
        for (var i in triggers[prop]) {
            var spec = triggers[prop][i];
            spec.rule = window.dynfields_rules[spec.rule_name];
        }
    }
};

var apply_rules = function(){
    var input = $(this);
    setup_triggers();

    // execute the rule lifecycle...

    // setup each rule
    jQuery.each(triggers, function(trigger,specs){
        jQuery.each(specs, function(i,spec){
            spec.rule.setup(input, spec);
        });
    });

    // apply each rule
    jQuery.each(triggers, function(trigger,specs){
        jQuery.each(specs, function(i,spec){
            if (input.attr('id') != specs.selector.slice(1))
                return;
            spec.rule.apply(input, spec);
        });
    });

    // complete each rule
    jQuery.each(triggers, function(trigger,specs){
        jQuery.each(specs, function(i,spec){
            if (input.attr('id') != specs.selector.slice(1))
                return;
            spec.rule.complete(input, spec);
        });
    });
};

jQuery(document).ready(function($){

    setup_triggers(); // trigger fields

    if (window.location.pathname.match(/\/query$/)){
        // hide all "hide_always" fields
        jQuery.each(triggers, function(trigger,specs){
            jQuery.each(specs, function(i,spec){
                spec.rule.query(spec);
            });
        });
    } else {
        var inputs = [];

        // collect all input fields that trigger rules
        jQuery.each(triggers, function(trigger,specs){
            var input = jQuery(specs.selector).get(0);
            inputs.push(input);
        });
        inputs = jQuery.unique(inputs);

        // attach change event to each input and trigger first change
        jQuery.each(inputs, function(obj){
            $(this).change(apply_rules).change();
        });

    }
});
