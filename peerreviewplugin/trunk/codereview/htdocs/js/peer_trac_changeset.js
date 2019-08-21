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
                $('#create-peerreview-form').hide("fade", function(){
                   $('#peer-codereview').html(data);
                });
            },
            'html');
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


    // Add review information to the overview data
    function move_review_info(){
        var html = $('#peer-review-info').html();
        $('#overview').append(html);
        $('#peer-create-review').empty();
    };


  $('#overview').after('<div id="peer-create-review"></div>');

  var data = 'peer_repo=' + peer_repo + '&peer_rev=' + peer_rev
  $.get(peer_changeset_url, data, function(res){
      $('#peer-create-review').html(res['html'])
      if(res['action'] === 'create')
      {
          prepare_create_review();
      }
      else{
          move_review_info();
      };

      },
      'json');

});