
function collapseComments(parentID)
{
    $('table[data-child-of='+parentID+']').hide();
    $('#'+parentID+'collapse').hide();
    $('#'+parentID+'expand').show();
};

function expandComments(parentID)
{
    $('table[data-child-of='+parentID+']').show();
    $('#'+parentID+'collapse').show();
    $('#'+parentID+'expand').hide();
};

function createCommentDiv(type_char, LineNum){
  var comment = '<div class="peer-comment">'
  comment += '<p class="refresh"><a id="comment-refresh-'+type_char+LineNum+'" href="">Refresh</a></p>'
  comment += '<p id="comment-loading-'+type_char+LineNum+'">Loading...</p>'
  if(type_char === 'P'){
    comment += '<div id="PL'+LineNum+'"></div></div>'
  }
  else{
    comment += '<div id="CL'+LineNum+'"></div></div>'
  };
  return comment
};

function getInlineCommentMarkup(LineNum, diff_view, parent_comment){
  var markup = '<th></th>'
  if(parent_comment){
      /* Parent comment implies diff view */
      if(peer_diff_style === 'inline'){
          markup += '<th></th><td id="PTD'+LineNum+'">'+createCommentDiv('P', LineNum)+'</td><td id="CTD'+LineNum+'"></td>'
      }
      else{
          markup += '<td id="PTD'+LineNum+'">'+createCommentDiv('P', LineNum)+'</td><th></th><td id="CTD'+LineNum+'"></td>'
      }
  }
  else{
      comment = createCommentDiv('C', LineNum)
      if(diff_view){
          if(peer_diff_style === 'inline'){
              markup += '<th></th><td id="PTD'+LineNum+'"></td><td id="CTD'+LineNum+'">'+comment+'</td>'
          }
          else{
              markup += '<td id="PTD'+LineNum+'"></td><th></th><td id="CTD'+LineNum+'">'+comment+'</td>'
          };
      }
      else{
          markup += '<td id="CTD'+LineNum+'" class="peer-comment-td">'+comment+'</td>';
      };
  }
  return $('<tr>',
           {id: "CTR"+LineNum, class: "comment-tr"}
           ).append(markup);
};

function default_for(arg, val){
    return typeof arg !== 'undefined' ? arg : val;
};

function getCommentsInline(LineNum, fileID, refresh)
{
    refresh = default_for(refresh, false);
    if($('#CTD'+LineNum).children().length > 0){
        $('#CTD'+LineNum).empty();
        if(!refresh){
           console.log($('#PTD'+LineNum).children().length);
           if($('#PTD'+LineNum).children().length === 0){
               $('#CTR'+LineNum).remove();
           };
           return;
        };
    };

    $('#comment-loading-C'+LineNum).show();
    var diff_view = false;
    if(peer_parent_file_id !== 0){
        diff_view = true;
    };
    if($('#CTD'+LineNum).length === 0 ){
       $('#L'+LineNum).parent().after(getInlineCommentMarkup(LineNum, diff_view, false));
    }
    else{
        $('#CTD'+LineNum).append(createCommentDiv('C', LineNum));
    }
    var url = baseUrl + '?actionType=getCommentTree&IDFile=' + fileID + '&LineNum=' + LineNum
    $('#CL'+LineNum).load(url, function(){
                           $('#comment-loading-C'+LineNum).hide();
                           $("#comment-line-view"+LineNum).val(LineNum);
                           $("#comment-fileid-view"+LineNum).val(fileID);
                           $('#comment-refresh-C'+LineNum).attr('href', 'javascript:getComments('+LineNum+', '+fileID +', true)')
                           $('#addcomment-view'+LineNum).on('click', function(){
                                   addComment($("#comment-line-view"+LineNum).val(), $("#comment-fileid-view"+LineNum).val(), -1);
                           });
                           });
};

function getParentCommentsInline(LineNum, fileID, refresh)
{
    refresh = default_for(refresh, false);

    if($('#PTD'+LineNum).children().length > 0){
        $('#PTD'+LineNum).empty();
        if(!refresh){
           if($('#CTD'+LineNum).children().length === 0){
               $('#CTR'+LineNum).remove();
           };
           return;
        };
    };
    $('#comment-loading-P'+LineNum).show();
    var diff_view = true;

    if($('#PTD'+LineNum).length === 0 ){
        $('#P'+LineNum).parent().after(getInlineCommentMarkup(LineNum, diff_view, true));
    }
    else{
        $('#PTD'+LineNum).append(createCommentDiv('P', LineNum));
    }
    var url = baseUrl + '?actionType=getCommentTree&IDFile=' + fileID + '&LineNum=' + LineNum
    $('#PL'+LineNum).load(url, function(){
                           $('#comment-loading-P'+LineNum).hide();
                           $("#comment-line-view"+LineNum).val(LineNum);
                           $("#comment-fileid-view"+LineNum).val(fileID);
                           $('#comment-refresh-P'+LineNum).attr('href', 'javascript:getParentComments('+LineNum+', '+fileID +', true)')
                           $('#addcomment-view'+LineNum).on('click', function(){
                                   addComment($("#comment-line-view"+LineNum).val(), $("#comment-fileid-view"+LineNum).val(), -1);
                           });
                           });
};

