// Copyright (C) 2013-2023 OpenGroove,Inc.
// All rights reserved.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

jQuery(document).ready(function($) {
    var listener = function() {
        console.log('------');
        var node = $(this);
        var fieldset = node.closest('fieldset');
        fieldset.toggleClass('collapsed');
        fieldset.closest('tbody').toggleClass('ticketfieldslayout-collapsed');
        return false;
    };
    $('#content').on('click', '.ticketfieldslayout-toggle .foldable', listener);
});
