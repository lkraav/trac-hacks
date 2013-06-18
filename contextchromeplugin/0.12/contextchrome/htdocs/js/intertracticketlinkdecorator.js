// FIXME: IE8,9 bug, refs; http://dev.classmethod.jp/cloud/cors-cross-origin-resource-sharing-cross-domain/

(function($) {
  var XMLRPC = true;
  $(function($) {
    var fields = config__ticket__decolate_fields;
    $('a[class*="ext-link"][href*="/intertrac/"]')
      .each(function() {
        var that = $(this);
        // with XMLRPC on target 
        var url = that.attr("href").replace(/%3A/g,':').replace(/%23/g,'ticket:');
        var ticket = /ticket:([0-9]+)/.exec(url);
        if(!ticket) return;
        url = url.replace(/\/intertrac\/.+/,"/jsonrpc");
        $.ajax({
          type: 'POST',
          url: url,
          contentType: 'application/json',
          data: JSON.stringify({
            method:'ticket.get',
            params:[ticket[1]]
          }),
          dataType: "json"
        }).success(function(json) {
          if(json.error) {
            if (json.error.code == 404) that.addClass('missing');
          } else {
            var attr = json.result[3];
            var status = attr['status'];
            that.addClass(status);
            if(status == 'closed') status += ': ' + attr['resolution'];
            that.attr('title', that.attr('title') + ":\n" + attr['type'] + ': ' + attr['summary'] + ' (' + status + ')');
            for (i in fields) {
              that.addClass(fields[i] + '_is_' + attr[fields[i]]);
            }
          }
        }).fail(function(data){
          // without XMLRPC on target
          $.ajax({
            url: that.attr("href")
          }).success(function(data) {
            data = $(data);
            var status = data.find(".trac-status a")[0];
            if(status) that.addClass(status.innerText);
            var title = data.find("#trac-ticket-title span")[0];
            if(title) that.attr('title', that.attr('title') + ':\n' + title.innerText + ' (' + status.innerText + ')');
            for (i in fields) {
              var xpath = ((fields[i]=='type')
                        ? ".trac-"+fields[i]+" a"
                        : "td[headers=h_"+fields[i]+"] a");
              var val = data.find(xpath)[0];
              if(val) that.addClass(fields[i] +"_is_" + val.innerText);
            }
          });
        });
      });
  });
})(jQuery);