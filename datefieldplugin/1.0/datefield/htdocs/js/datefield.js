jQuery(document).ready(function($) {
  var $fields = $('.datepick');
  $fields.datepicker({
    firstDay: datefield['first_day'],
    dateFormat: datefield['format'],
    showOn: "both",
    weekHeader: 'W',
    showWeek: datefield['show_week'],
    showButtonPanel: datefield['show_panel'],
    numberOfMonths: datefield['num_months'],
    changeMonth: datefield['change_month'],
    changeYear: datefield['change_year'],
    buttonImage: datefield['calendar'],
    buttonImageOnly: true
  });
  $fields.each(function() {
    var $field = $(this);
    if ($field.val() == "<now>") {
      $field.datepicker('setDate', '-0d');
    }
  })
});
