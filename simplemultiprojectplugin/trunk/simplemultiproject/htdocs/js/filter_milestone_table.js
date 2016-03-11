jQuery(document).ready(function($) {

    function prepare_hiding(idx){
          if(idx > 0){ /* Skip header */
            var txt = $('td.default', this).prev().text();
            if(txt.length > 0){
              $(this).addClass('completed');
            };
            txt = $('td.project', this).text();
            if(txt.length > 0){
              $(this).data('project', txt);
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
          if($(this).data('project') === prj){
            $(this).removeClass('smp-hide-project');
          }else{
              if(idx > 0){
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
