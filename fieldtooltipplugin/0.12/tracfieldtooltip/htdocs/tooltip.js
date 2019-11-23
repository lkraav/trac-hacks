/*
 * Copyright (C) 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

!function($){
  $(function(){
    const locale = '.' + $('html')[0].lang;
    const wikipng = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAAeUlEQVQoU8WQ0Q0AERBER5Ea0AUF0IUGlKQB/wpwGcldlkNyX+dHrHkzu6sAwFrbeK9OCEHJen8QcM4Neu89jDGIMUJCA5BSeqCcM2hSShmgYwKda61NQseEeSYabBNmMWd6AXIGCWitsQR2q2X9p4RPLZ3E9x+3dAHt6W0Nuw2FVgAAAABJRU5ErkJggg==';
    var ajax = null;
    const _wiki_prefix = 'help/';
    const sorry = '<em><sub>(sorry, no hint is presented... click icon above to add)<sub></em>';
    var pages = null;
    var pages_age = 0;
    var pages_etag = 'void'
    var path = $('#search')[0].attributes.action.value;
    path = path.substring(0,path.length - 7);
    $('#ticketbox .properties th[id], #modify th:has(label[for]), #action div:has(label[for])').tooltip({
      items: 'th[id], th:has(label[for]), div:has(label[for])',
      show: { delay: 1500 }, 
      position: { my: "left top", at: "left+30 top+40", collision: "flipfit" },
      hide: { effect: null },
      close: function(event, ui) { // make a tooltip clickable
        ui.tooltip.hover(
          function() {$(this).stop(true).fadeTo(400, 1); },
          function() {$(this).fadeOut("100", function(){ $(this).remove(); })}
        );
      },
      content: function(callback) {
        const field = this.id && this.id.slice(2) || this.querySelector('label').attributes.for.value.replace(/^field-/,'').replace(/^action_/,'');
        // const imglink = `<a href="${path}/wiki/${_wiki_prefix}${field}"><img align="right" src="${path}/chrome/common/wiki.png"></img></a>`;
        const imglink = '<a href="'+path+'/wiki/'+_wiki_prefix+field+'"><img align="right" src="'+wikipng+'"></img></a>';

        const get_content = function(field) {
          return imglink+'<strong>'+field+'</strong>:<p>'+(pages[field+locale] || pages[field] || defaults[field+locale] || defaults[field] || sorry)
        }
        //  if not expired, use the page cache
        if(pages_age > Date.now() - 10e3)
          return get_content(field);
        else {
          // else, retrieve it
          _ajax = ajax;  // copy ajax singleton to local to avoid timing issue
          // if some ajax request in progress exists, add a resolver without new request to the ajax
          if(_ajax && _ajax.readystate != 4) {
            _ajax.done(function(){callback(get_content(field))});
          } else {
            // if no ajax request in progress, create new request
            ajax = $.ajax({
              type: 'POST',
              url: path + '/tracfieldtooltip/tooltip.jsonrpc',
              contentType: 'application/json',
              headers: {
                'If-None-Match': pages_etag,
              },
              data: JSON.stringify({
                method: 'wiki.getPage',
              }),
              dataType: "json",
            }).done(function(json, status_text, jqXHR) {
              // when 304, json also we can use jqXHR.responseJSON from browser cache
              pages = json && json['pages'] || pages
              defaults = json && json['defaults'] || defaults
              pages_age = Date.now()
              pages_etag = jqXHR.getResponseHeader('etag') || pages_etag  // if no etag header presented, use old one
              callback(get_content(field));
            })
            .fail(console.error)  // FIXME
            .always(function() {ajax = null})  // if all done, dispose the ajax singleton
          }
        }
        // during ajax, will show a spinner
        return imglink+field+':<p><i>Loading...</i></p>';
      },
    });
  })
}(jQuery)
