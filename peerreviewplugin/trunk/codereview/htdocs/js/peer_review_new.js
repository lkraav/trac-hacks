
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