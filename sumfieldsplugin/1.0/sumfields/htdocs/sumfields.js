/*
  Copyright (C) 2010-2013 Rob Guttman <guttman@alum.mit.edu>
  All rights reserved.

  This software is licensed as described in the file COPYING, which
  you should have received as part of this distribution.
*/
jQuery(document).ready(function($){
    // loop through each "listing tickets" table
    $('.listing.tickets tbody').each(function(){
        var sums = {};

        // sum each provided field's column
        for (var i=0; i < fields.length; i++) {
            var field = fields[i];
            sums[field] = 0;
            // sum up each row
            $('.' + field, this).each(function () {
                var num = parseFloat($(this).text().replace(',', '.'));
                if (!isNaN(num)) {
                    sums[field] += num;
                }
            });
        }

        // clone the last row in table and replace with the sum(s)
        var lastrow = $(this).find('tr:last');
        var sumrow = lastrow.clone().removeAttr('class');
        var found = false;
        sumrow.find('td').each(function(){
            var field = $(this).attr('class');
            if (field != 'id'){
                // HACK: remove all but the id class to resolve plugin conflicts:
                //  1. have BatchModify plugin find the row to add checkbox (to ensure column alignment)
                //  2. have GridModify not find the rest of the fields
                $(this).removeAttr('class');
            }
            if ($.inArray(field, fields) == -1){
                $(this).text('');
                $(this).children().remove();
            } else {
                $(this).text(sums[field]);
                found = true;
            }
        });
        if (found){
            sumrow.find('td:first').text('sum:');
            lastrow.after(sumrow);
        }
    });
});
