/*
 * Copyright (C) 2021 Jun Omae <jun66j5@gmail.com>
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

jQuery(function($) {
    var data = window.ticketlog;
    if (data === undefined)
        return;
    var target = $('div#ticket');
    if (target.siblings('#ticket_log').length !== 0)
        return;
    var content = $('<div>').html(data.content).contents();
    target.after(content);
});
