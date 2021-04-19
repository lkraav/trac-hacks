jQuery(document).ready(function($) {
  $('#info').before('<div id="peer-status"></div>');

  /*$('#info').before('<div id="view-comment-dlg"><p id="refresh"><a id="comment-refresh" href="">Refresh</a></p><div id="comment-tree"></div><p id="comment-loading">Loading...</p><div class="buttons"><input type="hidden" name="fileid" value="-1" id="comment-fileid-view"/><input type="hidden" name="line" value="" id="comment-line-view" /><input type="hidden" name="addcomment" value="Add Comment"/></div></div>')

  $('#info').before('<div id="add-comment-dlg"><form action="peerReviewCommentCallback" method="POST" id="add-comment-form"><div><textarea rows="6" id="comment-txt" name="comment"></textarea><div id="commentchange" class="ticketdraft" style="display: none"><p class="help">Preview:</p><div class="notes-preview comment searchable"></div></div></div><div class="buttons"><input type="hidden" name="fileid" value="-1" id="comment-fileid"/><input type="hidden" name="parentid" value="-1" id="comment-parentid"/><input type="hidden" name="line" value="" id="comment-line" /><input type="hidden" name="addcomment" value="Add Comment"/><input type="submit" name="addcomment" value="Add Comment" id="addcomment"/></div></form></div>');

   $( "#view-comment-dlg_" ).dialog({
      title: "View Comments",
      width: 440,
      autoOpen: false,
      resizable: false,
   });
*/
  var data = 'peer_path=' + peer_path + '&peer_repo=' + peer_repo + '&peer_is_head=' + peer_is_head + '&peer_rev=' + peer_rev
  data += '&peer_is_dir=' + peer_is_dir
  $('#peer-status').load(peer_status_url, data, function(){


  });
});