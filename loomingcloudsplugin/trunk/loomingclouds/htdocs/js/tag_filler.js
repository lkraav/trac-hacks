jQuery(function($) {
  /*  Transformation functions Copyright (C) 2021 Cinc */
  function apply_transform(filter_list){
      var i;
      for(i = 0; i < filter_list.length; i++){
        var html = filter_list[i];
        switch(html['pos']){
          case 'after':
            $(html['css']).after(html['html']);
            break;
          case 'append':
            $(html['css']).append(html['html']);
            break;
          case 'before':
            $(html['css']).before(html['html']);
            break;
          case 'prepend':
            $(html['css']).prepend(html['html']);
            break;
          case 'remove':
            $(html['css']).remove();
            break;
          case 'replace':
            $(html['css']).replaceWith(html['html']);
            break;
          default:
            break;
        };
      } // for
  };

  if(typeof loomingclouds_filter !== 'undefined'){
      apply_transform(loomingclouds_filter);
  };

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
