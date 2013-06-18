/**
 * beta
 * adds javascript jQuery UI date picker to ticket fields
 */

$(document).ready(function () {
  
    if (!jQuery.ui) {
      $.ajax({
	url: ppGetBaseUrl()+"/chrome/projectplan/js/jquery-ui.min.js", // loading from CDN does not work if https is used on Trac
	dataType: "script",
	cache: true,
	success: function(){ initPPticketDatePicker(); },
	error: function(err, status, thrown) { console.log("unable to load jquery-ui.js: status " + status); console.log(err); }
      });
    } else {
      console.log("initPPticketDatePicker: jquery ui was already loaded.")
      initPPticketDatePicker();
    }
});

function initPPticketDatePicker(){
    $.datepicker.setDefaults({
      showOn: "both",
      calculateWeekType: true,
      showWeek: true,
      showAnim: "fadeIn",
      gotoCurrent: true,
      firstDay: 1,
      showButtonPanel: true,
      currentText: "current"
    }); 
    console.log("initPPticketDatePicker: init: "+($("#custom_due_assign_field_id").html())+", "+($("#custom_due_close_field_id").html()) );
    // $("#field-"+$("#custom_due_assign_field_id").html()).datepicker('destroy'); // safety, kills to late
    $("#field-"+$("#custom_due_assign_field_id").html()).datepicker( { dateFormat: $("#custom_due_assign_field_format").html().toLowerCase().replace("yyyy","yy") } );
    // $("#field-"+$("#custom_due_close_field_id").html()).datepicker('destroy'); // safety, kills to late
    $("#field-"+$("#custom_due_close_field_id").html()).datepicker( { dateFormat: $("#custom_due_close_field_format").html().toLowerCase().replace("yyyy","yy") } );
    $(".ui-datepicker-trigger").hide();
}




