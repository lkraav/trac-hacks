jQuery(document).ready(function($) {
    var col_pos = 2;

    function add_version_column(idx){
          if(idx > 0){ /* Skip header */
            var name = $('input', this).val();
            var ver = ms_ext_version[name];
            if(ver != undefined){
                $('td:nth-child(' + col_pos + ')', this).after('<td>' + ver + '</td>')
            }
            else{
                $('td:nth-child(' + col_pos + ')', this).after('<td></td>')
            };
          }
    };

    /* Add version column to list table */
    $('#millist tr th:nth-child(' + col_pos + ')').after('<th class="version">Version</th>');
    $('#millist tr').each(add_version_column);
});
