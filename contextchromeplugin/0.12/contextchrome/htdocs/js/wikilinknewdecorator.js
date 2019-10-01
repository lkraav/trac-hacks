/*
 * Copyright (C) 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

(function($) {
	$(function() {
    path = $('#search')[0].attributes['action'].value
    path = path.substring(0, path.length - 7);
    // generates dict as: { <wikiname>: [a, a, ...], <wikiname>: [a, ]}
    const wikiname_anchors =
      Array.prototype.slice.call(document.querySelectorAll('a.wiki'))
      .filter(a=>!a.classList.contains('missing'))
      .reduce((acc,a) => {
        const wikiname = a.pathname.substring((path + '/wiki/').length);
        acc[wikiname] ? acc[wikiname].push(a) : acc[wikiname] = [a];
        return acc}, {});
    const wikinames = Object.keys(wikiname_anchors);
    $.ajax({
      type: 'POST',
      url: path + '/contextchrome/wikilinknew.jsonrpc',
      contentType: 'application/json',
      data: JSON.stringify({
        method: 'wiki.getPageInfo',
        params: wikinames,
      }),
      dataType: "json",
    }).success(function(json) {
      for (wikiname in json) {
        const isNew = json[wikiname].result[2] < config__wiki__wiki_new_info_second;
        wikiname_anchors[wikiname].forEach(function(a){
          if(isNew) a.classList.add('new');
          a.classList.add('age_is_' + json[wikiname].result[2]);
        });
      }
    }).fail(function(json) {
      console.error(json);  // FIXME
    })
  })
})(jQuery);
