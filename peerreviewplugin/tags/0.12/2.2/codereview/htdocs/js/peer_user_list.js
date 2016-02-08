
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

    //takes a user from the table, adds them to the dropbox, and deletes from the table
    function removeuser(txt) {

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
         };

        colorTable('myuserbody');
    }

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
           removeuser($(this).data('user'));
           return false;
       });
    });
    $('#adduserbutton').on('click', function(event){
           event.preventDefault ? event.preventDefault() : event.returnValue = false;
           adduser($(this).data('user'));
           return false;
    });
});