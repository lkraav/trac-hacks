// Copyright (C) 2017 OpenGroove,Inc.
// All rights reserved.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

if (window.ticketfieldslayout) {
    jQuery(document).ready(function($) {
        var data = window.ticketfieldslayout;
        var fields = data.fields;
        var groups = data.groups;
        var properties = window.properties;

        $('#filters .actions select').each(function() {
            if (!/^add_(?:filter|clause)_/.test(this.name))
                return;
            var select = this;
            var options = $.makeArray(this.options);
            var new_options = [options[0]];
            options[0] = undefined;

            var collect_options = function(fields, new_options) {
                if (new_options === undefined)
                    new_options = [];
                $.each(fields, function(idx, field) {
                    if (field in properties) {
                        $.each(options, function(idx, opt) {
                            if (opt !== undefined && opt.value === field) {
                                new_options.push(opt);
                                options[idx] = undefined;
                                return false;
                            }
                        });
                    }
                });
                return new_options;
            };

            $.each(fields, function(idx, field) {
                if (field in properties) {
                    $.each(options, function(idx, opt) {
                        if (opt !== undefined && opt.value === field) {
                            new_options.push(opt);
                            options[idx] = undefined;
                            return false;
                        }
                    });
                }
                else if (/^@/.test(field)) {
                    var key = field.substring(1);
                    var group = groups[key];
                    var item = {label: group.label,
                                options: collect_options(group.fields)};
                    new_options.push(item);
                }
            });
            $.each(options, function(idx, opt) {
                if (opt !== undefined)
                    new_options.push(opt);
            });
            $.each(new_options, function(idx, item) {
                if ($.isPlainObject(item)) {
                    var optgroup = $('<optgroup>').attr('label', item.label);
                    optgroup.append(item.options);
                    item = optgroup[0];
                }
                select.appendChild(item);
            });
        });
    });
}
