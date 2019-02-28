function formatItem(row) {
  var firstLine = (row[2]) ? row[0] + " (" + row[2] + ")" : row[0];
  return $.htmlFormat('<div class="name">$1</div>', firstLine) +
    (row[1] ? $.htmlFormat('<div class="mail">$1</div>', row[1]) : '');
}

(function($){
  if($.isFunction($.htmlFormat)) return;

  // if $.htmlFormat is not defined,
  // use backported functions from trac.js for Trac-0.11 compatibility.

  // Escape special HTML characters (&<>")
  var quote = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"};

  $.htmlEscape = function(value) {
    if (typeof value != "string")
      return value;
    return value.replace(/[&<>"]/g, function(c) { return quote[c]; });
  }

  function format(str, args, escape) {
    var kwargs = args[args.length - 1];
    return str.replace(/\${?(\w+)}?/g, function(_, k) {
      var result;
      if (k.length == 1 && k >= '0' && k <= '9')
        result = args[k - '0'];
      else
        result = kwargs[k];
      return escape ? escape(result) : result;
    });
  }

  $.htmlFormat = function(str) {
    return format(str, arguments, $.htmlEscape);
  }
})(jQuery);
