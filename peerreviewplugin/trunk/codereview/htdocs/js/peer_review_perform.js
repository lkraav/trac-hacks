
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


function getInlineCommentMarkup(LineNum, diff_view, parent_comment){
  var markup = '<th></th>'
  if(diff_view){
      if(peer_diff_style === 'inline'){
          markup += '<th></th><td id="PTD' + LineNum + '"></td><td id="CTD' + LineNum + '"></td>'
      }
      else{
          markup += '<td id="PTD' + LineNum + '"></td><th></th><td id="CTD' + LineNum + '"></td>'
      };
  }
  else{
      markup += '<td id="CTD' + LineNum + '" class="peer-comment-td"></td>';
  };
  return $('<tr>',
           {id: "CTR" + LineNum, class: "comment-tr"}
           ).append(markup);
};


function default_for(arg, val){
    return typeof arg !== 'undefined' ? arg : val;
};


function refreshComment(path, fileid, line){
    let url = baseUrl + '?action=commenttree&fileid=' + fileid + '&line=' + line + '&path=' + path
    let selector = '#PTD' + line
    if(fileid == peer_file_id){  /* don't use '===' here it may be either int or str */
      selector = '#CTD' + line
    }

    if($(selector).length == 0){
      /* No comment for this line yet. Prepare tr */
      if(peer_parent_file_id !== 0){
        diff_view = true;
      }
      else{
        diff_view = false;
      }
      $('th#L' + line).parent().after(getInlineCommentMarkup(line, diff_view, false));
    }
    else{
      $(selector + ' .peer-loading').show();
    }
    $(selector).load(url);
};


function getComments(LineNum, fileID, refresh)
{
    refresh = default_for(refresh, false);

    /* Hide/show comments by clicking header again */
    if($('#CTD'+LineNum).children().length > 0){
        $('#CTD'+LineNum).empty();
        if(!refresh){
           if($('#PTD' + LineNum).children().length === 0){
               $('#CTR' + LineNum).remove();
           };
           return;
        };
    };

    if(peer_parent_file_id !== 0){
      diff_view = true;
    }
    else{
      diff_view = false;
    }
    if($('#CTD'+LineNum).length === 0 ){
       $('th#L'+LineNum).parent().after(getInlineCommentMarkup(LineNum, diff_view, false));
    }

    let url = baseUrl + '?action=commenttree&fileid=' + fileID + '&line=' + LineNum + '&path=' + peer_file_path
    $('#CTD' + LineNum).load(url, function(){
      /* On page load all parents are loaded, then all follow-ups. If we are the last follow-up line we
         assume all comments are loaded. This isn't entirely accurate because loading of comments is async */
      let selector = '#CTD' + peer_comments[peer_comments.length - 1] + ' .peer-comment'
      if($(selector).length !== 0 ){
        $('#peer-spinner').hide();
      }
    });
};


function getParentComments(line, fileid, refresh)
{
    refresh = default_for(refresh, false);

    /* Hide/show comments by clicking header again */
    if($('#PTD' + line).children().length > 0){
        $('#PTD' + line).empty();
        if(!refresh){
           if($('#CTD' + line).children().length === 0){
               $('#CTR' + line).remove();
           };
           return;
        };
    };
    /* Make sure comment tr exists */
    if($('#PTD' + line).length === 0 ){
        $('th#P' + line).parent().after(getInlineCommentMarkup(line, true, true));
    }

    let url = baseUrl + '?action=commenttree&fileid=' + fileid + '&line=' + line + '&path=' + peer_file_path
    $('#PTD' + line).load(url);
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
             /* Show or refresh comment dialog */
             refreshComment(peer_file_path, data['fileid'], data['line'])
           });
};

function markCommentRead(line, file_id, comment_id, review_id){
    markComment(line, file_id, comment_id, 'read', review_id);
};

function markCommentNotread(line, file_id, comment_id, review_id){
    markComment(line, file_id, comment_id, 'notread', review_id);
};

jQuery(document).ready(function($) {

    function loadComments(path, comment_list){
             if(peer_parent_file_id !== 0){
                 /* This is a diff view. */
                 if(peer_diff_style === 'inline'){
                     $('table.trac-diff thead tr').append('<td class="ctd-inline"></td>')
                     $('table.trac-diff tbody tr').append('<td class="ctd-inline"></td>')
                 };
                 /* First load parent comments */
                 for(var i = 0; i < peer_parent_comments.length; i++){
                     getParentComments(peer_parent_comments[i], peer_parent_file_id);
                 };
             };
             for(var i = 0; i < peer_comments.length; i++){
                 getComments(peer_comments[i], peer_file_id);
             };
    };


    function comment_link(LineNum, fileID, is_parent){
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
        $(prefix+line).append(comment_link(line, fileid, is_parent));
    }

    function add_comment_button(event){
       event.preventDefault ? event.preventDefault() : event.returnValue = false;

       var LineNum = $( "#comment-line" ).val();
       $.post("peerReviewCommentCallback", $("#add-comment-form").serialize(), function(data){
          /* Show or refresh comment after creation */
          refreshComment(peer_file_path, data['fileid'], data['line'])
       });

       $( "#add-comment-dlg" ).dialog('close');
       /* Add open comment link. This can't be a parent. */
       add_get_comments_link('#L', LineNum, $("#comment-fileid" ).val(), false);
    }

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
    /* Submit button for comment on add comment dialog */
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

  /* Show inline comments */
  if(typeof peer_comments !== 'undefined'){
    if($('table th#L1').length !== 0){
      loadComments(peer_file_path, peer_comments);
      if(peer_comments.length ===0){
        $('#peer-spinner').hide();
      }
    }
    else{
    /* No file is shown (identical follow-up) */
      $('#peer-spinner').hide();
    }
  };

});
