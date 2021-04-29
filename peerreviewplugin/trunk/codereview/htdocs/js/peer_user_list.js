
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
    }

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

    function removeuser(user_name, label){
        $('#user-rem-name').text(label);
        $('#user-rem-confirm').data('username', user_name);
        $('#user-rem-confirm').data('label', label);
        $('#user-rem-confirm').dialog('open');
        /* User is removed in click handler of dialog if necessary */
    };

    //takes a user from the table, adds them to the dropbox, and deletes from the table
    function do_removeuser(user, label) {

         tline = '<option value="'+user+'">'+label+'</option>';

         if($('#Reviewers > #no-more-users').is(':visible')){
            $('#no-more-users').replaceWith(tline);
         }
         else{
            $('#Reviewers').append(tline);
         };

         $('#myuserbody tr[id="'+user+'id"]').remove();
         if($("#myuserbody tr").length == 0){
             $('#myuserbody').append('<tr id="no-users"><td>No users have been added to the code review.</td></tr>');
         };

        colorTable('myuserbody');
        select_options();
    }

    function create_remove_link(user, label){
       return $('<a>', {href: "",
                                 'data-user': user,
                                 text: label,
                                 on:{
                                    click: function(event){
                                               event.preventDefault ? event.preventDefault() : event.returnValue = false;
                                               removeuser($(this).data('user'), $(this).text());
                                               return false;}
                                    }
                                 });
    };

    //takes a user from the dropdown, adds them to the table, and deletes from the dropdown
    function adduser()
    {
        var user = $("#Reviewers option:selected").val();
        var label = $("#Reviewers option:selected").text();
        var td = $('<td/>').append('<input type="hidden" name="user" value="'+user+'"/>',
                                   create_remove_link(user, label));
        var tline = $("<tr/>",{
        id: user+"id"
        }).append(td);

        $("#Reviewers option[value='"+user+"']").remove();

        if($('#myuserbody > #no-users').is(':visible')){
            $('#no-users').replaceWith(tline);
            delete $('#no-users');
            select_options();
        }
        else{
            $('#myuserbody').append(tline);
            select_options();
        };

        colorTable('myuserbody');
        return false;
    }

    $('.remove-user').each(function(idx){
       var user = $(this).data('user');

       $(this).click( function(event){
           event.preventDefault ? event.preventDefault() : event.returnValue = false;
           removeuser($(this).data('user'), $(this).text());
           return false;
       });
    });
    $('#adduserbutton').on('click', function(event){
           event.preventDefault ? event.preventDefault() : event.returnValue = false;
           adduser();
           return false;
    });

    /* Confirmation dialog when removing users */
    $( "#user-rem-confirm" ).dialog({
          resizable: false,
          height: 175,
          width: 500,
          modal: true,
          autoOpen: false,
          buttons: [
            {
              text: "Remove User",
              click: function() {
                                 $(this).dialog( "close" );
                                 var username = $('#user-rem-confirm').data('username');
                                 do_removeuser(username, $('#user-rem-confirm').data('label'));
                                }
            },
            {
              text: "Cancel",
              id: "peer-cancel",
              click: function() {
                                 $(this).dialog( "close" );
                                }
            }
          ],
          open: function(event, ui){
            $(this).parent().find('#peer-cancel').focus();
          }
    });
});
