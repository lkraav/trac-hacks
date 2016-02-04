
jQuery(document).ready(function($) {

  function append_img(id){
     var tline = '<img src="chrome/hw/images/thumbtac11x11.gif" />';
     $(id).append(tline);
  };

  for(var i=0; i < peer_comments.length; i++) {
     var id = '#L'+peer_comments[i];
     var tline = '<a href="javascript:getComments('+peer_comments[i]+','+peer_file_id+')">'+peer_comments[i]+'</a>'
     $(id).empty();
     append_img(id);
     $(id).append(tline);
  }
    for(var i=0; i < peer_parent_comments.length; i++) {
       var id = '#P'+peer_parent_comments[i];
       var tline = '<a href="javascript:getComments('+peer_parent_comments[i]+
       ','+peer_parent_file_id+')">'+peer_parent_comments[i]+'</a>'
       $(id).empty();
       append_img(id);
       $(id).append(tline);
    }
});
