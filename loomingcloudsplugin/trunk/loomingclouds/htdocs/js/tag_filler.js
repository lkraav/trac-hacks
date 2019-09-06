jQuery(function($) {
  var tagnode = $("#field-keywords");
  $("ul.tagcloud a").click(function() {
    var value = tagnode.val();
    var newval = $(this).text();
    var value_as_array = value.trim().split(/[;,\s]+/);
    var index = value_as_array.indexOf(newval);
    if (index > -1) {
      value_as_array.splice(index, 1);
    } else {
      value_as_array.push(newval);
    }
    value = value_as_array.join(' ');
    tagnode.val(value);
    return false;
  });
  $(".tag-cloud-filler").click(function(){
     if ($("ul.tagcloud").css("maxHeight")=="40px") {
       $("ul.tagcloud").css("maxHeight","99999px");
       $(this).html("Less...");
     } else {
       $("ul.tagcloud").css("maxHeight","40px");
       $(this).html("More...");
     }
     return false;
  });
});
