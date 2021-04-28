jQuery(document).ready(function($) {

    //Colorizes the tables according to Trac standards
    function colorTable(txt){
        var table = document.getElementById(txt);
        var loop = 0;
        for (; loop < table.rows.length; loop++) {
            var row = table.rows[loop];
            if (loop % 2 == 0) {
                row.className = 'odd';
            } else {
                row.className = 'even';
            }
        }
    };


    function removeuser(user_name){
        $('#user-rem-name').text(user_name);
        $('#user-rem-confirm').data('username', user_name);
        $('#user-rem-confirm').dialog('open');
        /* User is removed in click handler of dialog if necessary */
    };


    //takes a user from the table, adds them to the dropbox, and deletes from the table
    function do_removeuser(txt) {

         tline = '<option value="'+txt+'">'+txt+'</option>';

         if($('#Reviewers > #no-more-users').is(':visible')){
            $('#no-more-users').replaceWith(tline);
         }
         else{
            $('#Reviewers').append(tline);
         };

         $('#myuserbody tr[id="'+txt+'id"]').remove();
         if($("#myuserbody tr").length == 0){
             $('#myuserbody').append('<tr id="no-users"><td>No users have been added to the code review.</td></tr>');
             $("#create-review-submit").prop('disabled', true);
         };

        colorTable('myuserbody');
        select_options();
    };


    function create_remove_link(user){
       return $('<a>', {href: "",
                                 'data-user': user,
                                 text: user,
                                 on:{
                                    click: function(event){
                                               event.preventDefault ? event.preventDefault() : event.returnValue = false;
                                               removeuser($(this).data('user'));
                                               return false;}
                                    }
                                 });
    };


    function select_options()
    {
        if($("#Reviewers option").length == 0){
             $("#Reviewers").append('<option id="no-more-users">-- No more users --</option>');
             $("#adduserbutton").prop('disabled', true);
        }
        else{
           $('#no-more-users').remove();
           $("#adduserbutton").prop('disabled', false);
        };
    };


    //takes a user from the dropdown, adds them to the table, and deletes from the dropdown
    function adduser()
    {
        var user = $("#Reviewers option:selected").text();
        var td = $('<td/>').append('<input type="hidden" name="user" value="'+user+'"/>',
                                   create_remove_link(user));
        var tline = $("<tr/>",{
        id: user+"id"
        }).append(td);

        $("#Reviewers option[value='"+user+"']").remove();

        if($('#myuserbody > #no-users').is(':visible')){
            $('#no-users').replaceWith(tline);
            delete $('#no-users');
        }
        else{
            $('#myuserbody').append(tline);
        };
        select_options();
        $("#create-review-submit").prop('disabled', false);
        colorTable('myuserbody');
        return false;
    };


    // Add callbacks to the loaded 'create review' view
    function prepare_create_review(){
        $("#create-review-submit").prop('disabled', true);
        $(".foldable").enableFolding(true, false);
        $('#adduserbutton').on('click', function(event){
               event.preventDefault ? event.preventDefault() : event.returnValue = false;
               adduser($(this).data('user'));
               return false;
        });

        $("#create-review-submit").on('click', function(event){
            event.preventDefault ? event.preventDefault() : event.returnValue = false;
            $.post(peer_changeset_url, $('#create-peerreview-form').serialize(), function(data){
                $('#peer-create-review').hide("fade", function(){
                   $('#peer-create-review').after(data['html']);
                   if(data['success'] == 1){
                     for(var key in data['filedata']){
                       loadComments(key, data['filedata'][key]);
                     };
                   };
                });
            },
            'json');
            return false;
        });

      /* Confirmation dialog when removing users */
      $( "#user-rem-confirm" ).dialog({
            resizable: false,
            height: 150,
            width: 500,
            modal: true,
            autoOpen: false,
            buttons: {
              "Remove User": function() {
                $(this).dialog( "close" );
                var username = $('#user-rem-confirm').data('username');
                do_removeuser(username);
              },
              Cancel: function() {
                $(this).dialog( "close" );
              }
            }
      });
    };


    /* Submit handler for comments */
    function handle_add_comment(event){
       $.post($(this).attr('action'), $(this).serialize(), function(data){
          refreshComment(data['path'], data['fileid'], data['line'])
       });
       $("#add-comment-dlg").dialog('close');
       return false;
    }

  window.markComment = function markComment(line, file_id, comment_id, read_status, review_id){
    $.post(peer_comment_url,
           {'fileid': file_id, 'line': line, 'commentid': comment_id, 'markread': read_status,
            'reviewid': review_id,
            '__FORM_TOKEN': $('#form-token').val()
           },
            function(data){
              /* Refresh comment dialog */
              refreshComment(data['path'], data['fileid'], data['line'])
           });
    };

  window.markCommentRead = function markCommentRead(line, file_id, comment_id, review_id){
        markComment(line, file_id, comment_id, 'read', review_id);
    };

  window.markCommentNotread = function markCommentNotread(line, file_id, comment_id, review_id){
        markComment(line, file_id, comment_id, 'notread', review_id);
    };

  /* USer wants to add a comment */
  window.addComment = function addComment(line, fileid, parentid)
    {
        $("#comment-line").val(line);
        $("#comment-parentid").val(parentid);
        $("#comment-fileid").val(fileid);
        $("#comment-txt").val("");
        $("#commentchange").hide();
        $('#add-comment-dlg').dialog({title: "Add Comment for Line " + line});
        $('#add-comment-dlg').dialog('open');
        $('#add-comment-dlg').dialog('moveToTop');
    }

  /* Refresh the specified comment */
  window.refreshComment = function refreshComment(path, fileid, line){
    /* Find the file entry */
    let entry = $('li.entry h2:contains(' + path + ')');
    let diff_table = entry.siblings('table.trac-diff');

    let th = $(diff_table).find('th[data-line=' + line + ']')
    if($(th).length == 1){
        /* First comment in this line */
        let style = $('select[name="style"]').val();
        if (style === 'inline'){
          $(th).parent().after('<tr class="comment-tr" id="CTR' + line + '"><td colspan="3" id="CTD' + line + '">Loading...</td></tr>')
        }else{
          $(th).parent().after('<tr class="comment-tr" id="CTR' + line + '"><td colspan="2"></td><td colspan="2" id="CTD' + line + '">Loading...</td></tr>')
        }
        $(th).replaceWith('<th>' + line + '</th>')
    };

    $(diff_table).find('#CTD' + line + ' #comment-loading-' + line).show();
    var url = peer_comment_url + '?action=commenttree&fileid=' + fileid + '&line=' + line + '&path=' + path
    $('#CTD' + line).load(url);
  };

  /* Add a table row for each comment */
  function loadComments(path, comment_info){
    let fid_comments = comment_info
    /* Find the file entry */
    let entry = $('li.entry h2:contains(' + path + ')');
    let diff_table = entry.siblings('table.trac-diff');

    let style = $('select[name="style"]').val();
    if (style === 'inline'){
      var selector = 'tbody > tr th:nth-child(2)';
    }
    else{
      var selector = 'tbody > tr th:nth-child(3)';
    }

    diff_table.find(selector).each(function(){
      let line = parseInt($(this).text());
      let fileid = fid_comments[0];
      if(fid_comments[1].includes(line)){
        $(diff_table).find('#CTD' + line).remove();
        if (style === 'inline'){
          $(this).parent().after('<tr class="comment-tr" id="CTR' + line + '"><td colspan="3" id="CTD' + line + '">Loading...</td></tr>')
        }else{
          $(this).parent().after('<tr class="comment-tr" id="CTR' + line + '"><td colspan="2"></td><td colspan="2" id="CTD' + line + '">Loading...</td></tr>')
        }
        let url = peer_comment_url + '?action=commenttree&fileid=' + fid_comments[0] + '&line=' + line + '&path=' + path
        $('#CTD' + line).load(url);
      }
      else{
      if($.isNumeric(line) && peer_perm_dev == 1)
        $(this).replaceWith('<th data-line="' + line + '"><a href="javascript:addComment(' + line + ', ' + fileid + ', -1)">' + line + '</a></th>')
      }
    });
  };

  $('#overview').after('<div id="peer-create-review"></div><div id="peer-add-comment"></div>');

  /* Get 'Codereview' section */
  var data = 'peer_repo=' + peer_repo + '&peer_rev=' + peer_rev
  $.get(peer_changeset_url, data, function(res){
      if(res['action'] === 'create')
      {
        $('#peer-create-review').html(res['html']);
        prepare_create_review();
      }
      else{
        // Add review information to the overview data
        $('#overview').append(res['html']);
      };
    },
    'json');


  /* Add comments to diff */
  if(typeof peer_file_comments !== 'undefined'){
      /* Load add comments dialog */
      $('#peer-add-comment').load(peer_comment_url + '?action=addcommentdlg', function(){
           $("#add-comment-dlg").dialog({
              title: "Add Comment",
              width: 500,
              autoOpen: false,
              resizable: true,
              dialogClass: 'top-dialog',
           });
        /* Submit for comment */
        $('#add-comment-form').submit(handle_add_comment);
      })

    for(var key in peer_file_comments){
      loadComments(key, peer_file_comments[key]);
    };
  };

});