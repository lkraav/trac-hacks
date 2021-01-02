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
    switch (data.type) {
    case 'ticket':
        $('div#ticket').after(content);
        break;
    case 'wiki':
        $('div#content div.wikipage.searchable').after(content);
        break;
    case 'milestone':
        $('div#attachments').before(content);
        break;
    }
});
