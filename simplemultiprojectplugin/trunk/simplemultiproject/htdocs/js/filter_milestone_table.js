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
    function prepare_hiding(idx){
          if(idx > 0){ /* Skip header */
            var txt = $('td.default', this).prev().text();
            if(txt.length > 0){
              $(this).addClass('completed');
            };
          }
    };
    function hide_milestone(){
      if($('#smp-hide-completed').is(':checked')){
        $('tr.completed').hide();
      }
      else{
        $('tr.completed').show();
      };
    };

    /* Add version dropdown */
    $('#millist').before('<label><input type="checkbox" id="smp-hide-completed"/>Hide completed milestones</label>');
    $('#smp-hide-completed').on('click', hide_milestone);
    $('#millist tr').each(prepare_hiding);
});
