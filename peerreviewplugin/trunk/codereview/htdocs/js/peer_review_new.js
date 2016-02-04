
String.prototype.hashCode = function() {
    /* See */
    var hash = 0, i = 0, len = this.length, chr;
    while ( i < len ) {
            hash  = ((hash << 5) - hash + this.charCodeAt(i++)) << 0;
    }
    return hash;
};

function validateInput(form) {
    if (form.Name.value == "") {
        alert("You must specify a code review name.");
        return false;
    }

    if($('#myfilebody > #no-files').is(':visible')){
        alert("You must select at least one file.");
        return false;
    }

    if($('#myuserbody > #no-users').is(':visible')){
        alert("You must select at least one user.");
        return false;
    }

    return true;
}

//Add a file to the file structure in the database
function addFile(filepath)
{
    var tbl = document.getElementById('myfilebody');

    if ((tbl.rows.length == 1) && (tbl.rows[0].getAttribute("id") == "no-files")) {
        tbl.deleteRow(0);
    }

    var start = $('#lineBox1').val();
    var end = $('#lineBox2').val();
    var rev = $('#fileRevVal').val();

    var saveLine = filepath + "," + rev + "," + start + "," + end;
    var row_id = 'id'+saveLine.hashCode();

    if(document.getElementById(row_id) != null) {
        alert("Specified combination of filename, revision, and line numbers is already included in the file list.");
        return;
    }


    var tline = $("<tr/>",{id: row_id}).append($('<td/>').append('<input type="hidden" name="file" value="'
                                                                +saveLine
                                                                +'"/><a href="javascript:removefile(\''
                                                                +saveLine
                                                                +'\')">'
                                                                +filepath
                                                                +'</a>'),
                                                                $("<td>"+start+"</td>"),
                                                                $("<td>"+end+"</td>"),
                                                                $("<td>"+rev+"</td>"));
    $('#myfilebody').append(tline);

    colorTable('myfilebody');
}

//Remove the file from the struct

function removefile(txt) {
    // delete the row containing the txt from the table
    var filetable = document.getElementById('myfilelist');

    var loop = 0;
    for (loop = 0; loop < filetable.rows.length; loop++) {
        var row = filetable.rows[loop];
        var cell = row.cells[0];
        if (row.id == 'id'+txt.hashCode()) {
            filetable.deleteRow(loop);
            loop--;
            break;
        }
    }

    colorTable('myfilebody');

    //Remove the entry from the table in the HTML

    var tbl = document.getElementById('myfilebody');
    if (tbl.rows.length == 0){
        tbl.insertRow(0);
        tbl.rows[0].setAttribute('id', "no-files");
        var cellLeft = tbl.rows[0].insertCell(0);
        cellLeft.innerHTML = "No files have been added to the code review.";
        tbl.rows[0].appendChild(cellLeft);
        cellLeft = tbl.rows[0].insertCell(1);
        cellLeft.innerHTML ="";
        tbl.rows[0].appendChild(cellLeft);
        cellLeft = tbl.rows[0].insertCell(2);
        cellLeft.innerHTML ="";
        tbl.rows[0].appendChild(cellLeft);
        cellLeft = tbl.rows[0].insertCell(3);
        cellLeft.innerHTML ="";
        tbl.rows[0].appendChild(cellLeft);
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

//takes a user from the dropdown, adds them to the table, and deletes from the dropdown
function adduser()
{
    var user = $("#Reviewers option:selected").text();
    var tline = $("<tr/>",{
    id: user+"id"
    }).append($('<td>').append('<input type="hidden" name="user" value="'+user+'"/><a href="javascript:removeuser(\''+user+'\')">'+user+'</a>',{value: user}));

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

//takes a user from the table, adds them to the dropbox, and deletes from the table
function removeuser(txt) {
    var dropdown = document.getElementById('Reviewers');

    if (dropdown.options[0].value == '-1') {
        dropdown.options[0] = new Option(txt, '0');
        document.getElementById("adduserbutton").disabled = false;
        document.getElementById("adduserbutton").style.color = "#000000";
    } else {
        dropdown.options[dropdown.options.length] = new Option(txt, '0');
    }

    // delete the row containing the txt from the table
    var table = document.getElementById('myuserbody');

    // remove row
    var loop = 0;
    for (loop = 0; loop < table.rows.length; loop++) {

        var row = table.rows[loop];
        var cell = row.cells[0];
        if (row.id == txt + 'id') {
            table.deleteRow(loop);
            loop--;
            break;
        }
    }

    colorTable('myuserbody');

    if (table.rows.length == 0)
        checkEmpty(0, 'myuserbody');
}

jQuery(document).ready(function($) {
   var cur_repo_path = repo_browser;

    /* Called after browser is loaded */
    function create_browser_link(){
       $('#repo_browser .dir, #repo_browser .file,#repo_browser .parent,#repo_browser .pathentry').each(function(idx){
          var url = $(this).attr('href');
          $(this).on("click", function(){
              /* Reset line selection stuff */
              GLOBAL_lineStart = -1;
              GLOBAL_lineEnd = -1;
              lastPick = null;
              cur_repo_path = url;
              load_browser(url);
              return false;});
       });
       $('.fileselect').on('change', function(){
           if($('.fileselect:checked').length > 0){
                $('#addfiles').prop("disabled", false);
           }
           else{
               $('#addfiles').prop("disabled", true);
           };
       });
       $('#addfiles').on('click', function(){
            $('.fileselect:checked').each(function(idx){
                 /* $('#fileRevVal').val($(this).data('rev')); */
                 addFile($(this).val());
                 });
       });
       if($('#repo_browser').data('is-followup') == 1){
          $('#addfiles').hide();
          $('#add-file-fs').hide();
          $('.newrev').each(function(idx){
             $(this).text($('#fileRevVal').val());
          });
       }
    };

    function switch_rev(event){
      if ( event.which == 13 ) {
         load_browser(cur_repo_path+"?rev="+$('#switch_rev').val());
         event.preventDefault();
      };
    };

    function load_browser(url){
      $('#repo_browser').load(url, function(){
           create_browser_link();
           $('#repo_browser #switch_rev').on('keypress',switch_rev)
           //$("#addFileButton").on('click', addFile_)
      });
    };

    /* Initial browser load */
    load_browser(repo_browser);

});