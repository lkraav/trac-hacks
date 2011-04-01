/*
 * Rule 'class'
 */
var Rule = function(name){
    var noop = function(input, spec){};
    this.setup    = noop;
    this.apply    = noop;
    this.complete = noop;
    this.query    = function(spec){}; // for query page
    
    // register this rule by adding to global variable
    if (window.dynfields_rules == undefined)
        window.dynfields_rules = new Object();
    window.dynfields_rules[name] = this;
}


/*
 * ClearRule implementation
 */
var clearrule = new Rule('ClearRule'); // must match python class name exactly

// apply
clearrule.apply = function(input, spec){
    var target = spec.target;

    if (spec.clear_on_change == undefined)
        return;
    
    var fld = jQuery('#field-'+target);
    if (fld.hasClass('clearable')){
        fld.val('').change();
    } else {
        fld.addClass('clearable');
    }
};


/*
 * CopyRule implementation
 */
var copyrule = new Rule('CopyRule'); // must match python class name exactly

// apply
copyrule.apply = function(input, spec){
    var target = spec.target;

    if (spec.value == undefined)
        return;
        
    var fld = jQuery('#field-'+target);
    if (spec.overwrite.toLowerCase() == 'false'){
        if (fld.val() != '' || fld.is(":hidden"))
            return;
    }
    
    if (fld.hasClass('copyable')){
        // only do effect if value is changing
        var doit = true;
        if (fld.get(0).tagName.toLowerCase() == 'select'){
            var opts = new Array();
            fld.find('option').each(function(i,e){
                opts.push(jQuery(e).text());
            });
            if (jQuery.inArray(input.val(), opts) == -1){
                doit = false;
            }
        } 
        if (doit){
            fld.hide();
            fld.val(input.val()).change();
            fld.fadeIn('slow');
        }
    } else {
        fld.addClass('copyable');
    }
};


/*
 * DefaultValueRule implementation
 */
var defaultrule = new Rule('DefaultValueRule'); // must match python class name exactly

// apply
defaultrule.apply = function(input, spec){
    var fld = jQuery('#field-'+spec.target);
    if (!fld.hasClass('defaulted')){
        fld.addClass('defaulted');
        var doit = true;
        var value = spec.value;
        
        // ensure default value is in list of select options
        if (fld.get(0).tagName.toLowerCase() == 'select'){
            var opts = new Array();
            fld.find('option').each(function(i,e){
                opts.push(jQuery(e).text());
            });
            if (jQuery.inArray(value, opts) == -1)
                doit = false;
        }
            
        // ensure an 'empty' option value for existing tickets (unless appending)
        if (fld.val().length > 1 &&
           window.location.pathname.indexOf('/ticket') > -1){
            doit = spec.append.toLowerCase() == 'true';
            if (doit){
                // append preference to text field's value
                var values = new Array();
                jQuery(fld.val().split(',')).each(function(i,v){
                    values.push(jQuery.trim(v));
                });
                // the preference value could be comma-delimited list itself
                jQuery(value.split(',')).each(function(i,v){
                    v = jQuery.trim(v);
                    if (jQuery.inArray(v, values) == -1){
                        values.push(v);
                    }
                });
                value = values.join(', ');
            }
        }
        
        if (doit)
            fld.val(value).change(); // cascade rules
    }
};


/*
 * HideRule implementation
 */
var hiderule = new Rule('HideRule'); // must match python class name exactly

// setup
hiderule.setup = function(input, spec){
    var id = input.attr('id');
    if (id){ // no input fields when on /query page
        // show and reset elements controlled by this input field
        var trigger = id.substring(6); // ids start with 'field-'
        jQuery('.dynfields-'+trigger)
            .removeClass('dynfields-hide dynfields-'+trigger)
            .show();
    }
};

// apply
hiderule.apply = function(input, spec){
    var trigger = spec.trigger;
    var target = spec.target;
    
    // process hide rule
    var v = input.val();
    var l = spec.trigger_value.split('|'); // supports list of trigger values
    if ((jQuery.inArray(v,l) != -1 && spec.op == 'hide') ||
        (jQuery.inArray(v,l) == -1 && spec.op == 'show')){
        
        // we want to hide the input fields's td and related th
        var field = jQuery('#field-'+target);
        var td = field.parents('td:first');
        var th = td.siblings('th')
                   .find('label[for=field-'+target+']')
                   .parents('th:first');
        var cls = 'dynfields-hide dynfields-'+trigger;
        if (spec.link_to_show.toLowerCase() == 'true')
            cls += ' dynfields-link';
        td.addClass(cls);
        th.addClass(cls);
        
        // let's also clear out the field's value to avoid confusion
        if (spec.clear_on_hide.toLowerCase() == 'true' &&
            field.val() && field.val().length) // Chrome fix - see #8654
            field.val('').change(); // cascade rules
            
        // hide field in the header if cleared or always hidden
        if (spec.clear_on_hide.toLowerCase() == 'true' ||
            spec.hide_always.toLowerCase() == 'true'){
            th = jQuery('#h_'+target);
            td = th.siblings('td[headers=h_'+target+']');
            td.addClass('dynfields-hide dynfields-'+trigger);
            th.addClass('dynfields-hide dynfields-'+trigger);
        }
    }        
};

// complete
hiderule.complete = function(input, spec){
    jQuery('.dynfields-hide').hide();
    
    // update layout (see layout.js)
    inputs_layout.update(spec);
    header_layout.update(spec);
    
    // add link to show hidden fields (that are enabled to be shown)
    if (spec.link_to_show.toLowerCase() == 'true'){
        if (jQuery('#dynfields-show-link').length == 0){
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
hiderule.query = function(spec){
    // hide hide_always fields on /query page
    if (spec.hide_always.toLowerCase() == 'true'){
        // hide from columns section
        jQuery('input[value="'+spec.target+'"]')
              .attr('checked',false)
              .parent().hide();
        // hide from column filter/dropdown
        jQuery('#add_filter option[value="'+spec.target+'"]')
              .hide();
    }
};
