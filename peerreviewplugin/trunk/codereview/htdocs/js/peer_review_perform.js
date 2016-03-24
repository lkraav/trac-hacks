
function collapseComments(parentID)
{
   console.log('collapse');
    $('table[data-child-of='+parentID+']').hide();
    $('#'+parentID+'collapse').hide();
    $('#'+parentID+'expand').show();
};

function expandComments(parentID)
{
   console.log('expand');
    $('table[data-child-of='+parentID+']').show();
    $('#'+parentID+'collapse').show();
    $('#'+parentID+'expand').hide();
};

function getComments(LineNum, fileID)
{
    if(LineNum != $("#comment-line-view").val() || fileID != $("#comment-fileid-view").val()){
        $('#view-comment-dlg').dialog('close');
    };
    $("#comment-line-view").val(LineNum);
    $("#comment-fileid-view").val(fileID);
    $('#view-comment-dlg').dialog({title: "Comments for Line "+LineNum});
    $('#comment-tree').empty();
    $('#view-comment-dlg').dialog('open');
    $('#comment-loading').show();
    var url = baseUrl + '?actionType=getCommentTree&IDFile=' + fileID + '&LineNum=' + LineNum
    $('#comment-tree').load(url, function(){
                           $('#comment-loading').hide();
                           $('#comment-refresh').attr('href', 'javascript:getComments('+LineNum+', '+fileID +')')
                           $('#addcomment-view').on('click', function(){
                                   addComment($("#comment-line-view").val(), $("#comment-fileid-view").val(), -1);
                           });
                           });
}

function addComment(LineNum, fileID, parentID)
{
    $("#comment-line").val(LineNum);
    $("#comment-parentid").val(parentID);
    $("#comment-fileid").val(fileID);
    $("#comment-txt").val("");
    $("#commentchange").hide();
    $('#add-comment-dlg').dialog({title: "Add Comment for Line "+LineNum});
    $('#add-comment-dlg').dialog('open');
    $('#add-comment-dlg').dialog('moveToTop');
}

function markCommentRead(line, file_id, comment_id){

    $.post("peerReviewCommentCallback",
           {'fileid': file_id, 'line': line, 'commentid': comment_id, 'markread': 'read',
            'reviewid': peer_review_id,
            '__FORM_TOKEN': form_token
           },
            function(data){
              var data = $.parseJSON(data);
              /* Show or refresh comment doalog */
              getComments(data['line'], data['fileid']);
           });
};

function markCommentNotread(line, file_id, comment_id){

    $.post("peerReviewCommentCallback",
           {'fileid': file_id, 'line': line, 'commentid': comment_id, 'markread': 'notread',
            'reviewid': peer_review_id,
            '__FORM_TOKEN': form_token
           },
            function(data){
              var data = $.parseJSON(data);
              /* Show or refresh comment doalog */
              getComments(data['line'], data['fileid']);
           });
};

jQuery(document).ready(function($) {

    function create_comment_link(LineNum, fileID){
        return $('<a>', {href: 'javascript:getComments(' + LineNum + ',' + fileID+ ')',
                         text: LineNum}).prepend($('<img>', {src: tacUrl}));
    };

    function add_get_comments_link(prefix, line, fileid){
        $(prefix+line).empty();
        $(prefix+line).append(create_comment_link(line, fileid));
    }

    function add_comment_button(event){
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
      resizable: true,
      dialogClass: 'top-dialog',
   });

   $( "#view-comment-dlg" ).dialog({
      title: "View Comments",
      width: 440,
      autoOpen: false,
      resizable: false,
   });

    $('#addcomment').on('click', add_comment_button);

    /* auto preview */
    var args = {realm: "peerreview", escape_newlines: 1};
    $("#comment-txt").autoPreview("preview_render", args, function(textarea, text, rendered) {
        $("#commentchange div.comment").html(rendered);
        if (rendered)
          $("#commentchange").show();
        else if ($("#commentchange ul.changes").length == 0)
          $("#commentchange").hide();
    });
});
