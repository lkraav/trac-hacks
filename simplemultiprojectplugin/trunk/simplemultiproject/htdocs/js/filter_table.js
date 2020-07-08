jQuery(function($) {

  function prepare_hiding(idx) {
    if(idx > 0) { /* Skip header */
      var txt = $('td.default', this).prev().text();
      if(txt.trim().length > 0) {
        $(this).addClass('completed');
      };
    }
  };
  function toggle_completed() {
    if($('#smp-hide-completed').is(':checked')) {
      $('tr.completed').addClass('smp-hide-completed');
    }
    else {
      $('tr.completed').removeClass('smp-hide-completed')
    };
  };

  function toggle_by_prj() {
    var prj = $('#smp-project-sel').val();
    if(prj != '') {
      $(smp_tbl_selector + ' tr').each(function(idx) {
        if(idx > 0) {
          var prj_for_item = smp_proj_per_item[$('input:first', this).val()];
          if ($.inArray(prj, prj_for_item) != -1) {
            $(this).removeClass('smp-hide-project');
          } else {
            $(this).addClass('smp-hide-project');
          };
        };
      });
    } else {
      $(smp_tbl_selector + ' tr').each(function(idx) {
        if(idx > 0){
          $(this).removeClass('smp-hide-project');
        };
      });
    };
  };

  /* Hide completed */
  $('#verlist').before(
    '<label id="smp-hide-label"><input type="checkbox" id="smp-hide-completed"/>' +
    'Hide completed versions</label>');
  $('#smp-hide-completed').on('click', toggle_completed);
  $(smp_tbl_selector + ' tr').each(prepare_hiding);

  /* Hide by project */
  $('#smp-project-sel').on('change', toggle_by_prj);
  toggle_by_prj(); /* For proper reloading of page */

});
