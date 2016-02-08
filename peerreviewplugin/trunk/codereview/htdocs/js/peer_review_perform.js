
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

    function create_comment_link(LineNum, fileID){
       return $('<a>', {href: 'javascript:getComments(' + LineNum + ',' + fileID+ ')',
                        text: LineNum}).prepend($('<img>', {src: tacUrl}));
    };

    $( "#add-comment-dlg" ).dialog({
      title: "Add Comment",
      width: 500,
      autoOpen: false,
      resize: false,
      icons: { primary: "ui-icon-locked"},
    });

    $('#addcomment').on('click', function(event){
       event.preventDefault ? event.preventDefault() : event.returnValue = false;

       var LineNum = $( "#comment-line" ).val();
       $.post("peerReviewCommentCallback", $("#add-comment-form").serialize(), function(data){
          var data = $.parseJSON(data);
          /* Show or refresh comment doalog */
          getComments(data['line'], data['fileid']);
       });

       $( "#add-comment-dlg" ).dialog('close');
       /* Open comment link */
       $('#L'+LineNum).empty();
       $('#L'+LineNum).append(create_comment_link(LineNum, $("#comment-fileid" ).val()));

    });


});
