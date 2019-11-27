// Copyright (C) 2014 Jun Omae
// All rights reserved.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

(function(window, document) {
    jQuery(document).ready(function($) {
        $('#content .usernamedecorate[title]').tipsy();
    });
    var settings = window.tracusernamedecorate;
    if (settings !== undefined && settings.gravatar_icon_size !== undefined) {
        var size = settings.gravatar_icon_size;
        var text =
            ".usernamedecorate-gravatar { padding-left: %(padding)dpx }\n" +
            ".usernamedecorate-gravatar > img { width: %(size)dpx; height: %(size)dpx }\n";
        text = text.replace(/%\(\w+\)d/g, function(match) {
            switch (match) {
                case '%(padding)d': return '' + (size + 1);
                case '%(size)d': return '' + size;
            }
        });
        var style = $('<style />').attr('type', 'text/css').text(text);
        style.appendTo('head');
    }
})(window, document);
