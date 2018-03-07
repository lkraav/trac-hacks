jQuery(document).ready(function($) {

    function prepare_hiding(idx){
          if(idx > 0){ /* Skip header */
            var txt = $('td.default', this).prev().text();
            if(txt.length > 0){
              $(this).addClass('completed');
            };
          }
    };
    function toggle_milestone_completed(){
      if($('#smp-hide-completed').is(':checked')){
        $('tr.completed').addClass('smp-hide-completed');
      }
      else{
        $('tr.completed').removeClass('smp-hide-completed')
      };
    };

    function toggle_milestone_by_prj(){
      var prj = $('#smp-project-sel').val();
      if(prj != ''){
        $('#millist tr').each(function(idx){
          if(idx > 0){
             var prj_for_ms = smp_proj_ms[$('input:first', this).val()];
             if ($.inArray(prj, prj_for_ms) != -1){
                $(this).removeClass('smp-hide-project');
             }else{
                 $(this).addClass('smp-hide-project');
             };
          };
        });
      }else{
        $('#millist tr').each(function(idx){
               if(idx > 0){
                   $(this).removeClass('smp-hide-project');
               };
           });
      };
    };

    /* Hide completed */
    $('#millist').before('<label id="smp-hide-label"><input type="checkbox" id="smp-hide-completed"/>Hide completed milestones</label>');
    $('#smp-hide-completed').on('click', toggle_milestone_completed);
    $('#millist tr').each(prepare_hiding);

    /* Hide by project */
    $('#smp-project-sel').on('change', toggle_milestone_by_prj);
    toggle_milestone_by_prj(); /* For proper reloading of page */

});
