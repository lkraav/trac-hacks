/*
 * Copyright (C) 2013, 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 * 
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

$(document).ready(function() {
  jQuery(window).on('load hashchange', function(event) {
    $("#proj-search").attr('value', decodeURIComponent(traclinks)).attr('size', 80)
    if ($('#main #ticket').length == 1) { // ticket
      path_elements = document.location.pathname.split('/');
      ticketid = path_elements[path_elements.length - 1];
      if (ticketid != "newticket") {
        if (location.search == "" && location.hash.indexOf('#comment:') == 0) { // comment of ticket
          traclinks = location.hash.slice(1) + ':ticket:' + ticketid;
        } else {
          traclinks = 'ticket:' + ticketid + location.search + location.hash;
        }
        $("#proj-search").attr('value', traclinks);
      }
    }
    if ($('#main #wikipage').length == 1) { // wiki
      start = $('link[rel="start"]')[0].href
      hash = document.location.hash
      pagename = document.location.href
      pagename = pagename.slice(pagename.search(start) + start.length + 1)
      if(hash)
        pagename = pagename.slice(0, -hash.length)
      // take care for WikiStart as start page ... pagename == "" in some case
      traclinks = 'wiki:' + pagename + location.hash
      $("#proj-search").attr('value', decodeURIComponent(traclinks));
    }
    if (($('#main #content.browser').length == 1) ||  // browser
        ($('#main #content.changeset').length == 1) ) {  // changeset
      traclinks = traclinks.split('#')[0] + location.hash
      $("#proj-search").attr('value', traclinks);
    }
  });
});
