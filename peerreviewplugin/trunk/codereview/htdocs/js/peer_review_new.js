
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

    if(peer_is_modify != 1 && peer_is_followup != 1){
        if($('#fileRevVal').length == 0){
            alert("You must choose a revision for your new files.");
            return false;
        }
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
    var reponame = $('#reponame_file').val();
    if(reponame === ''){
        display_reponame = '(default)'
    }else{
        display_reponame = reponame
    };

    var saveLine = filepath + "," + rev + "," + start + "," + end + "," + reponame;
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
                                                                $("<td>"+display_reponame+"</td>"),
                                                                $("<td>"+start+"</td>"),
                                                                $("<td>"+end+"</td>"),
                                                                $("<td>"+rev+"</td>"));
    $('#myfilebody').append(tline);

    colorTable('myfilebody');
}

//Remove the file from the struct

function removefile(fileidstring){
    $('#confirm-name').text(fileidstring.split(',')[0]);
    $('#dialog-confirm').data('filename', fileidstring);
    $('#dialog-confirm').dialog('open');
    /* File is removed in click handler of dialog if necessary */
};


function do_removefile(txt) {
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

jQuery(document).ready(function($) {
   var cur_repo_path = repo_browser;

    /* Called after browser is loaded */
    function create_browser_link(){
       $('#repo_browser .dir, #repo_browser .file,#repo_browser .parent,#repo_browser .pathentry, .link_repo_idx').each(function(idx){
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
    };

    function switch_rev(event){
      if ( event.which == 13 ) {
          if($('#switch_rev').val() != ""){
             load_browser(cur_repo_path.split('?')[0]+"?rev="+$('#switch_rev').val()+'&repo='+$('#reponame_file').val());
             event.preventDefault();
             }
          else{
             load_browser(cur_repo_path.split('?')[0]);
             event.preventDefault();
          };
      };
    };

    function changeRepo(){
        load_browser($(this).val()+'&rev='+encodeURIComponent($('#switch_rev').val()));
    };

    function load_browser(url){
      $('#repo_browser').load(url, function(){
           create_browser_link();
           $('#repo_browser #switch_rev').on('keypress',switch_rev);
           $('#sel_repo').on('change', changeRepo);
      });
    };

    /* Initial browser load only when not modifying and no followup review */
    if($('#repo_browser').data('is-modify') == 0 && peer_is_followup == 0){
       load_browser(repo_browser);
    };

    var args = {realm: "peerreview", escape_newlines: 1};
    $("#review-notes").autoPreview("preview_render", args, function(textarea, text, rendered) {
        $("#noteschange div.comment").html(rendered);
        if (rendered)
          $("#noteschange").show();
        else if ($("#noteschange ul.changes").length == 0)
          $("#noteschange").hide();
    });

    /* Confirmation when leaving page. */
    var review_not_saved = true;

    $(window).bind("beforeunload", function(e) {
      var confirmationMessage = "Review is not saved yet. Do you really want to leave the page?";
      if(review_not_saved){
          e.returnValue = confirmationMessage;
          return confirmationMessage
      };
    })
    $('#new-review').on('submit', function(event){review_not_saved = false;});

    /* Confirmation dialog when removing files */
    $( "#dialog-confirm" ).dialog({
          resizable: false,
          height: 150,
          width: 500,
          modal: true,
          autoOpen: false,
          buttons: {
            "Remove File": function() {
              $(this).dialog( "close" );
              var filepath = $('#dialog-confirm').data('filename');
              do_removefile(filepath);
            },
            Cancel: function() {
              $(this).dialog( "close" );
            }
          }
    });
});