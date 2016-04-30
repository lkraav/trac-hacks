jQuery(document).ready(function($) {

    function prepare_hiding(idx){
          if(idx > 0){ /* Skip header */
            var txt = $('td.default', this).prev().text();
            if(txt.length > 0){
              $(this).addClass('completed');
            };
          }
    };
    function toggle_version_completed(){
      if($('#smp-hide-completed').is(':checked')){
        $('tr.completed').addClass('smp-hide-completed');
      }
      else{
        $('tr.completed').removeClass('smp-hide-completed')
      };
    };

    function toggle_version_by_prj(){
      var prj = $('#smp-project-sel').val();
      if(prj != ''){
        $('#verlist tr').each(function(idx){
          if(idx > 0){
             var prj_for_ver = smp_proj_ver[$('input:first', this).val()];
             if ($.inArray(prj, prj_for_ver) != -1){
                $(this).removeClass('smp-hide-project');
             }else{
                 $(this).addClass('smp-hide-project');
             };
          };
        });
      }else{
        $('#verlist tr').each(function(idx){
               if(idx > 0){
                   $(this).removeClass('smp-hide-project');
               };
           });
      };
    };

    /* Hide completed */
    $('#verlist').before('<label id="smp-hide-label"><input type="checkbox" id="smp-hide-completed"/>Hide completed versions</label>');
    $('#smp-hide-completed').on('click', toggle_version_completed);
    $('#verlist tr').each(prepare_hiding);

    /* Hide by project */
    $('#smp-project-sel').on('change', toggle_version_by_prj);
    toggle_version_by_prj(); /* For proper reloading of page */

});
