/*
 * Copyright (C) 2021 OpenGroove,Inc.
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

jQuery(function($) {
    var data = window.tracbacklink;
    if (data === undefined)
        return;

    var content = $('<div>').html(data.content).contents();
    var target;
    var method;
    switch (data.type) {
    case 'ticket':
        target = 'div#ticket';
        method = 'after';
        break;
    case 'wiki':
        target = 'div#content div.wikipage.searchable';
        method = 'after';
        break;
    case 'milestone':
        target = 'div#attachments';
        method = 'before';
        break;
    default:
        return;
    }
    target = $(target);
    if (target.siblings('div#backlinks').length !== 0)
        return;
    target[method](content);
});
