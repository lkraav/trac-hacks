/*
 * Copyright (C) 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

(function($) {
	$(function() {
    path = $('#search')[0].action;
    path = path.substring(0, path.length - 7);
    // generates dict as: { <ticketid>: [a, a, ...], <ticketid>: [a, ]}
    const ticketArray =
      Array.prototype.slice.call(document.querySelectorAll('a.ticket'))
      .reduce(function(acc,a){
        const ticketid = parseInt(a.href.substring((path + '/ticket/').length));
        acc[ticketid] ? acc[ticketid].push(a) : acc[ticketid] = [a];
        return acc}, {});
    const idArray = Object.keys(ticketArray).filter(function(n){return n>0});
    $.ajax({
      type: 'POST',
      url: path + '/contextchrome/ticketlink.jsonrpc',
      contentType: 'application/json',
      data: JSON.stringify({
        method: 'ticket.get',
        params: idArray,
      }),
      dataType: "json",
    }).success(function(json) {
      for (ticketid in json) {
        const attrs = json[ticketid].result[3];
        for (key in attrs) {
          ticketArray[ticketid].forEach(function(a){a.classList.add(key + '_is_' + attrs[key])});
        }
      }
    }).fail(function(json) {
      console.error(json);  // FIXME
    })
  })
})(jQuery);