function getCommentsPopup(LineNum, fileID)
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
                           $('#addcomment-view'+LineNum).on('click', function(){
                                   addComment($("#comment-line-view").val(), $("#comment-fileid-view").val(), -1);
                           });
                           });
}

function getComments(LineNum, fileID, refresh)
{
   refresh = default_for(refresh, false);

   if($('#inline-comments').is(':checked')){
       getCommentsInline(LineNum, fileID, refresh)
   }else{
       getCommentsPopup(LineNum, fileID)
   };
};

function getParentComments(LineNum, fileID, refresh)
{
   refresh = default_for(refresh, false);

   if($('#inline-comments').is(':checked')){
       getParentCommentsInline(LineNum, fileID, refresh)
   }else{
       getCommentsPopup(LineNum, fileID)
   };
};

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

function markComment(line, file_id, comment_id, read_status, review_id){
    $.post("peerReviewCommentCallback",
           {'fileid': file_id, 'line': line, 'commentid': comment_id, 'markread': read_status,
            'reviewid': review_id,
            '__FORM_TOKEN': form_token
           },
            function(data){
              var data = $.parseJSON(data);
              /* Show or refresh comment dialog */
              getComments(data['line'], data['fileid'], true);
           });
};

function markCommentRead(line, file_id, comment_id, review_id){
    markComment(line, file_id, comment_id, 'read', review_id);
};

function markCommentNotread(line, file_id, comment_id, review_id){
    markComment(line, file_id, comment_id, 'notread', review_id);
};

jQuery(document).ready(function($) {

    function create_comment_link(LineNum, fileID, is_parent){
        if(is_parent){
            var js_href = 'javascript:getParentComments(' + LineNum + ',' + fileID+ ')'
        }
        else{
            var js_href = 'javascript:getComments(' + LineNum + ',' + fileID+ ')'
        };
        return $('<a>', {href: js_href,
                         text: LineNum}).prepend($('<img>', {src: tacUrl}));
    };

    function add_get_comments_link(prefix, line, fileid, is_parent){
        $(prefix+line).empty();
        $(prefix+line).append(create_comment_link(line, fileid, is_parent));
    }

    function add_comment_button(event){
       event.preventDefault ? event.preventDefault() : event.returnValue = false;

       var LineNum = $( "#comment-line" ).val();
       $.post("peerReviewCommentCallback", $("#add-comment-form").serialize(), function(data){
          var data = $.parseJSON(data);
          /* Show or refresh comment dialog */
          getComments(data['line'], data['fileid'], true);
       });

       $( "#add-comment-dlg" ).dialog('close');
       /* Add open comment link. This can't be a parent. */
       add_get_comments_link('#L', LineNum, $("#comment-fileid" ).val(), false);
    }

    function inline_comment_cbox(){
         if($('#inline-comments').is(':checked')){
             $('#view-comment-dlg').dialog('close');

             if(peer_parent_file_id !== 0){
                 /* This is a diff view. */
                 if(peer_diff_style === 'inline'){
                     $('table.trac-diff thead tr').append('<td class="ctd-inline"></td>')
                     $('table.trac-diff tbody tr').append('<td class="ctd-inline"></td>')
                 };
                 /* First load parent comments */
                 for(var i = 0; i < peer_parent_comments.length; i++){
                     getParentCommentsInline(peer_parent_comments[i], peer_parent_file_id);
                 };
             };
             for(var i = 0; i < peer_comments.length; i++){
                 getCommentsInline(peer_comments[i], peer_file_id);
             };
         }else{
                 if(peer_diff_style === 'inline'){
                     $('table.trac-diff .ctd-inline').remove()
                 };
             $('.comment-tr').remove();
         };
    };

   for(var i=0; i < peer_comments.length; i++) {
       add_get_comments_link('#L', peer_comments[i], peer_file_id, false);
   }

   for(var i=0; i < peer_parent_comments.length; i++) {
       add_get_comments_link('#P', peer_parent_comments[i], peer_parent_file_id, true);
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

    /* Submit button for comment */
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

    $('#inline-comments').on('change', inline_comment_cbox);
});
