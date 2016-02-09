
jQuery(document).ready(function($) {

    function create_comment_link(LineNum, fileID){
        return $('<a>', {href: 'javascript:getComments(' + LineNum + ',' + fileID+ ')',
                         text: LineNum}).prepend($('<img>', {src: tacUrl}));
    };

    function add_get_comments_link(prefix, line, fileid){
        $(prefix+line).empty();
        $(prefix+line).append(create_comment_link(line, fileid));
    }

   for(var i=0; i < peer_comments.length; i++) {
       add_get_comments_link('#L', peer_comments[i], peer_file_id)
   }

   for(var i=0; i < peer_parent_comments.length; i++) {
       add_get_comments_link('#P', peer_parent_comments[i], peer_parent_file_id)
   }

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
       /* Add open comment link */
       add_get_comments_link('#L', LineNum, $("#comment-fileid" ).val())
    });
});
