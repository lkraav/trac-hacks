
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
    if(LineNum != $("#comment-line-view").val()){
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
                           });
}

function addComment(LineNum, fileID, parentID)
{
    $("#comment-line").val(LineNum);
    $("#comment-parentid").val(parentID);
    $("#comment-fileid").val(fileID);
    $("#comment-txt").val("");
    $('#add-comment-dlg').dialog({title: "Add Comment for Line "+LineNum});
    $('#add-comment-dlg').dialog('open');
}

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
      resizable: false,
   });

   $( "#view-comment-dlg" ).dialog({
      title: "View Comments",
      width: 440,
      autoOpen: false,
      resizable: false,
   });

    $('#addcomment').on('click', add_comment_button);
    $('#addcomment-view').on('click', function(){
            addComment($("#comment-line-view").val(), $("#comment-fileid-view").val(), -1);
    });

     /*addComment($("#comment-line-view").val(),
                                                 $("#comment-fileid-view").val(),
                                                 -1));
*/
});
