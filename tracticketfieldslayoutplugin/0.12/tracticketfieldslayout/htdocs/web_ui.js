// Copyright (C) 2013,2014 OpenGroove,Inc.
// All rights reserved.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

jQuery(document).ready(function($) {
    setTimeout(function() {
        var onclick = function() {
            var node = $(this);
            node.parent().add(node.closest('tbody')).toggleClass('collapsed');
            return false;
        };
        $('.ticketfieldslayout-foldable')
            .addClass('foldable')
            .removeClass('ticketfieldslayout-foldable')
            .click(onclick);
    }, 1);
});
