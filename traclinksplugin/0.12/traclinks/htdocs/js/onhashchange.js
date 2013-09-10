/*
 * Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 * 
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

$(document).ready(function() {
  jQuery(window).hashchange(function(event) {
    traclinks = $("#proj-search").attr('value');
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
      pagename = pagename.slice(pagename.search(start) + start.length + 1, -hash.length)
      // take care for WikiStart as start page ... pagename == "" in some case
      traclinks = 'wiki:' + pagename + location.hash
      $("#proj-search").attr('value', traclinks);
    }
    if (($('#main #content.browser').length == 1) ||  // browser
        ($('#main #content.changeset').length == 1) ) {  // changeset
      // TODO: rewrite this ad-hoc code
      if ((i = traclinks.indexOf('#')) >= 0) traclinks = traclinks.slice(0, i)
      traclinks = traclinks + '#' + location.hash.slice(1)
      $("#proj-search").attr('value', traclinks);
    }
  });
  if (location.hash.length > 0) // invoke it if necessary after load
  jQuery(window).hashchange();
});
