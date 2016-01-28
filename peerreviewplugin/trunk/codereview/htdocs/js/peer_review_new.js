
String.prototype.hashCode = function() {
    /* See */
    var hash = 0, i = 0, len = this.length, chr;
    while ( i < len ) {
            hash  = ((hash << 5) - hash + this.charCodeAt(i++)) << 0;
    }
    return hash;
};

//Add a file to the file structure in the database
function addFile(filepath)
{
    var tbl = document.getElementById('myfilebody');

    if ((tbl.rows.length == 1) && (tbl.rows[0].getAttribute("id") == "nofile")) {
        tbl.deleteRow(0);
    }

    var lastRow = tbl.rows.length;

    var start = $('#lineBox1').val();
    var end = $('#lineBox2').val();
    var rev = $('#fileRevVal').val();

    var saveLine = filepath + "," + rev + "," + start + "," + end;
    var row_id = 'id'+saveLine.hashCode();

    if(document.getElementById(row_id) != null) {
        alert("Specified combination of filename, revision, and line numbers is already included in the file list.");
        return;
    }

    var row = tbl.insertRow(lastRow);

    var files = document.getElementById('FilesSelected');
    files.setAttribute('value', files.value + saveLine + "#");

    //Create the entry in the actual table in the page

    row.id = row_id;
    var cellLeft = row.insertCell(0);
    cellLeft.innerHTML = "<" + "a href=\"javascript:removefile('" + saveLine + "')\">" + filepath + "</a>";
    cellLeft.setAttribute('value', saveLine);
    row.appendChild(cellLeft);
    cellLeft = row.insertCell(1);
    cellLeft.innerHTML = start;
    row.appendChild(cellLeft);
    cellLeft = row.insertCell(2);
    cellLeft.innerHTML = end;
    row.appendChild(cellLeft);
    cellLeft = row.insertCell(3);
    cellLeft.innerHTML = rev;
    row.appendChild(cellLeft);

    colorTable('myfilebody');
}

//Remove the file from the struct

function removefile(txt) {
    //remove the file from the post value
    var files = document.getElementById('FilesSelected');
    var tokens = files.value.split("#");
    var newfiles = "";
    for (var i=0; i < tokens.length-1; i++) {
        if (tokens[i] == txt){
            continue;
            };
        newfiles += tokens[i] + "#";
    }

    files.setAttribute('value', newfiles);

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
        tbl.rows[0].setAttribute('id', "nofile");
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