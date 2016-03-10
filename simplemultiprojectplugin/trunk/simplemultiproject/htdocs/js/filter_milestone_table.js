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
            /* */
            txt = $('td.project', this).text();
            if(txt.length > 0){
              //$(this).data('project', txt);
              $(this).attr('data-project', txt);
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

    function hide_milestone_by_prj(){
      var prj = $('#smp-projects-sel').val();
      if(prj != ''){
        $('[data-project='+prj+']').hide();
      };
    };

    /* Add version dropdown */
    $('#millist').before('<label><input type="checkbox" id="smp-hide-completed"/>Hide completed milestones</label>');
    $('#smp-hide-completed').on('click', hide_milestone);
    $('#millist tr').each(prepare_hiding);

    $('#hide-ms-by-prj').on('click', hide_milestone_by_prj);

});
